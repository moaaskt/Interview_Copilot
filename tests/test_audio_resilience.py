import unittest
from unittest.mock import MagicMock
import numpy as np

from src.ui import CopilotUI
from src.transcriber import Transcriber
from src.main import CopilotApp


class TestAudioResilience(unittest.TestCase):
    def setUp(self):
        self.app_ui = CopilotUI()
        self.app_ui.update()

    def tearDown(self):
        try:
            self.app_ui.destroy()
        except Exception:
            pass

    def test_audio_meter_silence(self):
        self.app_ui.update_audio_level(50.0)
        self.assertEqual(self.app_ui.audio_meter_label.cget("text"), "🎙 ···")
        self.assertEqual(self.app_ui.audio_meter_label.cget("fg"), "#585B70")

    def test_audio_meter_low(self):
        self.app_ui.update_audio_level(350.0)
        self.assertEqual(self.app_ui.audio_meter_label.cget("text"), "🎙 ▃··")
        self.assertEqual(self.app_ui.audio_meter_label.cget("fg"), "#94E2D5")

    def test_audio_meter_medium(self):
        self.app_ui.update_audio_level(1200.0)
        self.assertEqual(self.app_ui.audio_meter_label.cget("text"), "🎙 ▃▅·")
        self.assertEqual(self.app_ui.audio_meter_label.cget("fg"), "#A6E3A1")

    def test_audio_meter_high(self):
        self.app_ui.update_audio_level(4000.0)
        self.assertEqual(self.app_ui.audio_meter_label.cget("text"), "🎙 ▃▅█")
        self.assertEqual(self.app_ui.audio_meter_label.cget("fg"), "#89B4FA")

    def test_rms_calculation_synthetic_pcm(self):
        # 1600 amostras (100ms a 16kHz)
        amplitude = 2000
        samples = np.full(1600, amplitude, dtype=np.int16)
        raw_pcm = samples.tobytes()

        # Simula lógica de main.py
        decoded = np.frombuffer(raw_pcm, dtype=np.int16)
        rms = float(np.sqrt(np.mean(decoded.astype(np.float32) ** 2)))
        self.assertAlmostEqual(rms, 2000.0, places=1)

    def test_transcriber_handle_disconnect_triggers_callback(self):
        conn_mock = MagicMock()
        transcriber = Transcriber(
            api_key="mock_key",
            on_interim_transcript=MagicMock(),
            on_final_transcript=MagicMock(),
            on_connection_change=conn_mock,
        )

        transcriber.is_connected = True
        transcriber._handle_disconnect()

        self.assertFalse(transcriber.is_connected)
        conn_mock.assert_called_once_with(False)

    def test_main_on_connection_change(self):
        # Simula CopilotApp sem inicializar áudio real
        app = object.__new__(CopilotApp)
        app.loop = None
        app.ui = self.app_ui

        app.on_connection_change(False)
        self.assertIn("Reconectando", self.app_ui.status_badge.cget("text"))

        app.on_connection_change(True)
        self.assertIn("Pronto", self.app_ui.status_badge.cget("text"))


if __name__ == "__main__":
    unittest.main()
