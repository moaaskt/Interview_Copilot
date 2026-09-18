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
from config_manager import ConfigManager
from hotkey_manager import HotkeyManager
from question_detector import QuestionDetector

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
        self.gemini_key = os.getenv("GEMINI_API_KEY")

        if not self.deepgram_key or not self.groq_key:
            missing = []
            if not self.deepgram_key:
                missing.append("DEEPGRAM_API_KEY")
            if not self.groq_key:
                missing.append("GROQ_API_KEY (ou OPENAI_API_KEY)")
            logger.error(f"Configuração incompleta no arquivo .env ({env_path}). Chave(s) ausente(s): {', '.join(missing)}")
            sys.exit(1)

        self.config_manager = ConfigManager()

        self.ui = CopilotUI(
            on_start_recording=self.start_recording,
            on_stop_recording=self.stop_recording,
            on_toggle_recording=self.toggle_recording,
            on_respond_now=self.respond_now,
            on_clear=self.clear_session,
            config_manager=self.config_manager,
            on_quick_question=self.on_quick_question,
            on_device_change=self.on_device_change,
            on_llm_change=self.on_llm_change,
            on_hotkeys_change=self.on_hotkeys_change,
            on_question_detection_change=self.on_question_detection_change,
            on_pre_roll_change=self.on_pre_roll_change,
        )
        self.llm_service = LLMService(
            api_key=self.groq_key,
            gemini_api_key=self.gemini_key,
            response_style=self.config_manager.response_style,
            custom_persona=self.config_manager.custom_persona,
            on_provider_change=self.on_provider_change,
            on_status_notice=self.on_status_notice,
            on_token_usage_change=self.on_token_usage_change,
        )
        self.transcriber = Transcriber(
            api_key=self.deepgram_key,
            on_interim_transcript=self.on_interim_transcript,
            on_final_transcript=self.on_final_transcript,
            on_connection_change=self.on_connection_change,
            language=self.config_manager.transcription_language,
            keywords=self.config_manager.get_combined_keywords(),
            endpointing=self.config_manager.transcription_endpointing_ms,
        )
        self.audio_capture = AudioCapture(
            audio_callback=self.on_audio_data,
            device_index=self.config_manager.audio_device_index,
            device_name=self.config_manager.audio_device_name,
            pre_roll_seconds=self.config_manager.pre_roll_seconds,
        )

        # Gerenciador de Atalhos Globais do Sistema Operacional (pynput)
        hotkey_callbacks = {
            "toggle_recording": self.toggle_recording,
            "toggle_recording_alt": self.toggle_recording,
            "respond_now": self.respond_now,
            "clear_session": self.clear_session,
            "clear_session_alt": self.clear_session,
            "cycle_position": self.ui.cycle_window_position,
            "cycle_opacity": self.ui.cycle_opacity,
            "open_settings": self.ui.open_settings,
        }
        self.hotkey_manager = HotkeyManager(
            callbacks=hotkey_callbacks,
            hotkeys=self.config_manager.hotkeys,
        )

        self.loop: asyncio.AbstractEventLoop | None = None
        self.current_llm_task: asyncio.Task | None = None
        self.decay_task: asyncio.Task | None = None
        self.auto_trigger_task: asyncio.Task | None = None

        # Motor determinístico de detecção de perguntas
        self.question_detector = QuestionDetector()

        # Estado da gravação e controle de epoch de isolamento de sessão
        self.is_recording = False
        self._recording_epoch = 0
        self.transcript_buffer: list[str] = []

    def on_quick_question(self, question: str) -> None:
        """Manipula clique em pergunta rápida pré-configurada."""
        if self.is_recording:
            self.stop_recording()

        self.transcript_buffer = [question]
        self.ui.update_transcription(question, is_final=True)
        logger.info(f"Pergunta rápida selecionada: '{question}'")
        self.respond_now()

    def on_device_change(self, device_idx: Optional[int], device_name: str) -> None:
        """Callback chamada quando o usuário altera o dispositivo de áudio na tela de configurações."""
        logger.info(f"Alterando dispositivo de áudio para: [{device_idx}] {device_name}")
        self.audio_capture.set_device(device_idx, self.loop, device_name=device_name)
        self.ui.set_status(f"● Áudio: {device_name[:18]}", "#A6E3A1")

    def on_llm_change(self, style: str, custom_persona: Optional[str]) -> None:
        """Callback chamada quando o usuário altera o estilo de resposta ou persona na tela de configurações."""
        logger.info(f"Atualizando configurações de IA: estilo='{style}'")
        self.llm_service.set_response_style(style)
        self.llm_service.set_system_prompt(custom_persona)
        self.ui.set_status(f"● IA: {style.capitalize()}", "#89B4FA")

    def on_hotkeys_change(self, new_hotkeys: dict) -> None:
        """Callback chamada quando o usuário altera os atalhos na tela de configurações."""
        logger.info(f"Atualizando atalhos globais no HotkeyManager: {new_hotkeys}")
        self.hotkey_manager.update_hotkeys(new_hotkeys)

    def on_question_detection_change(self, enabled: bool) -> None:
        """Callback chamada quando o usuário ativa ou desativa a detecção de perguntas nas configurações."""
        logger.info(f"Detecção de perguntas alterada para: enabled={enabled}")
        if not enabled:
            self._cancel_auto_trigger()
            if self.loop and self.loop.is_running():
                self.loop.call_soon_threadsafe(self.ui.set_question_detected, False)
            else:
                self.ui.set_question_detected(False)
            self.on_status_notice("🎯 Detecção de Perguntas: Desativada", "#A6ADC8")
        else:
            self.on_status_notice("🎯 Detecção de Perguntas: Ativada", "#A6E3A1")

    def on_pre_roll_change(self, enabled: bool) -> None:
        """Callback chamada quando o usuário ativa ou desativa o pré-roll de áudio nas configurações."""
        logger.info(f"Pré-roll de áudio alterado para: enabled={enabled}")
        if not enabled and hasattr(self, "audio_capture") and hasattr(self.audio_capture, "pre_roll_buffer"):
            self.audio_capture.pre_roll_buffer.clear()
        if enabled:
            self.on_status_notice("🎙 Pré-Roll: Ativado", "#A6E3A1")
        else:
            self.on_status_notice("🎙 Pré-Roll: Desativado", "#A6ADC8")

    def on_provider_change(self, provider_name: str) -> None:
        """Callback chamada quando o serviço LLM altera o provedor (ex: de Groq para Gemini)."""
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.ui.set_ai_provider, provider_name)
        else:
            self.ui.set_ai_provider(provider_name)

    def on_status_notice(self, message: str, color: str = "#F9E2AF") -> None:
        """Callback chamada quando um aviso transitório de sistema deve ser exibido no HUD."""
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.ui.set_status, message, color)
        else:
            self.ui.set_status(message, color)

    def on_token_usage_change(self, used: int, limit: int) -> None:
        """Callback chamada quando a contagem de tokens por minuto (TPM) é atualizada."""
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.ui.update_token_usage, used, limit)
        else:
            self.ui.update_token_usage(used, limit)

    async def _decay_tokens_loop(self) -> None:
        """Loop em background para decaimento suave em tempo real do uso de TPM a cada 1 segundo."""
        while True:
            try:
                await asyncio.sleep(1.0)
                if hasattr(self, "llm_service") and hasattr(self.llm_service, "token_tracker"):
                    tracker = self.llm_service.token_tracker
                    current_tpm = tracker.get_current_tpm()
                    if self.loop and self.loop.is_running():
                        self.loop.call_soon_threadsafe(self.ui.update_token_usage, current_tpm, tracker.limit)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.debug(f"[CopilotApp] Erro no loop de decaimento de TPM: {e}")

    def _cancel_auto_trigger(self) -> None:
        """Cancela qualquer auto-trigger pendente de forma segura."""
        task = getattr(self, "auto_trigger_task", None)
        if task and not task.done():
            task.cancel()
            self.auto_trigger_task = None

    def start_recording(self) -> None:
        """Inicia uma nova captura de áudio caso nenhuma gravação esteja ativa."""
        if self.is_recording:
            logger.info("Comando GRAVAR ignorado: gravação já está em andamento.")
            return
        self._start_recording()

    def stop_recording(self) -> None:
        """Encerra a gravação ativa sem disparar a resposta automaticamente."""
        if not self.is_recording:
            logger.info("Comando PARAR ignorado: nenhuma gravação ativa.")
            return

        self._cancel_auto_trigger()
        self.is_recording = False
        self._recording_epoch += 1  # Invalida mensagens residuais em trânsito
        self.audio_capture.stop_recording()
        self.ui.set_recording_state(False)
        logger.info("⏹ Gravação pausada/finalizada pelo usuário.")

    def toggle_recording(self) -> None:
        """Alterna entre iniciar e parar gravação (compatibilidade com atalhos de teclado)."""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def _start_recording(self) -> None:
        """Inicia uma nova rodada de gravação isolada, limpando o buffer e descartando resíduos."""
        self._cancel_auto_trigger()
        self._recording_epoch += 1  # Novo identificador monotônico de sessão
        self.transcript_buffer.clear()
        self.ui.clear_all()
        self.ui.set_recording_state(True)
        self.ui.set_question_detected(False)

        pre_roll_chunks = self.audio_capture.start_recording()
        if self.config_manager.pre_roll_enabled and pre_roll_chunks:
            pre_roll_sec = len(pre_roll_chunks) * (self.audio_capture.chunk_size / self.audio_capture.sample_rate)
            logger.info(f"🎙 Gravação iniciada com injeção de {len(pre_roll_chunks)} chunks pré-gravados (~{pre_roll_sec:.1f}s).")
            for chunk in pre_roll_chunks:
                self.transcriber.send_audio(chunk)
        else:
            if not self.config_manager.pre_roll_enabled:
                logger.info("🎙 Gravação iniciada sem pré-roll (chunks anteriores descartados).")
            else:
                logger.info("🎙 Gravação iniciada. Aguardando a fala da pergunta...")

        self.is_recording = True

    def _stop_and_respond(self) -> None:
        """Para a gravação e envia o texto consolidado para a IA."""
        self.stop_recording()
        self.respond_now()

    def respond_now(self) -> None:
        """Dispara a geração de resposta com base na transcrição acumulada ou visível na tela."""
        self._cancel_auto_trigger()

        # Se ainda estiver gravando, encerra a captura
        if self.is_recording:
            self.stop_recording()

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
        self._cancel_auto_trigger()
        if self.is_recording:
            self.stop_recording()
        self._recording_epoch += 1  # Invalida mensagens em trânsito
        self.transcript_buffer.clear()
        self.ui.clear_all()
        self.ui.set_question_detected(False)
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
        """Callback para transcrições parciais - concatena ao buffer provisório, cancela timers ativos e NÃO confirma pergunta."""
        if not self.is_recording:
            return

        # Fala em andamento: cancela imediatamente qualquer timer de auto-trigger pendente
        self._cancel_auto_trigger()

        current_full = " ".join(self.transcript_buffer + [text]).strip()
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.ui.update_transcription, current_full, False)
            if self.config_manager.question_detection_enabled:
                self.loop.call_soon_threadsafe(self.ui.set_question_detected, False)
        else:
            self.ui.update_transcription(current_full, is_final=False)
            if self.config_manager.question_detection_enabled:
                self.ui.set_question_detected(False)

    def on_final_transcript(self, text: str) -> None:
        """Callback para sentenças finalizadas - autoridade única para confirmação de pergunta e agendamento de auto-trigger."""
        if not self.is_recording:
            return

        text = text.strip()
        if text:
            self.transcript_buffer.append(text)
            current_full = " ".join(self.transcript_buffer).strip()
            if self.loop and self.loop.is_running():
                self.loop.call_soon_threadsafe(self.ui.update_transcription, current_full, False)
            else:
                self.ui.update_transcription(current_full, is_final=False)

            if self.config_manager.question_detection_enabled:
                detection = self.question_detector.detect(current_full)
                if self.loop and self.loop.is_running():
                    self.loop.call_soon_threadsafe(self.ui.set_question_detected, detection.is_question)
                else:
                    self.ui.set_question_detected(detection.is_question)

                # Auto-trigger é agendado EXCLUSIVAMENTE em transcrição final com pergunta confirmada
                if detection.is_question and self.config_manager.auto_trigger_enabled:
                    self._schedule_auto_trigger()
                else:
                    self._cancel_auto_trigger()
            else:
                if self.loop and self.loop.is_running():
                    self.loop.call_soon_threadsafe(self.ui.set_question_detected, False)
                else:
                    self.ui.set_question_detected(False)
                self._cancel_auto_trigger()

    def _schedule_auto_trigger(self) -> None:
        """Agenda o auto-trigger debounced após silêncio configurado."""
        self._cancel_auto_trigger()
        if self.loop and self.loop.is_running():
            delay_sec = self.config_manager.silence_delay_ms / 1000.0
            self.auto_trigger_task = self.loop.create_task(self._auto_trigger_countdown(delay_sec))

    async def _auto_trigger_countdown(self, delay_sec: float) -> None:
        """Aguarda a janela de silêncio antes de acionar a resposta automaticamente."""
        try:
            await asyncio.sleep(delay_sec)
            if self.is_recording:
                logger.info(f"🎯 Auto-trigger disparado após {delay_sec:.1f}s de silêncio pós-pergunta.")
                self._stop_and_respond()
        except asyncio.CancelledError:
            logger.debug("Auto-trigger cancelado por nova fala ou ação do usuário.")

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

        # Inicia a escuta de atalhos globais do sistema operacional
        self.hotkey_manager.set_loop(self.loop)
        self.hotkey_manager.start()

        # Inicia o loop em background de decaimento em tempo real de TPM
        self.decay_task = self.loop.create_task(self._decay_tokens_loop())

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
        self._cancel_auto_trigger()
        if self.decay_task and not self.decay_task.done():
            self.decay_task.cancel()
        self.hotkey_manager.stop()
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
