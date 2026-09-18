import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
from pathlib import Path

from src.config_manager import ConfigManager, DEFAULT_TECH_KEYWORDS
from src.transcriber import Transcriber


class TestTranscriberKeywords(unittest.TestCase):
    """
    Suíte de testes unitários para o vocabulário técnico da Deepgram,
    normalização de keywords e calibração de LiveOptions (Fase 9).
    """

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.temp_file.close()
        self.config_manager = ConfigManager(config_path=self.temp_file.name)

    def tearDown(self):
        try:
            Path(self.temp_file.name).unlink(missing_ok=True)
        except Exception:
            pass

    def test_default_keywords_construction(self):
        """Valida que a lista padrão contém os termos essenciais de desenvolvimento."""
        combined = self.config_manager.get_combined_keywords()
        self.assertTrue(len(combined) >= 35)
        self.assertIn("PHP:2", combined)
        self.assertIn("CodeIgniter:3", combined)
        self.assertIn("Docker:2", combined)
        self.assertIn("PostgreSQL:2", combined)
        self.assertIn("WhatsMiau:3", combined)

    def test_custom_keywords_appended(self):
        """Valida que novos termos customizados são anexados ao final da lista."""
        self.config_manager.set("transcription", "custom_keywords", ["Kubeflow:2", "Solidity:3"])
        combined = self.config_manager.get_combined_keywords()

        self.assertIn("Kubeflow:2", combined)
        self.assertIn("Solidity:3", combined)
        # Deve estar após os termos padrão
        idx_docker = [i for i, k in enumerate(combined) if "Docker" in k][0]
        idx_solidity = combined.index("Solidity:3")
        self.assertGreater(idx_solidity, idx_docker)

    def test_custom_keyword_overrides_default_weight(self):
        """Valida que uma custom keyword sobrescreve o termo padrão correspondente."""
        # Docker padrão é "Docker:2" -> sobrescreve para "Docker:5"
        self.config_manager.set("transcription", "custom_keywords", ["Docker:5"])
        combined = self.config_manager.get_combined_keywords()

        self.assertIn("Docker:5", combined)
        self.assertNotIn("Docker:2", combined)

    def test_whitespace_and_empty_string_sanitization(self):
        """Valida que espaços extras são removidos e strings vazias/nulas são descartadas."""
        self.config_manager.set("transcription", "custom_keywords", [
            "   ",
            "",
            "   Rust:3   ",
            None,
            "  Elixir  "
        ])
        combined = self.config_manager.get_combined_keywords()

        self.assertIn("Rust:3", combined)
        self.assertIn("Elixir", combined)
        self.assertNotIn("", combined)
        self.assertNotIn("   ", combined)

    def test_weighted_and_unweighted_terms(self):
        """Valida que termos com peso e termos simples sem peso são suportados."""
        self.config_manager.set("transcription", "custom_keywords", ["FastAPI", "GraphQL:2"])
        combined = self.config_manager.get_combined_keywords()

        self.assertIn("FastAPI", combined)
        self.assertIn("GraphQL:2", combined)

    def test_distinct_compound_terms_coexist(self):
        """Valida que 'CodeIgniter' e 'CodeIgniter 4' coexistem sem colisão."""
        combined = self.config_manager.get_combined_keywords()
        ci_terms = [k for k in combined if "CodeIgniter" in k]
        self.assertTrue(any("CodeIgniter:3" in k for k in ci_terms))
        self.assertTrue(any("CodeIgniter 4:3" in k for k in ci_terms))

    def test_absent_or_empty_custom_keywords_returns_defaults(self):
        """Valida que com custom_keywords vazio ou None, a lista padrão permanece intacta."""
        self.config_manager.set("transcription", "custom_keywords", [])
        combined = self.config_manager.get_combined_keywords()
        self.assertEqual(len(combined), len(DEFAULT_TECH_KEYWORDS))

    def test_config_manager_transcription_properties(self):
        """Valida getters e defaults de transcrição no ConfigManager."""
        self.assertEqual(self.config_manager.transcription_language, "pt-BR")
        self.assertEqual(self.config_manager.transcription_endpointing_ms, 350)
        self.assertEqual(self.config_manager.custom_keywords, [])

    @patch("src.transcriber.DeepgramClient")
    def test_live_options_parameters_received(self, mock_dg_client_class):
        """Valida que LiveOptions é montado com keywords, punctuate=True, smart_format=True e endpointing."""
        mock_client = MagicMock()
        mock_conn = MagicMock()
        mock_conn.start.return_value = True
        mock_client.listen.live.v.return_value = mock_conn
        mock_dg_client_class.return_value = mock_client

        keywords = ["Docker:2", "CodeIgniter:3", "Python:2"]
        transcriber = Transcriber(
            api_key="mock_key",
            on_interim_transcript=MagicMock(),
            on_final_transcript=MagicMock(),
            language="pt-BR",
            keywords=keywords,
            endpointing=350,
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(transcriber.start())
        finally:
            loop.close()

        mock_conn.start.assert_called_once()
        options_sent = mock_conn.start.call_args[0][0]

        self.assertEqual(options_sent.model, "nova-2")
        self.assertEqual(options_sent.language, "pt-BR")
        self.assertEqual(options_sent.smart_format, True)
        self.assertEqual(options_sent.punctuate, True)
        self.assertEqual(options_sent.endpointing, 350)
        self.assertEqual(options_sent.keywords, keywords)

    @patch("src.transcriber.DeepgramClient")
    def test_configurable_endpointing_ms(self, mock_dg_client_class):
        """Valida que endpointing customizado (ex: 500ms) é repassado ao LiveOptions."""
        mock_client = MagicMock()
        mock_conn = MagicMock()
        mock_conn.start.return_value = True
        mock_client.listen.live.v.return_value = mock_conn
        mock_dg_client_class.return_value = mock_client

        transcriber = Transcriber(
            api_key="mock_key",
            on_interim_transcript=MagicMock(),
            on_final_transcript=MagicMock(),
            endpointing=500,
        )

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(transcriber.start())
        finally:
            loop.close()

        options_sent = mock_conn.start.call_args[0][0]
        self.assertEqual(options_sent.endpointing, 500)


if __name__ == "__main__":
    unittest.main()
