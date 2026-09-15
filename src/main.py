import os
import sys

# Adiciona o diretório src ao sys.path para garantir resolução robusta de módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
import numpy as np
from dotenv import load_dotenv

from audio_capture import AudioCapture
from transcriber import Transcriber
from llm_service import LLMService
from ui import CopilotUI

# Configuração de Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("InterviewCopilot")


class CopilotApp:
    def __init__(self) -> None:
        # Carrega o .env a partir da raiz do projeto com caminho absoluto
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        env_path = os.path.join(project_root, ".env")
        load_dotenv(dotenv_path=env_path, override=True)

        self.deepgram_key = os.getenv("DEEPGRAM_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY")

        if not self.deepgram_key or not self.groq_key:
            missing = []
            if not self.deepgram_key:
                missing.append("DEEPGRAM_API_KEY")
            if not self.groq_key:
                missing.append("GROQ_API_KEY (ou OPENAI_API_KEY)")
            logger.error(f"Configuração incompleta no arquivo .env ({env_path}). Chave(s) ausente(s): {', '.join(missing)}")
            sys.exit(1)

        self.ui = CopilotUI(
            on_toggle_recording=self.toggle_recording,
            on_respond_now=self.respond_now,
            on_clear=self.clear_session,
        )
        self.llm_service = LLMService(api_key=self.groq_key)
        self.transcriber = Transcriber(
            api_key=self.deepgram_key,
            on_interim_transcript=self.on_interim_transcript,
            on_final_transcript=self.on_final_transcript,
            on_connection_change=self.on_connection_change,
        )
        self.audio_capture = AudioCapture(audio_callback=self.on_audio_data)

        self.loop: asyncio.AbstractEventLoop | None = None
        self.current_llm_task: asyncio.Task | None = None

        # Estado da gravação e buffer de transcrição consolidada
        self.is_recording = False
        self.transcript_buffer: list[str] = []

    def toggle_recording(self) -> None:
        """Alterna entre gravar pergunta e parar para responder."""
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_and_respond()

    def _start_recording(self) -> None:
        """Inicia uma nova rodada de gravação para a pergunta."""
        self.is_recording = True
        self.transcript_buffer.clear()
        self.ui.clear_all()
        self.ui.set_recording_state(True)
        logger.info("🎙 Gravação iniciada. Aguardando a fala da pergunta...")

    def _stop_and_respond(self) -> None:
        """Para a gravação e envia o texto consolidado para a IA."""
        self.is_recording = False
        self.ui.set_recording_state(False)
        logger.info("⏹ Gravação finalizada.")
        self.respond_now()

    def respond_now(self) -> None:
        """Dispara a geração de resposta com base na transcrição acumulada ou visível na tela."""
        # Se ainda estiver gravando, encerra a captura
        if self.is_recording:
            self.is_recording = False
            self.ui.set_recording_state(False)

        # Prioriza o buffer acumulado; se vazio, pega o texto atualmente digitado/exibido na UI
        consolidated_question = " ".join(self.transcript_buffer).strip()
        if not consolidated_question:
            consolidated_question = self.ui.get_transcription_text()

        if not consolidated_question:
            self.ui.set_status("● Nenhuma fala capturada", "#F38BA8")
            logger.warning("Nenhum texto disponível para responder.")
            return

        self.ui.update_transcription(consolidated_question, is_final=True)
        self.ui.set_status("⏳ Gerando resposta...", "#89B4FA")
        logger.info(f"Disparando resposta para: '{consolidated_question}'")

        # Cancela requisição anterior do LLM caso haja uma em andamento
        if self.current_llm_task and not self.current_llm_task.done():
            self.current_llm_task.cancel()

        # Dispara task assíncrona para streaming da resposta
        if self.loop and self.loop.is_running():
            self.current_llm_task = self.loop.create_task(self._process_llm_stream(consolidated_question))

    def clear_session(self) -> None:
        """Limpa dados da tela e cancela qualquer processamento pendente."""
        self.transcript_buffer.clear()
        self.ui.clear_all()
        self.ui.set_status("● Pronto", "#A6ADC8")
        if self.current_llm_task and not self.current_llm_task.done():
            self.current_llm_task.cancel()
        logger.info("Sessão limpa pelo usuário.")

    def on_connection_change(self, is_connected: bool) -> None:
        """Callback chamada quando o estado da conexão com o Deepgram se altera."""
        if not is_connected:
            if self.loop and self.loop.is_running():
                self.loop.call_soon_threadsafe(self.ui.set_status, "🔄 Reconectando áudio...", "#F9E2AF")
            else:
                self.ui.set_status("🔄 Reconectando áudio...", "#F9E2AF")
            logger.warning("Deepgram desconectado. Tentativa de reconexão automática em andamento...")
        else:
            if self.loop and self.loop.is_running():
                self.loop.call_soon_threadsafe(self.ui.set_status, "● Pronto", "#A6ADC8")
            else:
                self.ui.set_status("● Pronto", "#A6ADC8")
            logger.info("Deepgram conectado e operacional.")

    def on_audio_data(self, data: bytes) -> None:
        """Callback chamada a cada chunk de áudio capturado. Calcula RMS para o VU-meter e envia áudio se gravando."""
        try:
            samples = np.frombuffer(data, dtype=np.int16)
            rms = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))
        except Exception:
            rms = 0.0

        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.ui.update_audio_level, rms)
        else:
            self.ui.update_audio_level(rms)

        if self.is_recording:
            self.transcriber.send_audio(data)

    def on_interim_transcript(self, text: str) -> None:
        """Callback para transcrições parciais - concatena ao buffer existente e exibe na UI."""
        if not self.is_recording:
            return

        current_full = " ".join(self.transcript_buffer + [text]).strip()
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.ui.update_transcription, current_full, False)
        else:
            self.ui.update_transcription(current_full, is_final=False)

    def on_final_transcript(self, text: str) -> None:
        """Callback para sentenças finalizadas - adiciona ao buffer de fala consolidado."""
        if not self.is_recording:
            return

        text = text.strip()
        if text:
            self.transcript_buffer.append(text)
            current_full = " ".join(self.transcript_buffer).strip()
            if self.loop and self.loop.is_running():
                self.loop.call_soon_threadsafe(self.ui.update_transcription, current_full, False)

    async def _process_llm_stream(self, question: str) -> None:
        """Processa o streaming de tokens da Groq e envia para a UI de forma segura."""
        self.ui.clear_ai_response()
        try:
            async for token in self.llm_service.stream_response(question):
                self.ui.append_ai_token(token)
            self.ui.set_status("● Resposta Concluída", "#A6E3A1")
        except asyncio.CancelledError:
            logger.info("Task de geração de LLM cancelada para nova pergunta.")
        except Exception as e:
            logger.error(f"Erro no streaming LLM: {e}")
            self.ui.set_status("● Erro na resposta", "#F38BA8")

    async def run(self) -> None:
        """Malha principal do evento asyncio unificada com o Tkinter event loop."""
        self.loop = asyncio.get_running_loop()
        logger.info("Iniciando componentes do Interview Copilot...")
        
        # Conecta ao WebSocket da Deepgram
        await self.transcriber.start()

        # Inicia a captura de áudio loopback
        self.audio_capture.start(self.loop)

        logger.info("Interview Copilot executando. Pressione fechar no overlay para sair.")

        # Event Loop unificado Asyncio + CustomTkinter
        try:
            while True:
                # Atualiza a UI do Tkinter sem bloquear o asyncio
                self.ui.update()
                await asyncio.sleep(0.01)
        except Exception:
            # Captura o fechamento da janela Tkinter
            pass
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Finalização limpa e liberação de recursos."""
        logger.info("Encerrando aplicação...")
        self.audio_capture.stop()
        await self.transcriber.close()
        if self.current_llm_task and not self.current_llm_task.done():
            self.current_llm_task.cancel()
        logger.info("Aplicação encerrada com sucesso.")


def main() -> None:
    app = CopilotApp()
    try:
        asyncio.run(app.run())
    except KeyboardInterrupt:
        logger.info("Aplicação interrompida pelo usuário.")


if __name__ == "__main__":
    main()
