import unittest
from unittest.mock import MagicMock, patch
from src.ui import CopilotUI


class TestCopilotUIUXOverlay(unittest.TestCase):
    def setUp(self):
        self.app = CopilotUI()
        self.app.update()

    def tearDown(self):
        try:
            self.app.destroy()
        except Exception:
            pass

    def test_cycle_opacity(self):
        # Níveis configurados: [0.92, 1.0, 0.75, 0.85]
        # Padrão inicial é 0.92
        self.assertIn("92%", self.app.opacity_btn.cget("text"))

        # Primeiro ciclo -> 1.0 (100%)
        res = self.app.cycle_opacity()
        self.assertEqual(res, "break")
        self.assertIn("100%", self.app.opacity_btn.cget("text"))

        # Segundo ciclo -> 0.75 (75%)
        self.app.cycle_opacity()
        self.assertIn("75%", self.app.opacity_btn.cget("text"))

        # Terceiro ciclo -> 0.85 (85%)
        self.app.cycle_opacity()
        self.assertIn("85%", self.app.opacity_btn.cget("text"))

        # Quarto ciclo -> volta para 0.92 (92%)
        self.app.cycle_opacity()
        self.assertIn("92%", self.app.opacity_btn.cget("text"))

    def test_cycle_window_position(self):
        # Testa ciclo completo entre os 4 presets sem erros de geometria
        presets = ["top-center", "top-right", "top-left", "center"]
        for _ in range(len(presets)):
            res = self.app.cycle_window_position()
            self.assertEqual(res, "break")
            # Verifica que a geometria foi atualizada
            geom = self.app.geometry()
            self.assertTrue("520x390" in geom)

    def test_shortcuts_f8_and_f10_bound(self):
        bound_events = self.app.bind_all()
        self.assertTrue(any("F8" in b for b in bound_events))
        self.assertTrue(any("F10" in b for b in bound_events))

    def test_adaptive_auto_scroll_following_tokens(self):
        # Mock do método see
        self.app.ai_textbox.see = MagicMock()

        # Inserindo texto quando o widget está vazio / no fim
        self.app.append_ai_token("Primeira linha de resposta da IA.")
        self.app.ai_textbox.see.assert_called_with("end")

    def test_adaptive_auto_scroll_pauses_when_scrolled_up(self):
        # Simula que o usuário rolou manualmente para o topo (bottom = 0.40)
        self.app.ai_textbox._textbox.yview = MagicMock(return_value=(0.0, 0.40))
        self.app.ai_textbox.see = MagicMock()

        self.app.append_ai_token("Novo token que não deve forçar scroll")
        self.app.ai_textbox.see.assert_not_called()

    def test_drag_smooth_delta_calculation(self):
        self.app.winfo_x = MagicMock(return_value=1000)
        self.app.winfo_y = MagicMock(return_value=500)

        mock_event_click = MagicMock(x_root=1050, y_root=520)
        res_start = self.app._start_drag(mock_event_click)
        self.assertEqual(res_start, "break")
        self.assertEqual(self.app._drag_offset_x, 50)
        self.assertEqual(self.app._drag_offset_y, 20)

        # Simula movimento do ponteiro para (1090, 540) -> nova pos esperada (1040, 520)
        mock_event_drag = MagicMock(x_root=1090, y_root=540)
        self.app.geometry = MagicMock()
        res_drag = self.app._drag(mock_event_drag)
        self.assertEqual(res_drag, "break")
        self.assertEqual(self.app._drag_target_x, 1040)
        self.assertEqual(self.app._drag_target_y, 520)

        # Executa apply_drag
        self.app._apply_drag()
        self.app.geometry.assert_called_with("+1040+520")

        # Teste stop_drag
        res_stop = self.app._stop_drag()
        self.assertEqual(res_stop, "break")
        self.assertIsNone(self.app._drag_offset_x)
        self.assertIsNone(self.app._drag_offset_y)
        self.assertFalse(self.app._drag_scheduled)

    def test_multi_monitor_bounds_detection(self):
        mx, my, mw, mh = self.app._get_active_monitor()
        self.assertGreater(mw, 0)
        self.assertGreater(mh, 0)
        self.assertGreaterEqual(mx, 0)
        self.assertGreaterEqual(my, 0)

    def test_cycle_opacity_changes_visual_styles(self):
        initial_bg = self.app.main_frame.cget("fg_color")
        self.app.cycle_opacity()
        new_bg = self.app.main_frame.cget("fg_color")
        # Deve ter alterado a cor de fundo visualmente
        self.assertNotEqual(initial_bg, new_bg)


if __name__ == "__main__":
    unittest.main()

