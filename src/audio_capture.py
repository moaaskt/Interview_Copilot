import asyncio
import logging
import os
import subprocess
import sys
from typing import Callable, Optional

logger = logging.getLogger(__name__)

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    try:
        import pyaudiowpatch as pyaudio
    except ImportError:
        import pyaudio
else:
    try:
        import sounddevice as sd
    except ImportError:
        sd = None


class AudioCapture:
    """
    Captura de áudio do sistema multiplataforma (Windows WASAPI loopback e Linux PipeWire/PulseAudio).
    Envia chunks de áudio PCM para uma callback assíncrona.
    """

    def __init__(
        self,
        audio_callback: Callable[[bytes], None],
        sample_rate: int = 16000,
        chunk_duration: float = 0.1,
        device_index: Optional[int | str] = None,
    ) -> None:
        self.audio_callback = audio_callback
        self.sample_rate = sample_rate
        self.chunk_size = int(sample_rate * chunk_duration)
        self.device_index = device_index
        self.is_running = False
        self._current_loop: Optional[asyncio.AbstractEventLoop] = None

        # Recursos Windows
        self._pa: Optional[any] = None
        self._win_stream = None

        # Recursos Linux
        self._linux_stream = None

    @staticmethod
    def list_available_devices() -> list[dict]:
        """Enumera dispositivos de áudio disponíveis para captura na plataforma atual."""
        devices = []
        if IS_WINDOWS:
            try:
                pa = pyaudio.PyAudio()
                try:
                    for d in pa.get_loopback_device_info_generator():
                        devices.append({
                            "index": d["index"],
                            "name": d["name"],
                            "type": "loopback"
                        })
                except Exception as e:
                    logger.warning(f"Erro ao listar loopbacks WASAPI: {e}")

                # Se não encontrou loopbacks, adiciona dispositivos de entrada regulares
                if not devices:
                    for idx in range(pa.get_device_count()):
                        info = pa.get_device_info_by_index(idx)
                        if info.get("maxInputChannels", 0) > 0:
                            devices.append({
                                "index": info["index"],
                                "name": info["name"],
                                "type": "input"
                            })
                pa.terminate()
            except Exception as e:
                logger.error(f"Erro ao enumerar dispositivos no Windows: {e}")
        else:
            if sd is not None:
                try:
                    sd_devs = sd.query_devices()
                    for idx, dev in enumerate(sd_devs):
                        if dev.get("max_input_channels", 0) > 0:
                            devices.append({
                                "index": idx,
                                "name": dev["name"],
                                "type": "input"
                            })
                except Exception as e:
                    logger.error(f"Erro ao enumerar dispositivos via sounddevice: {e}")
        return devices

    # ==========================================
    # LÓGICA WINDOWS (PyAudioWPatch / WASAPI)
    # ==========================================
    def _get_windows_loopback_device(self, pa):
        """Busca o dispositivo de áudio loopback (WASAPI) padrão do Windows."""
        try:
            wasapi_info = pa.get_host_api_info_by_type(pyaudio.paWASAPI)
        except Exception:
            logger.warning("WASAPI não encontrado no host API. Tentando dispositivo padrão.")
            return pa.get_default_input_device_info()

        default_speakers = pa.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        if not default_speakers.get("isLoopbackDevice"):
            for loopback in pa.get_loopback_device_info_generator():
                if default_speakers["name"] in loopback["name"]:
                    return loopback
            for loopback in pa.get_loopback_device_info_generator():
                return loopback

        return default_speakers

    def _start_windows(self, loop: asyncio.AbstractEventLoop) -> None:
        """Inicia a captura de áudio no Windows usando WASAPI loopback."""
        self._pa = pyaudio.PyAudio()
        try:
            if self.device_index is not None:
                try:
                    device_info = self._pa.get_device_info_by_index(int(self.device_index))
                    logger.info(f"[Windows] Usando dispositivo especificado [{self.device_index}]: {device_info['name']}")
                except Exception as e:
                    logger.warning(f"[Windows] Dispositivo {self.device_index} inválido ({e}). Usando padrão.")
                    device_info = self._get_windows_loopback_device(self._pa)
            else:
                device_info = self._get_windows_loopback_device(self._pa)
                logger.info(f"[Windows] Iniciando captura loopback no dispositivo: {device_info['name']}")

            channels = 1
            rate = self.sample_rate

            def pcm_callback(in_data, frame_count, time_info, status):
                if self.is_running and in_data:
                    loop.call_soon_threadsafe(self.audio_callback, in_data)
                return (None, pyaudio.paContinue)

            self._win_stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=device_info["index"],
                frames_per_buffer=self.chunk_size,
                stream_callback=pcm_callback,
            )
            self._win_stream.start_stream()
        except Exception as e:
            logger.error(f"[Windows] Erro ao inicializar captura WASAPI: {e}")
            self.stop()

    # ==========================================
    # LÓGICA LINUX (sounddevice / PipeWire / PulseAudio)
    # ==========================================
    def _configure_linux_pulse_source(self) -> None:
        """
        Configura a variável de ambiente PULSE_SOURCE caso ainda não esteja definida:
        1. Se PULSE_SOURCE já existir no ambiente (ou .env), usa imediatamente sem chamar pactl.
        2. Caso contrário, executa 'pactl list short sinks' e procura o primeiro sink cujo estado seja 'RUNNING'.
        3. Se nenhum sink estiver 'RUNNING', faz fallback para 'pactl get-default-sink'.
        4. Define os.environ['PULSE_SOURCE'] = f"{sink_name}.monitor".
        """
        existing_source = os.environ.get("PULSE_SOURCE")
        if existing_source:
            logger.info(f"[Linux] Usando PULSE_SOURCE definido pelo usuário: {existing_source}")
            return

        chosen_sink = None
        reason = ""

        # 1. Busca primeiro sink no estado RUNNING
        try:
            sinks_output = subprocess.check_output(
                ["pactl", "list", "short", "sinks"],
                stderr=subprocess.DEVNULL,
                text=True
            ).strip()

            for line in sinks_output.splitlines():
                parts = line.split()
                # Formato: ID NOME FORMATO CANAIS FREQUENCIA ESTADO
                if len(parts) >= 6:
                    sink_name = parts[1]
                    sink_state = parts[-1].upper()
                    if sink_state == "RUNNING":
                        chosen_sink = sink_name
                        reason = f"Detectado sink ativo: {sink_name} (estado: RUNNING)"
                        break
        except Exception as e:
            logger.debug(f"[Linux] Falha ao listar sinks via pactl: {e}")

        # 2. Se nenhum estiver RUNNING, usa o sink padrão como fallback
        if not chosen_sink:
            try:
                default_sink = subprocess.check_output(
                    ["pactl", "get-default-sink"],
                    stderr=subprocess.DEVNULL,
                    text=True
                ).strip()
                if default_sink:
                    chosen_sink = default_sink
                    reason = f"Nenhum sink RUNNING encontrado. Fallback para sink padrão: {default_sink}"
            except Exception as e:
                logger.debug(f"[Linux] Falha ao obter default sink via pactl: {e}")

        if chosen_sink:
            monitor_source = f"{chosen_sink}.monitor"
            os.environ["PULSE_SOURCE"] = monitor_source
            logger.info(f"[Linux] {reason} -> Definido PULSE_SOURCE={monitor_source}")
        else:
            logger.warning("[Linux] Não foi possível determinar automaticamente o sink via pactl.")

    def _get_linux_device_index(self) -> Optional[int]:
        """
        Garante a configuração adequada do PULSE_SOURCE e seleciona o dispositivo
        de entrada correto do sounddevice (pulse / pipewire / default).
        """
        if self.device_index is not None:
            try:
                idx = int(self.device_index)
                logger.info(f"[Linux] Usando dispositivo de entrada selecionado: [{idx}]")
                return idx
            except Exception as e:
                logger.warning(f"[Linux] Falha ao usar índice {self.device_index}: {e}")

        # 1. Configura PULSE_SOURCE (respeitando se já existir ou detectando RUNNING)
        self._configure_linux_pulse_source()

        # 2. Procura o dispositivo de roteamento do PulseAudio/PipeWire no sounddevice
        devices = sd.query_devices()

        # Primeiro verifica se há um dispositivo 'pulse' ou 'pipewire'
        for preferred in ("pulse", "pipewire", "default"):
            for idx, dev in enumerate(devices):
                if preferred in dev.get("name", "").lower() and dev.get("max_input_channels", 0) > 0:
                    current_source = os.environ.get("PULSE_SOURCE", "padrão")
                    logger.info(f"[Linux] Conectando sounddevice ao dispositivo [{idx}] {dev['name']} (PULSE_SOURCE: {current_source})")
                    return idx

        # Fallback para qualquer dispositivo com monitor no nome ou dispositivo padrão
        for idx, dev in enumerate(devices):
            if dev.get("max_input_channels", 0) > 0 and "monitor" in dev.get("name", "").lower():
                logger.info(f"[Linux] Dispositivo monitor encontrado na lista: [{idx}] {dev['name']}")
                return idx

        logger.warning("[Linux] Dispositivo específico de roteamento não encontrado. Usando dispositivo de entrada padrão.")
        return None

    def _start_linux(self, loop: asyncio.AbstractEventLoop) -> None:
        """Inicia a captura de áudio no Linux via sounddevice."""
        if sd is None:
            logger.error("[Linux] A biblioteca 'sounddevice' não está instalada.")
            self.stop()
            return

        try:
            device_index = self._get_linux_device_index()
            device_desc = sd.query_devices(device_index)["name"] if device_index is not None else "padrão"
            logger.info(f"[Linux] Abrindo stream sounddevice no dispositivo: {device_desc}")

            def sd_callback(indata, frames, time_info, status):
                if status:
                    logger.debug(f"[Linux sounddevice status]: {status}")
                if self.is_running and indata is not None:
                    # Converte o buffer PCM int16 para bytes
                    data_bytes = bytes(indata)
                    loop.call_soon_threadsafe(self.audio_callback, data_bytes)

            self._linux_stream = sd.InputStream(
                device=device_index,
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                blocksize=self.chunk_size,
                callback=sd_callback,
            )
            self._linux_stream.start()
        except Exception as e:
            logger.error(f"[Linux] Erro ao inicializar captura via sounddevice: {e}")
            self.stop()

    # ==========================================
    # INTERFACE PÚBLICA (Compatível com main.py)
    # ==========================================
    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        """Inicia a captura de áudio dependendo da plataforma."""
        self._current_loop = loop
        self.is_running = True
        if IS_WINDOWS:
            self._start_windows(loop)
        else:
            self._start_linux(loop)

    def set_device(self, device_index: Optional[int | str], loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        """Altera o dispositivo de captura ativo e reinicia o stream se estiver rodando."""
        self.device_index = device_index
        target_loop = loop or self._current_loop
        if self.is_running:
            logger.info(f"Reiniciando captura de áudio para o dispositivo [{device_index}]...")
            self.stop()
            if target_loop:
                self.start(target_loop)

    def stop(self) -> None:
        """Para e encerra os recursos de áudio."""
        self.is_running = False

        # Encerramento Windows
        if self._win_stream:
            try:
                self._win_stream.stop_stream()
                self._win_stream.close()
            except Exception as e:
                logger.error(f"Erro ao fechar stream Windows: {e}")
            finally:
                self._win_stream = None

        if self._pa:
            try:
                self._pa.terminate()
            except Exception as e:
                logger.error(f"Erro ao encerrar PyAudio: {e}")
            finally:
                self._pa = None

        # Encerramento Linux
        if self._linux_stream:
            try:
                self._linux_stream.stop()
                self._linux_stream.close()
            except Exception as e:
                logger.error(f"Erro ao fechar stream Linux: {e}")
            finally:
                self._linux_stream = None

        logger.info("Captura de áudio finalizada.")
