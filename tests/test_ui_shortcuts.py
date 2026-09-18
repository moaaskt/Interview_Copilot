import unittest
from unittest.mock import MagicMock
from src.ui import CopilotUI


class TestCopilotUIShortcuts(unittest.TestCase):
    def setUp(self):
        self.start_mock = MagicMock()
        self.stop_mock = MagicMock()
        self.toggle_mock = MagicMock()
        self.respond_mock = MagicMock()
        self.clear_mock = MagicMock()

        mock_cfg = MagicMock()
        mock_cfg.hotkeys = {
            "toggle_recording": "<Control-space>",
            "toggle_recording_alt": "<F9>",
            "respond_now": "<Control-Return>",
            "clear_session": "<Escape>",
            "clear_session_alt": "<Control-BackSpace>",
            "cycle_position": "<F8>",
            "cycle_opacity": "<F10>",
            "open_settings": "<F12>",
        }
        mock_cfg.quick_questions = []

        self.app = CopilotUI(
            on_start_recording=self.start_mock,
            on_stop_recording=self.stop_mock,
            on_toggle_recording=self.toggle_mock,
            on_respond_now=self.respond_mock,
            on_clear=self.clear_mock,
            config_manager=mock_cfg,
        )

    def tearDown(self):
        try:
            self.app.destroy()
        except Exception:
            pass

    def test_handler_start_and_stop_recording_returns_break(self):
        result_start = self.app._handle_start_recording("mock_event")
        self.assertEqual(result_start, "break")
        self.start_mock.assert_called_once()

        result_stop = self.app._handle_stop_recording("mock_event")
        self.assertEqual(result_stop, "break")
        self.stop_mock.assert_called_once()

    def test_handler_toggle_recording_returns_break(self):
        result = self.app._handle_toggle_recording("mock_event")
        self.assertEqual(result, "break")
        self.toggle_mock.assert_called_once()

    def test_handler_respond_now_returns_break(self):
        result = self.app._handle_respond_now("mock_event")
        self.assertEqual(result, "break")
        self.respond_mock.assert_called_once()

    def test_handler_clear_returns_break(self):
        result = self.app._handle_clear("mock_event")
        self.assertEqual(result, "break")
        self.clear_mock.assert_called_once()

    def test_button_labels_contain_shortcuts_and_4_buttons_exist(self):
        self.assertIn("[Ctrl+Espaço]", self.app.record_btn.cget("text"))
        self.assertEqual(self.app.stop_btn.cget("text"), "⏹ Parar")
        self.assertIn("[Ctrl+Enter]", self.app.respond_btn.cget("text"))
        self.assertIn("[Esc]", self.app.clear_btn.cget("text"))

    def test_recording_state_updates_visual_styles_of_buttons(self):
        self.app.set_recording_state(True)
        self.assertIn("🎙 Gravando [Ctrl+Espaço]", self.app.record_btn.cget("text"))
        self.assertEqual(self.app.stop_btn.cget("fg_color"), "#F38BA8")

        self.app.set_recording_state(False)
        self.assertIn("🎙 Gravar [Ctrl+Espaço]", self.app.record_btn.cget("text"))
        self.assertEqual(self.app.stop_btn.cget("fg_color"), "#313244")

    def test_global_bindings_registered(self):
        bound_events = self.app.bind_all()
        self.assertTrue(any("space" in b for b in bound_events))
        self.assertTrue(any("Return" in b for b in bound_events))
        self.assertTrue(any("Escape" in b for b in bound_events))

    def test_custom_configured_hotkeys_reflected_in_button_labels(self):
        mock_custom_cfg = MagicMock()
        mock_custom_cfg.hotkeys = {
            "toggle_recording": "<Alt-Shift-F7>",
            "respond_now": "<Alt-Shift-F8>",
            "clear_session": "<Alt-Shift-BackSpace>",
        }
        mock_custom_cfg.quick_questions = []

        custom_ui = CopilotUI(config_manager=mock_custom_cfg)
        try:
            self.assertIn("[Alt+Shift+F7]", custom_ui.record_btn.cget("text"))
            self.assertEqual(custom_ui.stop_btn.cget("text"), "⏹ Parar")
            self.assertIn("[Alt+Shift+F8]", custom_ui.respond_btn.cget("text"))
            self.assertIn("[Alt+Shift+Backspace]", custom_ui.clear_btn.cget("text"))

            # Alternar gravação preserva o atalho customizado
            custom_ui.set_recording_state(True)
            self.assertIn("🎙 Gravando [Alt+Shift+F7]", custom_ui.record_btn.cget("text"))
            custom_ui.set_recording_state(False)
            self.assertIn("🎙 Gravar [Alt+Shift+F7]", custom_ui.record_btn.cget("text"))
        finally:
            try:
                custom_ui.destroy()
            except Exception:
                pass

    def test_apply_hotkeys_updates_hud_button_labels_dynamically(self):
        new_hotkeys = {
            "toggle_recording": "<Control-F1>",
            "respond_now": "<Control-F2>",
            "clear_session": "<Control-F3>",
        }
        self.app.apply_hotkeys(new_hotkeys)

        self.assertIn("[Ctrl+F1]", self.app.record_btn.cget("text"))
        self.assertEqual(self.app.stop_btn.cget("text"), "⏹ Parar")
        self.assertIn("[Ctrl+F2]", self.app.respond_btn.cget("text"))
        self.assertIn("[Ctrl+F3]", self.app.clear_btn.cget("text"))

        self.app.set_recording_state(True)
        self.assertIn("🎙 Gravando [Ctrl+F1]", self.app.record_btn.cget("text"))


if __name__ == "__main__":
    unittest.main()
