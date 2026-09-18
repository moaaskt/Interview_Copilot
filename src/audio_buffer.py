import logging
import math
import threading
from collections import deque
from enum import Enum, auto
from typing import List, Optional

logger = logging.getLogger(__name__)


class AudioCaptureState(Enum):
    """Estados explícitos da máquina de estados de captura de áudio."""
    PRE_ROLL = auto()
    RECORDING = auto()


class PreRollAudioBuffer:
    """
    Buffer circular de áudio contínuo thread-safe para retenção dos últimos segundos
    de fala antes do início ativo da gravação.

    A capacidade é calculada dinamicamente a partir da duração em segundos e dos parâmetros
    reais de amostragem e frames do áudio, com tolerância máxima de 1 chunk decorrente
    da granularidade dos blocos de captura.
    """

    def __init__(
        self,
        duration_seconds: float = 5.0,
        sample_rate: int = 16000,
        chunk_frames: int = 1600,
        channels: int = 1,
        sample_width: int = 2,
    ) -> None:
        self.sample_rate = sample_rate
        self.chunk_frames = chunk_frames
        self.channels = channels
        self.sample_width = sample_width
        self._lock = threading.Lock()

        # Duração de cada chunk em segundos: chunk_frames / sample_rate
        self.chunk_duration = chunk_frames / sample_rate if sample_rate > 0 else 0.1
        self.bytes_per_chunk = chunk_frames * channels * sample_width

        self.set_duration(duration_seconds)

    def set_duration(self, duration_seconds: float) -> None:
        """Atualiza a duração configurada do buffer mantendo thread-safety."""
        with self._lock:
            self.duration_seconds = max(0.0, float(duration_seconds))
            self.enabled = self.duration_seconds > 0.0

            if self.enabled and self.chunk_duration > 0:
                self.max_chunks = math.ceil(self.duration_seconds / self.chunk_duration)
                self._buffer: deque[bytes] = deque(maxlen=self.max_chunks)
            else:
                self.max_chunks = 0
                self._buffer = deque()

            logger.debug(
                f"[PreRollAudioBuffer] Configurado: {self.duration_seconds:.1f}s "
                f"(max_chunks={self.max_chunks}, chunk_dur={self.chunk_duration:.2f}s, enabled={self.enabled})"
            )

    def push(self, chunk: bytes) -> None:
        """
        Adiciona um novo chunk de áudio PCM ao buffer circular.
        Se desativado (pre_roll_seconds == 0.0), opera em bypass sem alocar memória.
        """
        if not self.enabled or not chunk:
            return

        with self._lock:
            self._buffer.append(chunk)

    def drain_all(self) -> List[bytes]:
        """
        Operação atômica que extrai todos os chunks acumulados na ordem cronológica
        estrita [t-N, ..., t-1] e redefine o buffer interno para vazio ([]).
        """
        if not self.enabled:
            return []

        with self._lock:
            if not self._buffer:
                return []
            chunks = list(self._buffer)
            self._buffer.clear()
            return chunks

    def get_all(self) -> List[bytes]:
        """Retorna uma cópia snapshot dos chunks sem esvaziar o buffer (para inspeção e testes)."""
        if not self.enabled:
            return []

        with self._lock:
            return list(self._buffer)

    def clear(self) -> None:
        """Limpa o buffer interno."""
        with self._lock:
            self._buffer.clear()

    @property
    def current_chunks_count(self) -> int:
        """Quantidade atual de chunks armazenados."""
        with self._lock:
            return len(self._buffer)

    @property
    def current_bytes_count(self) -> int:
        """Total de bytes brutos armazenados no buffer."""
        with self._lock:
            return sum(len(c) for c in self._buffer)

    @property
    def current_duration_seconds(self) -> float:
        """Duração aproximada em segundos do áudio atualmente retido no buffer."""
        with self._lock:
            return len(self._buffer) * self.chunk_duration
