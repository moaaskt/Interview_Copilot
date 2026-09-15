import unittest
from unittest.mock import MagicMock
from src.ui import CopilotUI


class TestCopilotUIShortcuts(unittest.TestCase):
    def setUp(self):
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

    def test_button_labels_contain_shortcuts(self):
        self.assertIn("[Ctrl+Espaço]", self.app.record_btn.cget("text"))
        self.assertIn("[Ctrl+Enter]", self.app.respond_btn.cget("text"))
        self.assertIn("[Esc]", self.app.clear_btn.cget("text"))

    def test_recording_state_toggles_button_text(self):
        self.app.set_recording_state(True)
        self.assertIn("⏹ Parar [Ctrl+Espaço]", self.app.record_btn.cget("text"))

        self.app.set_recording_state(False)
        self.assertIn("🎙 Gravar [Ctrl+Espaço]", self.app.record_btn.cget("text"))

    def test_global_bindings_registered(self):
        bound_events = self.app.bind_all()
        self.assertTrue(any("space" in b for b in bound_events))
        self.assertTrue(any("Return" in b for b in bound_events))
        self.assertTrue(any("Escape" in b for b in bound_events))


if __name__ == "__main__":
    unittest.main()
