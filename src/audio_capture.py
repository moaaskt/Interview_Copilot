import asyncio
import logging
from typing import Callable, Optional

import pyaudio

logger = logging.getLogger(__name__)


class AudioCapture:
    """
    Captura áudio do sistema (loopback/monitor PulseAudio/PipeWire) usando PyAudio.
    Envia chunks de áudio PCM para uma callback assíncrona.
    """

    def __init__(
        self,
        audio_callback: Callable[[bytes], None],
        sample_rate: int = 16000,
        chunk_duration: float = 0.1,
    ) -> None:
        self.audio_callback = audio_callback
        self.sample_rate = sample_rate
        self.chunk_size = int(sample_rate * chunk_duration)
        self.is_running = False
        self._pa: Optional[pyaudio.PyAudio] = None
        self._stream = None

    def _get_linux_loopback_device(self, pa: pyaudio.PyAudio):
        """
        Busca o dispositivo de áudio loopback/monitor do Linux (PulseAudio / PipeWire).
        Procura por dispositivos com maxInputChannels > 0 e 'monitor' no nome.
        Faz fallback para o dispositivo padrão de entrada caso nenhum seja encontrado.
        """
        device_count = pa.get_device_count()
        for idx in range(device_count):
            try:
                info = pa.get_device_info_by_index(idx)
                device_name = info.get("name", "")
                max_input_channels = int(info.get("maxInputChannels", 0))

                if max_input_channels > 0 and "monitor" in device_name.lower():
                    logger.info(f"Dispositivo de loopback/monitor encontrado: [{idx}] {device_name}")
                    return info
            except Exception as e:
                logger.debug(f"Erro ao inspecionar dispositivo {idx}: {e}")

        logger.warning(
            "Nenhum dispositivo de áudio com 'monitor' no nome foi encontrado. "
            "Fazendo fallback para o dispositivo de entrada padrão."
        )
        return pa.get_default_input_device_info()

    def start(self, loop: asyncio.AbstractEventLoop) -> None:
        """Inicia a captura de áudio em thread separada para não bloquear o event loop."""
        self.is_running = True
        self._pa = pyaudio.PyAudio()

        try:
            device_info = self._get_linux_loopback_device(self._pa)
            logger.info(f"Iniciando captura loopback no dispositivo: {device_info['name']}")

            # Configurado para 1 canal (mono) e sample_rate padrão (16000 Hz) para Deepgram
            channels = 1
            rate = self.sample_rate

            def pcm_callback(in_data, frame_count, time_info, status):
                if self.is_running and in_data:
                    # Thread-safe dispatch para o evento assíncrono do loop principal
                    loop.call_soon_threadsafe(self.audio_callback, in_data)
                return (None, pyaudio.paContinue)

            self._stream = self._pa.open(
                format=pyaudio.paInt16,
                channels=channels,
                rate=rate,
                input=True,
                input_device_index=device_info["index"],
                frames_per_buffer=self.chunk_size,
                stream_callback=pcm_callback,
            )
            self._stream.start_stream()
        except Exception as e:
            logger.error(f"Erro ao inicializar captura de áudio: {e}")
            self.stop()

    def stop(self) -> None:
        """Para e encerra os recursos de áudio."""
        self.is_running = False
        if self._stream:
            try:
                self._stream.stop_stream()
                self._stream.close()
            except Exception as e:
                logger.error(f"Erro ao fechar stream de áudio: {e}")
            finally:
                self._stream = None
        if self._pa:
            try:
                self._pa.terminate()
            except Exception as e:
                logger.error(f"Erro ao encerrar PyAudio: {e}")
            finally:
                self._pa = None
        logger.info("Captura de áudio finalizada.")
