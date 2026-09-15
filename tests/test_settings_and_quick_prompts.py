import os
import tempfile
import unittest
from unittest.mock import MagicMock

from src.config_manager import ConfigManager, DEFAULT_CONFIG
from src.audio_capture import AudioCapture
from src.llm_service import LLMService, DEFAULT_PERSONA
from src.ui import CopilotUI
from src.settings_window import SettingsWindow
from src.main import CopilotApp


class TestSettingsAndQuickPrompts(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()
        self.config_manager = ConfigManager(config_path=self.temp_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            try:
                os.remove(self.temp_file.name)
            except Exception:
                pass

    # ==========================================
    # TESTES CONFIG MANAGER
    # ==========================================
    def test_config_manager_defaults(self):
        self.assertEqual(self.config_manager.response_style, "direta")
        self.assertIsNone(self.config_manager.audio_device_index)
        self.assertEqual(self.config_manager.audio_device_name, "Padrão do Sistema")
        self.assertIn("toggle_recording", self.config_manager.hotkeys)
        self.assertGreaterEqual(len(self.config_manager.quick_questions), 5)

    def test_config_manager_set_and_save(self):
        self.config_manager.set("llm", "response_style", "tecnica")
        self.config_manager.set("audio", "device_index", 3)
        self.config_manager.set("audio", "device_name", "Microfone USB")

        # Recarrega em nova instância para validar persistência em disco
        reloaded = ConfigManager(config_path=self.temp_file.name)
        self.assertEqual(reloaded.response_style, "tecnica")
        self.assertEqual(reloaded.audio_device_index, 3)
        self.assertEqual(reloaded.audio_device_name, "Microfone USB")

    def test_config_manager_reset_defaults(self):
        self.config_manager.set("llm", "response_style", "star")
        self.config_manager.reset_defaults()
        self.assertEqual(self.config_manager.response_style, "direta")

    # ==========================================
    # TESTES AUDIO CAPTURE
    # ==========================================
    def test_audio_capture_list_devices(self):
        devices = AudioCapture.list_available_devices()
        self.assertIsInstance(devices, list)
        for dev in devices:
            self.assertIn("index", dev)
            self.assertIn("name", dev)

    def test_audio_capture_set_device(self):
        capture = AudioCapture(audio_callback=MagicMock(), device_index=1)
        self.assertEqual(capture.device_index, 1)
        capture.set_device(5)
        self.assertEqual(capture.device_index, 5)

    # ==========================================
    # TESTES LLM SERVICE ESTILOS & PERSONA
    # ==========================================
    def test_llm_service_response_styles(self):
        llm = LLMService(api_key="dummy_key", response_style="direta")
        self.assertIn("DIRETA & CONCISA", llm.get_effective_system_prompt())

        llm.set_response_style("tecnica")
        self.assertEqual(llm.response_style, "tecnica")
        self.assertIn("TÉCNICA & APROFUNDADA", llm.get_effective_system_prompt())

        llm.set_response_style("star")
        self.assertEqual(llm.response_style, "star")
        self.assertIn("MÉTODO STAR", llm.get_effective_system_prompt())

    def test_llm_service_custom_persona(self):
        llm = LLMService(api_key="dummy_key", custom_persona="Persona de teste para dev backend")
        prompt = llm.get_effective_system_prompt()
        self.assertIn("Persona de teste para dev backend", prompt)

        # Atualiza em runtime
        llm.set_system_prompt("Nova persona atualizada")
        self.assertIn("Nova persona atualizada", llm.get_effective_system_prompt())

        # Reset para default
        llm.set_system_prompt(None)
        self.assertIn("Moacir Neto", llm.get_effective_system_prompt())

    # ==========================================
    # TESTES UI, SETTINGS & QUICK PROMPTS
    # ==========================================
    def test_ui_settings_window_open_and_vu_update(self):
        ui = CopilotUI(config_manager=self.config_manager)
        ui.update()

        try:
            # Abre configurações
            ui.open_settings()
            ui.update()
            self.assertIsNotNone(ui.settings_window)
            self.assertTrue(ui.settings_window.winfo_exists())

            # Atualiza nível de áudio e verifica reflexo na modal de configurações
            ui.update_audio_level(3000.0)
            self.assertEqual(ui.settings_window.vu_indicator_label.cget("text"), "🎙 ▃▅█")
            self.assertGreater(ui.settings_window.vu_progress_bar.get(), 0.5)

            # Fecha modal
            ui.settings_window.destroy()
            ui.update()
        finally:
            ui.destroy()

    def test_ui_quick_prompt_dispatch(self):
        mock_quick = MagicMock()
        ui = CopilotUI(config_manager=self.config_manager, on_quick_question=mock_quick)
        ui.update()

        try:
            sample_question = "Fale mais sobre você e sua trajetória profissional"
            ui._handle_quick_prompt(sample_question)
            mock_quick.assert_called_once_with(sample_question)
        finally:
            ui.destroy()

    def test_ui_apply_hotkeys(self):
        ui = CopilotUI(config_manager=self.config_manager)
        ui.update()

        try:
            new_hotkeys = {
                "toggle_recording": "<Control-Shift-R>",
                "respond_now": "<Control-Shift-A>",
                "clear_session": "<Control-Shift-C>",
            }
            ui.apply_hotkeys(new_hotkeys)
            self.assertIn("Ctrl+Shift+R", ui.record_btn.cget("text"))
            self.assertIn("Ctrl+Shift+A", ui.respond_btn.cget("text"))
            self.assertIn("Ctrl+Shift+C", ui.clear_btn.cget("text"))
        finally:
            ui.destroy()

    # ==========================================
    # TESTES INTEGRAÇÃO COPILOT APP
    # ==========================================
    def test_copilot_app_callbacks(self):
        app = object.__new__(CopilotApp)
        app.loop = None
        app.is_recording = True
        app.transcript_buffer = []
        app.ui = MagicMock()
        app.respond_now = MagicMock()
        app.audio_capture = MagicMock()
        app.llm_service = MagicMock()

        # Disparo de Pergunta Rápida
        app.on_quick_question("Qual a arquitetura do projeto?")
        self.assertFalse(app.is_recording)
        self.assertEqual(app.transcript_buffer, ["Qual a arquitetura do projeto?"])
        app.ui.update_transcription.assert_called_with("Qual a arquitetura do projeto?", is_final=True)
        app.respond_now.assert_called_once()

        # Alteração de Dispositivo de Áudio
        app.on_device_change(2, "Fones de ouvido USB")
        app.audio_capture.set_device.assert_called_with(2, None)
        app.ui.set_status.assert_called()

        # Alteração de Configurações de IA
        app.on_llm_change("tecnica", "Nova Persona")
        app.llm_service.set_response_style.assert_called_with("tecnica")
        app.llm_service.set_system_prompt.assert_called_with("Nova Persona")


if __name__ == "__main__":
    unittest.main()
