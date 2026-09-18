import asyncio
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

# Adiciona src ao sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from question_detector import QuestionDetector, QuestionDetectionResult
from config_manager import ConfigManager
from ui import CopilotUI
from main import CopilotApp


class TestQuestionDetector(unittest.TestCase):
    """Testes unitários para o motor determinístico de classificação de perguntas."""

    def setUp(self):
        self.detector = QuestionDetector()

    def test_detect_direct_question_mark_pt(self):
        res = self.detector.detect("Você já trabalhou com microserviços em PHP?")
        self.assertTrue(res.is_question)
        self.assertEqual(res.reason, "punctuation")
        self.assertGreaterEqual(res.confidence, 0.90)

    def test_detect_direct_question_mark_en(self):
        res = self.detector.detect("How do you handle database migrations in production?")
        self.assertTrue(res.is_question)
        self.assertEqual(res.reason, "punctuation")
        self.assertGreaterEqual(res.confidence, 0.90)

    def test_detect_interview_opener_pt(self):
        res = self.detector.detect("Me conte sobre sua experiência com FastAPI e Docker")
        self.assertTrue(res.is_question)
        self.assertEqual(res.reason, "interview_pattern")
        self.assertGreaterEqual(res.confidence, 0.70)

    def test_detect_interview_opener_en(self):
        res = self.detector.detect("Tell me about a challenging bug you fixed recently")
        self.assertTrue(res.is_question)
        self.assertEqual(res.reason, "interview_pattern")
        self.assertGreaterEqual(res.confidence, 0.70)

    def test_detect_interrogative_opener_pt(self):
        res = self.detector.detect("Como você implementaria um cache distribuído com Redis")
        self.assertTrue(res.is_question)
        self.assertEqual(res.reason, "interrogative")
        self.assertGreaterEqual(res.confidence, 0.70)

    def test_detect_interrogative_opener_en(self):
        res = self.detector.detect("Why would you choose PostgreSQL over MongoDB")
        self.assertTrue(res.is_question)
        self.assertEqual(res.reason, "interrogative")
        self.assertGreaterEqual(res.confidence, 0.70)

    def test_affirmative_with_interrogative_word_in_middle(self):
        # A palavra 'como' está no meio de uma frase puramente afirmativa
        res = self.detector.detect("Nós utilizamos o Docker como ambiente principal de desenvolvimento.")
        self.assertFalse(res.is_question)
        self.assertEqual(res.reason, "none")
        self.assertLess(res.confidence, 0.70)

    def test_affirmative_simple_sentence(self):
        res = self.detector.detect("Trabalho com backend há mais de 5 anos.")
        self.assertFalse(res.is_question)
        self.assertEqual(res.reason, "none")
        self.assertLess(res.confidence, 0.70)

    def test_empty_or_none_input(self):
        res_none = self.detector.detect(None)
        self.assertFalse(res_none.is_question)
        self.assertEqual(res_none.confidence, 0.0)

        res_empty = self.detector.detect("")
        self.assertFalse(res_empty.is_question)
        self.assertEqual(res_empty.confidence, 0.0)

        res_spaces = self.detector.detect("   ")
        self.assertFalse(res_spaces.is_question)
        self.assertEqual(res_spaces.confidence, 0.0)

    def test_accentuation_and_case_insensitivity(self):
        res = self.detector.detect("QUAL É SUA EXPERIÊNCIA COM CI/CD")
        self.assertTrue(res.is_question)
        self.assertIn(res.reason, ["interview_pattern", "interrogative"])

    def test_clause_interrogative_detection(self):
        res = self.detector.detect("No último projeto, como você estruturou a camada de serviços")
        self.assertTrue(res.is_question)
        self.assertEqual(res.reason, "interrogative")


import tempfile
from pathlib import Path


class TestConfigManagerQuestionDetection(unittest.TestCase):
    """Testes para as configurações e defaults de detecção de pergunta."""

    def test_default_config_properties(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test_config_defaults.json"
            cfg = ConfigManager(config_path=str(config_file))
            self.assertTrue(cfg.question_detection_enabled)
            self.assertFalse(cfg.auto_trigger_enabled)
            self.assertEqual(cfg.silence_delay_ms, 1200)

    def test_custom_config_properties(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test_config_custom.json"
            cfg = ConfigManager(config_path=str(config_file))
            cfg.set("question_detection", "auto_trigger_on_silence", True)
            cfg.set("question_detection", "silence_delay_ms", 1500)
            self.assertTrue(cfg.auto_trigger_enabled)
            self.assertEqual(cfg.silence_delay_ms, 1500)


class TestUIQuestionDetection(unittest.TestCase):
    """Testes para o comportamento de realce visual no CopilotUI."""

    @patch("customtkinter.CTk.__init__", return_value=None)
    @patch("customtkinter.CTkFrame")
    @patch("customtkinter.CTkLabel")
    @patch("customtkinter.CTkTextbox")
    @patch("customtkinter.CTkButton")
    @patch("customtkinter.CTkProgressBar")
    @patch("tkinter.Frame")
    @patch("tkinter.Label")
    def test_set_question_detected_toggle(self, *mocks):
        ui = CopilotUI.__new__(CopilotUI)
        ui.transcription_label = MagicMock()
        ui.transcription_textbox = MagicMock()
        ui._opacity_profiles = [{"border": "#313244"}]
        ui._current_opacity_idx = 0
        ui._is_question_detected = False

        # Ativa highlight
        ui.set_question_detected(True)
        self.assertTrue(ui._is_question_detected)
        ui.transcription_label.configure.assert_called_with(
            text="🎯 Pergunta Detectada:",
            text_color="#FAB387"
        )
        ui.transcription_textbox.configure.assert_called_with(
            border_width=2,
            border_color="#FAB387"
        )

        # Desativa highlight
        ui.set_question_detected(False)
        self.assertFalse(ui._is_question_detected)
        ui.transcription_label.configure.assert_called_with(
            text="Pergunta Transcrita:",
            text_color="#A6ADC8"
        )
        ui.transcription_textbox.configure.assert_called_with(
            border_width=0,
            border_color="#313244"
        )


class TestMainQuestionDetectorIntegration(unittest.TestCase):
    """Testes de integração para o ciclo de vida do auto-trigger no CopilotApp."""

    @patch("main.CopilotUI")
    @patch("main.LLMService")
    @patch("main.Transcriber")
    @patch("main.AudioCapture")
    @patch("main.HotkeyManager")
    @patch("main.load_dotenv")
    @patch.dict(os.environ, {"DEEPGRAM_API_KEY": "dummy_dg", "GROQ_API_KEY": "dummy_groq"})
    def test_auto_trigger_lifecycle(self, *mocks):
        app = CopilotApp()
        app.loop = MagicMock()
        app.loop.is_running.return_value = True

        # 1. Com auto_trigger desligado (default), final transcript com pergunta não agenda auto_trigger
        app.config_manager.set("question_detection", "auto_trigger_on_silence", False)
        app.is_recording = True
        with patch.object(app, "_schedule_auto_trigger") as mock_schedule:
            app.on_final_transcript("Qual é a sua experiência com Docker?")
            mock_schedule.assert_not_called()

        # 2. Com auto_trigger ligado, final transcript com pergunta agenda auto_trigger
        app.config_manager.set("question_detection", "auto_trigger_on_silence", True)
        with patch.object(app, "_schedule_auto_trigger") as mock_schedule:
            app.on_final_transcript("Como você aborda testes unitários?")
            mock_schedule.assert_called_once()

        # 3. Cancelamento ao iniciar gravação / limpar sessão / responder
        mock_task = MagicMock()
        mock_task.done.return_value = False
        app.auto_trigger_task = mock_task
        app._cancel_auto_trigger()
        mock_task.cancel.assert_called_once()
        self.assertIsNone(app.auto_trigger_task)


if __name__ == "__main__":
    unittest.main()
