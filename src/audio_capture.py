import asyncio
import logging
import os
import subprocess
import sys
from typing import Callable, List, Optional

import numpy as np

try:
    from audio_buffer import AudioCaptureState, PreRollAudioBuffer
except ImportError:
    from src.audio_buffer import AudioCaptureState, PreRollAudioBuffer

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
    Envia chunks de áudio PCM para uma callback assíncrona e gerencia o buffer circular de pré-roll.
    """

    def __init__(
        self,
        audio_callback: Callable[[bytes], None],
        sample_rate: int = 16000,
        chunk_duration: float = 0.1,
        device_index: Optional[int | str] = None,
        device_name: Optional[str] = None,
        pre_roll_seconds: float = 5.0,
    ) -> None:
        self.audio_callback = audio_callback
        self.sample_rate = sample_rate
        self.chunk_size = int(sample_rate * chunk_duration)
        self.device_index = device_index
        self.device_name = device_name
        self.is_running = False
        self._current_loop: Optional[asyncio.AbstractEventLoop] = None

        self.state = AudioCaptureState.PRE_ROLL
        self.pre_roll_buffer = PreRollAudioBuffer(
            duration_seconds=pre_roll_seconds,
            sample_rate=self.sample_rate,
            chunk_frames=self.chunk_size,
            channels=1,
            sample_width=2,
        )

        # Recursos Windows
        self._pa: Optional[any] = None
        self._win_stream = None
        self._keepalive_stream = None

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

    def _find_windows_loopback(self, pa) -> dict:
        """Localiza com resiliência o dispositivo loopback WASAPI correspondente (por nome, índice ou default)."""
        loopbacks = list(pa.get_loopback_device_info_generator())
        if not loopbacks:
            logger.warning("[Windows] Nenhum dispositivo loopback WASAPI encontrado.")
            return self._get_windows_loopback_device(pa)

        # 1. Se foi passado device_name específico, tenta encontrar por nome entre os loopbacks
        if self.device_name and self.device_name != "Padrão do Sistema":
            clean_target = self.device_name.replace("[Loopback]", "").strip().lower()
            for lb in loopbacks:
                clean_lb = lb["name"].replace("[Loopback]", "").strip().lower()
                if clean_target in clean_lb or clean_lb in clean_target:
                    logger.info(f"[Windows] Dispositivo loopback resolvido por nome '{self.device_name}': [{lb['index']}] {lb['name']}")
                    return lb

        # 2. Se foi passado device_index, verifica se corresponde a um loopback válido
        if self.device_index is not None:
            try:
                idx_int = int(self.device_index)
                for lb in loopbacks:
                    if lb["index"] == idx_int:
                        logger.info(f"[Windows] Dispositivo loopback resolvido por índice [{idx_int}]: {lb['name']}")
                        return lb
            except Exception:
                pass

        # 3. Fallback: usa o loopback padrão da saída ativa do Windows
        logger.info("[Windows] Usando dispositivo loopback padrão do Windows.")
        return self._get_windows_loopback_device(pa)

    def _find_windows_render_device(self, pa, loopback_info: dict) -> Optional[dict]:
        """Localiza o dispositivo de reprodução (alto-falantes/fones) correspondente ao loopback na mesma hostApi (WASAPI)."""
        clean_name = loopback_info.get("name", "").replace("[Loopback]", "").strip().lower()
        target_api = loopback_info.get("hostApi")

        # 1. Procura dispositivo de saída com nome correspondente na mesma hostApi (WASAPI)
        for i in range(pa.get_device_count()):
            dev = pa.get_device_info_by_index(i)
            if dev.get("hostApi") == target_api and dev.get("maxOutputChannels", 0) > 0 and not dev.get("isLoopbackDevice", False):
                dev_clean = dev.get("name", "").strip().lower()
                if clean_name and (clean_name in dev_clean or dev_clean in clean_name):
                    logger.info(f"[Windows Keep-Alive] Dispositivo de saída WASAPI correspondente encontrado: [{dev['index']}] {dev['name']}")
                    return dev

        # 2. Se não achou por nome na mesma API, tenta qualquer saída na mesma hostApi
        for i in range(pa.get_device_count()):
            dev = pa.get_device_info_by_index(i)
            if dev.get("hostApi") == target_api and dev.get("maxOutputChannels", 0) > 0 and not dev.get("isLoopbackDevice", False):
                logger.info(f"[Windows Keep-Alive] Usando dispositivo de saída WASAPI alternativo: [{dev['index']}] {dev['name']}")
                return dev

        # 3. Fallback para o dispositivo padrão de saída do WASAPI
        try:
            wasapi_info = pa.get_host_api_info_by_type(pyaudio.paWASAPI)
            default_out = pa.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
            logger.info(f"[Windows Keep-Alive] Usando dispositivo de saída padrão: [{default_out['index']}] {default_out['name']}")
            return default_out
        except Exception as e:
            logger.warning(f"[Windows Keep-Alive] Não foi possível encontrar dispositivo de saída padrão: {e}")
            return None

    def _start_windows(self, loop: asyncio.AbstractEventLoop) -> None:
        """Inicia a captura de áudio no Windows usando WASAPI loopback com keep-alive contínuo."""
        self._pa = pyaudio.PyAudio()
        try:
            device_info = self._find_windows_loopback(self._pa)
            logger.info(f"[Windows] Iniciando captura loopback no dispositivo: [{device_info['index']}] {device_info['name']}")

            # Inicia stream keep-alive silencioso no dispositivo de saída correspondente
            # Isso força o driver de áudio (ex: headsets wireless USB) e o motor WASAPI a manterem
            # buffers ativos mesmo quando nada está tocando no sistema, eliminando a perda de pacotes em silêncio.
            try:
                render_device = self._find_windows_render_device(self._pa, device_info)
                if render_device:
                    out_channels = int(render_device.get("maxOutputChannels", 2)) or 2
                    out_rate = int(render_device.get("defaultSampleRate", 48000)) or 48000
                    def silent_callback(in_data, frame_count, time_info, status):
                        return (b"\x00" * (frame_count * 2 * out_channels), pyaudio.paContinue)

                    self._keepalive_stream = self._pa.open(
                        format=pyaudio.paInt16,
                        channels=out_channels,
                        rate=out_rate,
                        output=True,
                        output_device_index=render_device["index"],
                        stream_callback=silent_callback,
                    )
                    self._keepalive_stream.start_stream()
                    logger.info(f"[Windows Keep-Alive] Stream silencioso ativo em [{render_device['index']}] {render_device['name']} para manter WASAPI acordado.")
            except Exception as e:
                logger.warning(f"[Windows Keep-Alive] Não foi possível iniciar stream silencioso keep-alive: {e}")

            # WASAPI loopback exige canais e taxa de amostragem nativos do dispositivo
            native_channels = int(device_info.get("maxInputChannels", 2)) or 1
            native_rate = int(device_info.get("defaultSampleRate", 48000)) or self.sample_rate
            target_rate = self.sample_rate

            frames_per_buffer = int(native_rate * (self.chunk_size / self.sample_rate))

            def pcm_callback(in_data, frame_count, time_info, status):
                if self.is_running and in_data:
                    try:
                        samples = np.frombuffer(in_data, dtype=np.int16)
                        # Se multi-canal (estéreo/5.1), faz downmix para mono
                        if native_channels > 1 and len(samples) >= native_channels:
                            samples = samples.reshape(-1, native_channels).mean(axis=1).astype(np.int16)

                        # Se taxa de amostragem nativa for diferente de 16kHz, reamostra com interpolação linear rápida
                        if native_rate != target_rate and len(samples) > 0:
                            num_target = int(len(samples) * target_rate / native_rate)
                            if num_target > 0:
                                indices = np.linspace(0, len(samples) - 1, num_target)
                                samples = np.interp(indices, np.arange(len(samples)), samples).astype(np.int16)

                        out_bytes = samples.tobytes()
                    except Exception as e:
                        logger.debug(f"[Windows Audio] Erro na conversão de áudio: {e}")
                        out_bytes = in_data

                    is_recording_chunk = (self.state == AudioCaptureState.RECORDING)
                    if not is_recording_chunk:
                        self.pre_roll_buffer.push(out_bytes)

                    loop.call_soon_threadsafe(self.audio_callback, out_bytes, is_recording_chunk)
                return (None, pyaudio.paContinue)

            self._win_stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=native_channels,
                rate=native_rate,
                input=True,
                input_device_index=device_info["index"],
                frames_per_buffer=frames_per_buffer,
                stream_callback=pcm_callback,
            )
            self._win_stream.start_stream()
            logger.info(f"[Windows] Captura WASAPI iniciada com sucesso ({native_rate}Hz, {native_channels} canais -> reamostrado para {target_rate}Hz mono)")
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
                    is_recording_chunk = (self.state == AudioCaptureState.RECORDING)
                    if not is_recording_chunk:
                        self.pre_roll_buffer.push(data_bytes)
                    loop.call_soon_threadsafe(self.audio_callback, data_bytes, is_recording_chunk)

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
    def set_pre_roll_duration(self, seconds: float) -> None:
        """Atualiza a duração da retenção do buffer circular de pré-áudio."""
        self.pre_roll_buffer.set_duration(seconds)

    def start_recording(self) -> List[bytes]:
        """
        Transiciona o estado de captura de PRE_ROLL para RECORDING e extrai
        atomicamente todos os chunks de áudio pré-gravados retidos no buffer.
        """
        self.state = AudioCaptureState.RECORDING
        return self.pre_roll_buffer.drain_all()

    def stop_recording(self) -> None:
        """Transiciona o estado de captura de RECORDING de volta para PRE_ROLL e purga o buffer."""
        self.state = AudioCaptureState.PRE_ROLL
        self.pre_roll_buffer.clear()

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        """Inicia a captura de áudio dependendo da plataforma."""
        self._current_loop = loop
        self.is_running = True
        if IS_WINDOWS:
            self._start_windows(loop)
        else:
            self._start_linux(loop)

    def set_device(
        self,
        device_index: Optional[int | str],
        loop: Optional[asyncio.AbstractEventLoop] = None,
        device_name: Optional[str] = None,
    ) -> None:
        """Altera o dispositivo de captura ativo e reinicia o stream."""
        self.device_index = device_index
        if device_name is not None:
            self.device_name = device_name
        target_loop = loop or self._current_loop
        logger.info(f"Alterando dispositivo de áudio para [{device_index}] {self.device_name}...")
        if self.is_running:
            self.stop()
        if target_loop:
            self.start(target_loop)

    def stop(self) -> None:
        """Para e encerra os recursos de áudio."""
        self.is_running = False

        # Encerramento Windows
        if self._keepalive_stream:
            try:
                self._keepalive_stream.stop_stream()
                self._keepalive_stream.close()
            except Exception as e:
                logger.error(f"Erro ao fechar stream keep-alive Windows: {e}")
            finally:
                self._keepalive_stream = None

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
