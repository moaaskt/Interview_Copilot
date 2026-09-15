import asyncio
import logging
from typing import Callable, Optional
from deepgram import (
    DeepgramClient,
    DeepgramClientOptions,
    LiveTranscriptionEvents,
    LiveOptions,
)

logger = logging.getLogger(__name__)


class Transcriber:
    """
    Gerencia a transcrição em tempo real via WebSocket do Deepgram SDK.
    Envia transcrições parciais para a UI e finais para o pipeline do LLM.
    """

    def __init__(
        self,
        api_key: str,
        on_interim_transcript: Callable[[str], None],
        on_final_transcript: Callable[[str], None],
        on_connection_change: Optional[Callable[[bool], None]] = None,
        language: str = "pt-BR",
        sample_rate: int = 16000,
    ) -> None:
        self.api_key = api_key
        self.on_interim_transcript = on_interim_transcript
        self.on_final_transcript = on_final_transcript
        self.on_connection_change = on_connection_change
        self.language = language
        self.sample_rate = sample_rate

        self.client: Optional[DeepgramClient] = None
        self.connection = None
        self.is_connected = False
        self.should_run = False
        self._reconnect_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Conecta ao WebSocket da Deepgram e registra os handlers de eventos."""
        self.should_run = True
        try:
            config = DeepgramClientOptions(options={"keepalive": "true"})
            self.client = DeepgramClient(self.api_key, config)

            # Inicializa conexão WebSocket ao vivo
            self.connection = self.client.listen.live.v("1")

            def on_message(self_conn, result, **kwargs):
                sentence = result.channel.alternatives[0].transcript
                if not sentence.strip():
                    return

                if result.is_final:
                    logger.info(f"[Deepgram FINAL]: {sentence}")
                    self.on_final_transcript(sentence)
                else:
                    logger.info(f"[Deepgram INTERIM]: {sentence}")
                    self.on_interim_transcript(sentence)

            def on_error(self_conn, error, **kwargs):
                logger.error(f"[Deepgram Error]: {error}")
                self._handle_disconnect()

            def on_close(self_conn, close, **kwargs):
                logger.warning("[Deepgram Connection Closed]")
                self._handle_disconnect()

            self.connection.on(LiveTranscriptionEvents.Transcript, on_message)
            self.connection.on(LiveTranscriptionEvents.Error, on_error)
            self.connection.on(LiveTranscriptionEvents.Close, on_close)

            options = LiveOptions(
                model="nova-2",
                language=self.language,
                smart_format=True,
                interim_results=True,
                endpointing=300,
                encoding="linear16",
                channels=1,
                sample_rate=self.sample_rate,
            )

            if self.connection.start(options) is False:
                logger.error("Falha ao iniciar conexão WebSocket com a Deepgram.")
                self._handle_disconnect()
                return

            self.is_connected = True
            if self.on_connection_change:
                self.on_connection_change(True)
            logger.info("Conexão WebSocket com a Deepgram estabelecida com sucesso.")
        except Exception as e:
            logger.error(f"Erro ao conectar ao Deepgram: {e}")
            self._handle_disconnect()

    def _handle_disconnect(self) -> None:
        """Registra a desconexão e agenda tentativa de reconexão automática."""
        was_connected = self.is_connected
        self.is_connected = False
        if was_connected and self.on_connection_change:
            self.on_connection_change(False)

        if self.should_run and (self._reconnect_task is None or self._reconnect_task.done()):
            try:
                loop = asyncio.get_running_loop()
                self._reconnect_task = loop.create_task(self._reconnect_loop())
            except RuntimeError:
                pass

    async def _reconnect_loop(self) -> None:
        """Tentativa de reconexão automática com backoff exponencial."""
        backoff = 2.0
        while self.should_run and not self.is_connected:
            logger.info(f"Tentando reconectar ao Deepgram em {backoff:.1f}s...")
            await asyncio.sleep(backoff)
            if not self.should_run:
                break
            try:
                await self.start()
                if self.is_connected:
                    logger.info("Reconexão com o Deepgram estabelecida com sucesso!")
                    break
            except Exception as e:
                logger.warning(f"Tentativa de reconexão falhou: {e}")
            backoff = min(10.0, backoff * 1.5)

    def send_audio(self, pcm_data: bytes) -> None:
        """Envia pacote PCM diretamente pelo WebSocket ativo."""
        if self.connection and self.is_connected:
            try:
                self.connection.send(pcm_data)
            except Exception as e:
                logger.error(f"Erro ao enviar áudio para a Deepgram: {e}")
                self._handle_disconnect()

    async def close(self) -> None:
        """Encerra a conexão WebSocket com a Deepgram."""
        self.should_run = False
        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()
        if self.connection:
            try:
                self.connection.finish()
            except Exception as e:
                logger.error(f"Erro ao encerrar conexão Deepgram: {e}")
        self.is_connected = False
        logger.info("Deepgram Transcriber encerrado.")
