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
        self._orig_groq_key = os.environ.get("GROQ_API_KEY")
        self._orig_openai_key = os.environ.get("OPENAI_API_KEY")
        self._orig_gemini_key = os.environ.get("GEMINI_API_KEY")
        self.temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_file.close()
        self.config_manager = ConfigManager(config_path=self.temp_file.name)

    def tearDown(self):
        if self._orig_groq_key is None:
            os.environ.pop("GROQ_API_KEY", None)
        else:
            os.environ["GROQ_API_KEY"] = self._orig_groq_key

        if self._orig_openai_key is None:
            os.environ.pop("OPENAI_API_KEY", None)
        else:
            os.environ["OPENAI_API_KEY"] = self._orig_openai_key

        if self._orig_gemini_key is None:
            os.environ.pop("GEMINI_API_KEY", None)
        else:
            os.environ["GEMINI_API_KEY"] = self._orig_gemini_key

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
        app._recording_epoch = 0
        app.auto_trigger_task = None
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
        app.audio_capture.set_device.assert_called_with(2, None, device_name="Fones de ouvido USB")
        app.ui.set_status.assert_called()

        # Alteração de Configurações de IA
        app.on_llm_change("tecnica", "Nova Persona")
        app.llm_service.set_response_style.assert_called_with("tecnica")
        app.llm_service.set_system_prompt.assert_called_with("Nova Persona")

        # Alteração de Atalhos Globais
        app.hotkey_manager = MagicMock()
        app.on_hotkeys_change({"toggle_recording": "<Control-g>"})
        app.hotkey_manager.update_hotkeys.assert_called_with({"toggle_recording": "<Control-g>"})

        # Alteração dinâmica de Chaves de API
        app.on_api_keys_change("gsk_live", "AIza_live")
        self.assertEqual(app.groq_key, "gsk_live")
        self.assertEqual(app.gemini_key, "AIza_live")
        app.llm_service.update_api_keys.assert_called_with("gsk_live", "AIza_live")

    def test_key_capture_parsing_and_formatting(self):
        try:
            from settings_window import format_tk_to_user, parse_key_event
        except ImportError:
            from src.settings_window import format_tk_to_user, parse_key_event

        self.assertEqual(format_tk_to_user("<Control-space>"), "Ctrl + Espaço")
        self.assertEqual(format_tk_to_user("<Control-Return>"), "Ctrl + Enter")
        self.assertEqual(format_tk_to_user("<Escape>"), "Esc")
        self.assertEqual(format_tk_to_user("<F12>"), "F12")

        class MockEvent:
            def __init__(self, keysym, state):
                self.keysym = keysym
                self.state = state

        # Modificador isolado (não deve disparar bind)
        self.assertIsNone(parse_key_event(MockEvent("Control_L", 4)))

        # Tecla com modificador
        tk_bind, user_repr = parse_key_event(MockEvent("space", 4))
        self.assertEqual(tk_bind, "<Control-space>")
        self.assertEqual(user_repr, "Ctrl + Espaço")

        # Tecla de função
        tk_bind_f, user_repr_f = parse_key_event(MockEvent("F11", 0))
        self.assertEqual(tk_bind_f, "<F11>")
        self.assertEqual(user_repr_f, "F11")

    def test_hotkey_manager_global_conversion_and_dispatch(self):
        try:
            from hotkey_manager import HotkeyManager, to_pynput_hotkey
        except ImportError:
            from src.hotkey_manager import HotkeyManager, to_pynput_hotkey

        self.assertEqual(to_pynput_hotkey("<Control-space>"), "<ctrl>+<space>")
        self.assertEqual(to_pynput_hotkey("<Control-Return>"), "<ctrl>+<enter>")
        self.assertEqual(to_pynput_hotkey("<Escape>"), "<esc>")
        self.assertEqual(to_pynput_hotkey("<F12>"), "<f12>")
        self.assertEqual(to_pynput_hotkey("<Control-Shift-r>"), "<ctrl>+<shift>+r")

        called = []
        callbacks = {"toggle_recording": lambda: called.append("toggled")}
        mgr = HotkeyManager(callbacks=callbacks, hotkeys={"toggle_recording": "<Control-space>"})
        mgr._dispatch_callback("toggle_recording")
        self.assertEqual(called, ["toggled"])

    def test_quick_prompt_entry_parsing(self):
        ui = CopilotUI(config_manager=self.config_manager)
        try:
            # Formato customizado Nome | Pergunta
            lbl, prompt = ui._parse_quick_prompt_entry("Experiência Go | Conte sobre seus projetos e experiência em Go")
            self.assertEqual(lbl, "Experiência Go")
            self.assertEqual(prompt, "Conte sobre seus projetos e experiência em Go")

            # Fallback sem pipe
            lbl_legacy, prompt_legacy = ui._parse_quick_prompt_entry("Fale mais sobre você e sua trajetória")
            self.assertEqual(lbl_legacy, "Sobre Mim")
            self.assertEqual(prompt_legacy, "Fale mais sobre você e sua trajetória")
        finally:
            ui.destroy()

    def test_llm_service_prompt_budget_fitting(self):
        from src.llm_service import LLMService
        service = LLMService(api_key="mock", custom_persona="A" * 30000)
        fitted = service._fit_prompt_to_budget(service.get_effective_system_prompt(), max_chars=18000)
        self.assertLessEqual(len(fitted), 18000)


    def test_quick_questions_save_and_reload_persistence(self):
        ui = CopilotUI(config_manager=self.config_manager)
        ui.update()

        try:
            ui.open_settings()
            ui.update()
            sw = ui.settings_window
            self.assertIsNotNone(sw)

            custom_lines = [
                "Meu Perfil | Fale sobre você e sua trajetória",
                "NodeJS | Explique como funciona o Event Loop no Node.js",
            ]
            sw.quick_textbox.delete("1.0", "end")
            sw.quick_textbox.insert("1.0", "\n".join(custom_lines))

            # Dispara salvamento
            sw._save_quick_questions()
            ui.update()

            # 1. Verifica persistência no ConfigManager em memória
            self.assertEqual(self.config_manager.quick_questions, custom_lines)

            # 2. Verifica persistência no arquivo em disco
            reloaded = ConfigManager(config_path=self.temp_file.name)
            self.assertEqual(reloaded.quick_questions, custom_lines)

            # 3. Verifica se os botões do HUD foram atualizados dinamicamente
            hud_buttons = []
            for child in ui.quick_prompts_frame.winfo_children():
                if isinstance(child, type(sw.save_quick_btn)):
                    hud_buttons.append(child)
                else:
                    for subchild in child.winfo_children():
                        if isinstance(subchild, type(sw.save_quick_btn)):
                            hud_buttons.append(subchild)
            button_texts = [b.cget("text") for b in hud_buttons]
            self.assertIn("Meu Perfil", button_texts)
            self.assertIn("NodeJS", button_texts)

            # 4. Fecha e reabre SettingsWindow para garantir que o texto carregado é o salvo
            sw.destroy()
            ui.update()

            ui.open_settings()
            ui.update()
            sw2 = ui.settings_window
            loaded_text = sw2.quick_textbox.get("1.0", "end").strip()
            self.assertEqual(loaded_text, "\n".join(custom_lines))
            sw2.destroy()
            ui.update()
        finally:
            ui.destroy()

    def test_question_detection_switch_and_persistence(self):
        mock_qd_callback = MagicMock()
        ui = CopilotUI(
            config_manager=self.config_manager,
            on_question_detection_change=mock_qd_callback
        )
        ui.update()

        try:
            ui.open_settings()
            ui.update()
            sw = ui.settings_window
            self.assertIsNotNone(sw)

            # 1. Default deve ser True
            self.assertTrue(self.config_manager.question_detection_enabled)
            self.assertEqual(sw.qd_switch.get(), 1)

            # 2. Desativa o switch
            sw.qd_switch.deselect()
            sw._on_toggle_question_detection()
            ui.update()

            self.assertFalse(self.config_manager.question_detection_enabled)
            mock_qd_callback.assert_called_with(False)

            # 3. Valida persistência em disco
            reloaded = ConfigManager(config_path=self.temp_file.name)
            self.assertFalse(reloaded.question_detection_enabled)

            # 4. Fecha e reabre SettingsWindow para conferir se o switch reflete o estado salvo (desativado)
            sw.destroy()
            ui.update()

            ui.open_settings()
            ui.update()
            sw2 = ui.settings_window
            self.assertEqual(sw2.qd_switch.get(), 0)

            # 5. Reativa o switch
            sw2.qd_switch.select()
            sw2._on_toggle_question_detection()
            ui.update()

            self.assertTrue(self.config_manager.question_detection_enabled)
            mock_qd_callback.assert_called_with(True)

            # 6. Valida persistência em disco do estado reativado
            reloaded2 = ConfigManager(config_path=self.temp_file.name)
            self.assertTrue(reloaded2.question_detection_enabled)
            sw2.destroy()
            ui.update()
        finally:
            ui.destroy()

    def test_pre_roll_switch_and_persistence(self):
        mock_pr_callback = MagicMock()
        ui = CopilotUI(
            config_manager=self.config_manager,
            on_pre_roll_change=mock_pr_callback
        )
        ui.update()

        try:
            ui.open_settings()
            ui.update()
            sw = ui.settings_window
            self.assertIsNotNone(sw)

            # 1. Default deve ser True
            self.assertTrue(self.config_manager.pre_roll_enabled)
            self.assertEqual(sw.pr_switch.get(), 1)

            # 2. Desativa o switch de pré-roll
            sw.pr_switch.deselect()
            sw._on_toggle_pre_roll()
            ui.update()

            self.assertFalse(self.config_manager.pre_roll_enabled)
            mock_pr_callback.assert_called_with(False)

            # 3. Valida persistência em disco
            reloaded = ConfigManager(config_path=self.temp_file.name)
            self.assertFalse(reloaded.pre_roll_enabled)

            # 4. Fecha e reabre SettingsWindow para conferir se o switch reflete o estado salvo (desativado)
            sw.destroy()
            ui.update()

            ui.open_settings()
            ui.update()
            sw2 = ui.settings_window
            self.assertEqual(sw2.pr_switch.get(), 0)

            # 5. Reativa o switch
            sw2.pr_switch.select()
            sw2._on_toggle_pre_roll()
            ui.update()

            self.assertTrue(self.config_manager.pre_roll_enabled)
            mock_pr_callback.assert_called_with(True)

            # 6. Valida persistência em disco do estado reativado
            reloaded2 = ConfigManager(config_path=self.temp_file.name)
            self.assertTrue(reloaded2.pre_roll_enabled)
            sw2.destroy()
            ui.update()
        finally:
            ui.destroy()

    def test_api_keys_config_persistence_and_fallback(self):
        os.environ["GROQ_API_KEY"] = "env_groq_fallback"
        os.environ["GEMINI_API_KEY"] = "env_gemini_fallback"

        # 1. Quando JSON está vazio, usa fallback das variáveis de ambiente
        self.assertEqual(self.config_manager.groq_api_key, "env_groq_fallback")
        self.assertEqual(self.config_manager.gemini_api_key, "env_gemini_fallback")

        # 2. Salva novas chaves via set_api_keys (com sanitização de espaços)
        self.config_manager.set_api_keys("  gsk_test_123  ", "  AIza_test_456  ", sync_env=False)
        self.assertEqual(self.config_manager.groq_api_key, "gsk_test_123")
        self.assertEqual(self.config_manager.gemini_api_key, "AIza_test_456")
        self.assertEqual(os.environ.get("GROQ_API_KEY"), "gsk_test_123")
        self.assertEqual(os.environ.get("GEMINI_API_KEY"), "AIza_test_456")

        # 3. Recarrega do arquivo JSON e confirma persistência
        reloaded = ConfigManager(config_path=self.temp_file.name)
        self.assertEqual(reloaded.groq_api_key, "gsk_test_123")
        self.assertEqual(reloaded.gemini_api_key, "AIza_test_456")

    def test_llm_service_update_api_keys_dynamically(self):
        llm = LLMService(api_key="old_groq", gemini_api_key=None)
        self.assertEqual(llm.api_key, "old_groq")
        self.assertIsNone(llm.gemini_api_key)

        llm.update_api_keys("  new_groq_key  ", "  new_gemini_key  ")
        self.assertEqual(llm.api_key, "new_groq_key")
        self.assertEqual(llm.client.api_key, "new_groq_key")
        self.assertEqual(llm.gemini_api_key, "new_gemini_key")

    def test_settings_window_api_keys_tab_save_and_toggle(self):
        os.environ["GROQ_API_KEY"] = "initial_groq_env"
        os.environ["GEMINI_API_KEY"] = "initial_gemini_env"

        mock_api_cb = MagicMock()
        ui = CopilotUI(
            config_manager=self.config_manager,
            on_api_keys_change=mock_api_cb
        )
        ui.update()

        try:
            ui.open_settings()
            ui.update()
            sw = ui.settings_window
            self.assertIsNotNone(sw)

            # 1. Seleciona aba de Chaves de API e verifica máscara padrão ("•")
            sw.tabview.set("🔑 Chaves de API")
            ui.update()
            self.assertEqual(sw.groq_key_entry.cget("show"), "•")
            self.assertEqual(sw.gemini_key_entry.cget("show"), "•")
            self.assertEqual(sw.groq_key_entry.get(), "initial_groq_env")
            self.assertEqual(sw.gemini_key_entry.get(), "initial_gemini_env")

            # 2. Alterna switch para mostrar texto visível
            sw.show_keys_switch.select()
            sw._toggle_show_api_keys()
            ui.update()
            self.assertEqual(sw.groq_key_entry.cget("show"), "")
            self.assertEqual(sw.gemini_key_entry.cget("show"), "")

            # 3. Alterna switch de volta para ocultar
            sw.show_keys_switch.deselect()
            sw._toggle_show_api_keys()
            ui.update()
            self.assertEqual(sw.groq_key_entry.cget("show"), "•")
            self.assertEqual(sw.gemini_key_entry.cget("show"), "•")

            # 4. Preenche novas chaves e salva
            sw.groq_key_entry.delete(0, "end")
            sw.groq_key_entry.insert(0, "  gsk_ui_key  ")
            sw.gemini_key_entry.delete(0, "end")
            sw.gemini_key_entry.insert(0, "  AIza_ui_key  ")

            sw._save_api_keys()
            ui.update()

            mock_api_cb.assert_called_once_with("gsk_ui_key", "AIza_ui_key")

            # 5. Verifica persistência em disco
            reloaded = ConfigManager(config_path=self.temp_file.name)
            self.assertEqual(reloaded.groq_api_key, "gsk_ui_key")
            self.assertEqual(reloaded.gemini_api_key, "AIza_ui_key")

            # 6. Fecha e reabre SettingsWindow para verificar recarregamento nos campos
            sw.destroy()
            ui.update()

            ui.open_settings()
            ui.update()
            sw2 = ui.settings_window
            self.assertEqual(sw2.groq_key_entry.get(), "gsk_ui_key")
            self.assertEqual(sw2.gemini_key_entry.get(), "AIza_ui_key")
            sw2.destroy()
            ui.update()
        finally:
            ui.destroy()


if __name__ == "__main__":
    unittest.main()
