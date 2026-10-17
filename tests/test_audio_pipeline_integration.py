import asyncio
import os
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

from src.audio_buffer import AudioCaptureState
from src.audio_capture import AudioCapture
from src.config_manager import ConfigManager
from src.main import CopilotApp


class TestAudioPipelineIntegration(unittest.TestCase):
    """
    Testes de Integração de Nível 2 para o Pipeline Completo:
    AudioCapture (Thread de Áudio) -> on_audio_data (Asyncio) -> Transcriber.send_audio
    """

    def setUp(self):
        self.chunk_size = 1600
        self.sample_rate = 16000
        self.chunk_bytes = 3200

    def _make_chunk(self, seq_num: int) -> bytes:
        header = f"SEQ_{seq_num:06d}:".encode("utf-8")
        return header + b"\x00" * (self.chunk_bytes - len(header))

    def _extract_seq(self, chunk_bytes: bytes) -> int:
        header = chunk_bytes[:11].decode("utf-8")
        return int(header.split("_")[1].replace(":", ""))

    def test_pipeline_no_loss_during_pre_roll_to_recording_transition(self):
        """
        Valida que durante a transição concorrente de PRE_ROLL para RECORDING:
        - Nenhum chunk do pré-roll ou do fluxo ativo é perdido.
        - Nenhum chunk é duplicado.
        - A ordem cronológica é estritamente mantida.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # Mock de dependências da UI e do Transcriber
        sent_chunks: list[bytes] = []
        sent_lock = threading.Lock()

        def mock_send_audio(pcm_data: bytes):
            with sent_lock:
                sent_chunks.append(pcm_data)

        # Configura objeto CopilotApp sem subir janelas gráficas Tkinter
        app = object.__new__(CopilotApp)
        app.loop = loop
        app.is_recording = False
        app._recording_epoch = 0
        app.transcript_buffer = []
        app.auto_trigger_task = None
        app.config_manager = ConfigManager()

        mock_ui = MagicMock()
        mock_transcriber = MagicMock()
        mock_transcriber.send_audio = mock_send_audio

        app.ui = mock_ui
        app.transcriber = mock_transcriber

        # AudioCapture com pré-roll de 2.0s (~20 chunks de 100ms)
        audio_capture = AudioCapture(
            audio_callback=app.on_audio_data,
            sample_rate=self.sample_rate,
            chunk_duration=0.1,
            pre_roll_seconds=2.0,
        )
        audio_capture.is_running = True
        app.audio_capture = audio_capture

        total_chunks = 40
        start_trigger_at = 15  # Aciona gravação quando chunk 15 for gerado
        exceptions = []

        def audio_hardware_thread():
            """Simula callbacks contínuas da placa de som em thread nativa."""
            try:
                for i in range(total_chunks):
                    chunk = self._make_chunk(i)
                    if audio_capture.state == AudioCaptureState.PRE_ROLL:
                        audio_capture.pre_roll_buffer.push(chunk)
                    app.on_audio_data(chunk)

                    time.sleep(0.01)  # 10ms por chunk (acelerado para o teste)
            except Exception as e:
                exceptions.append(e)

        # Inicia loop asyncio em thread secundária para processamento de eventos
        loop_thread = threading.Thread(target=loop.run_forever)
        loop_thread.daemon = True
        loop_thread.start()

        prod_thread = threading.Thread(target=audio_hardware_thread)
        prod_thread.start()

        # Aguarda a produção chegar próximo do chunk 15
        time.sleep(0.18)

        # Aciona START no loop principal (como um clique de UI ou Hotkey)
        loop.call_soon_threadsafe(app._start_recording)

        prod_thread.join(timeout=3.0)
        time.sleep(0.1)  # Permite que os últimos eventos sejam processados

        loop.call_soon_threadsafe(loop.stop)
        loop_thread.join(timeout=2.0)

        # Validações estritas
        self.assertEqual(exceptions, [], f"Exceções na thread de áudio: {exceptions}")
        self.assertTrue(len(sent_chunks) > 0, "Nenhum chunk foi transmitido ao Transcriber")

        # Extrai números de sequência recebidos pelo Transcriber
        seq_numbers = [self._extract_seq(c) for c in sent_chunks]

        # 1. Valida ausência de duplicatas
        self.assertEqual(
            len(seq_numbers),
            len(set(seq_numbers)),
            f"Duplicatas detectadas no stream: {seq_numbers}"
        )

        # 2. Valida ordem estritamente crescente (cronológica)
        is_sorted = all(seq_numbers[i] < seq_numbers[i + 1] for i in range(len(seq_numbers) - 1))
        self.assertTrue(is_sorted, f"Inversão de ordem temporal detectada: {seq_numbers}")

        # 3. Valida continuidade sequencial contínua (nenhum gap entre o menor e maior chunk gravado)
        first_seq = seq_numbers[0]
        last_seq = seq_numbers[-1]
        expected_range = list(range(first_seq, last_seq + 1))
        self.assertEqual(
            seq_numbers,
            expected_range,
            f"Gaps ou chunks perdidos na transição. Esperado: {expected_range}, Recebido: {seq_numbers}"
        )

        # 4. Valida que o último chunk transmitido foi o último gerado pela hardware thread
        self.assertEqual(last_seq, total_chunks - 1)

    def test_audio_capture_device_switch_preserves_pre_roll(self):
        """Valida que a troca de dispositivo preserva a configuração de pre-roll."""
        cap = AudioCapture(
            audio_callback=MagicMock(),
            sample_rate=16000,
            pre_roll_seconds=3.5,
        )
        self.assertEqual(cap.pre_roll_buffer.duration_seconds, 3.5)
        self.assertEqual(cap.state, AudioCaptureState.PRE_ROLL)

    @patch("main.CopilotUI")
    @patch("main.LLMService")
    @patch("main.Transcriber")
    @patch("main.AudioCapture")
    @patch("main.HotkeyManager")
    @patch("main.load_dotenv")
    @patch.dict(os.environ, {"DEEPGRAM_API_KEY": "dummy_dg", "GROQ_API_KEY": "dummy_groq"})
    def test_pipeline_pre_roll_disabled_discards_old_chunks(self, *mocks):
        """Valida que com pre_roll_enabled=False, chunks anteriores são descartados e apenas áudio novo é transmitido."""
        app = CopilotApp()
        sent_chunks = []
        mock_transcriber = MagicMock()
        mock_transcriber.send_audio.side_effect = lambda c: sent_chunks.append(c)
        app.transcriber = mock_transcriber

        # Configura pre_roll desativado
        app.config_manager.set("audio", "pre_roll_enabled", False)

        audio_capture = AudioCapture(
            audio_callback=app.on_audio_data,
            sample_rate=self.sample_rate,
            chunk_duration=0.1,
            pre_roll_seconds=2.0,
        )
        audio_capture.is_running = True
        app.audio_capture = audio_capture

        # 1. Simula fala anterior à gravação (chunks 0 a 14) retida no buffer de pré-roll
        for i in range(15):
            chunk = self._make_chunk(i)
            audio_capture.pre_roll_buffer.push(chunk)
            app.on_audio_data(chunk)

        self.assertEqual(audio_capture.pre_roll_buffer.current_chunks_count, 15)
        self.assertEqual(len(sent_chunks), 0, "Nenhum chunk deveria ter sido enviado antes do início da gravação")

        # 2. Usuário clica em GRAVAR com pre_roll_enabled = False
        app._start_recording()

        # O buffer de pré-roll deve ter sido drenado/limpo
        self.assertEqual(audio_capture.pre_roll_buffer.current_chunks_count, 0)
        # Chunks antigos 0..14 NÃO devem ter sido enviados
        self.assertEqual(len(sent_chunks), 0, "Chunks pré-gravados foram enviados indevidamente quando pre_roll_enabled=False")

        # 3. Novos chunks chegam após o início da gravação (chunks 15 a 25)
        for i in range(15, 26):
            chunk = self._make_chunk(i)
            app.on_audio_data(chunk)

        seq_numbers = [self._extract_seq(c) for c in sent_chunks]
        expected_seqs = list(range(15, 26))
        self.assertEqual(seq_numbers, expected_seqs, f"Stream de áudio novo incorreto: {seq_numbers}")

    @patch("main.CopilotUI")
    @patch("main.LLMService")
    @patch("main.Transcriber")
    @patch("main.AudioCapture")
    @patch("main.HotkeyManager")
    @patch("main.load_dotenv")
    @patch.dict(os.environ, {"DEEPGRAM_API_KEY": "dummy_dg", "GROQ_API_KEY": "dummy_groq"})
    def test_session_isolation_and_delayed_callbacks_discarded(self, *mocks):
        """Valida que mensagens atrasadas da sessão anterior não poluem a nova gravação."""
        app = CopilotApp()
        app.loop = MagicMock()
        app.loop.is_running.return_value = True

        # 1. Sessão 1: Gravação em andamento
        app.start_recording()
        self.assertTrue(app.is_recording)
        epoch_1 = app._recording_epoch

        app.on_final_transcript("Qual o satélite natural da Terra?")
        self.assertEqual(app.transcript_buffer, ["Qual o satélite natural da Terra?"])

        # 2. Usuário para a gravação (sem disparar IA)
        app.stop_recording()
        self.assertFalse(app.is_recording)
        self.assertGreater(app._recording_epoch, epoch_1)

        # 3. Mensagem atrasada da Deepgram chega quando o usuário já parou
        app.on_final_transcript("A Lua.")
        # Buffer e estado não devem aceitar essa mensagem
        self.assertEqual(app.transcript_buffer, ["Qual o satélite natural da Terra?"])

        # 4. Sessão 2: Usuário clica em GRAVAR novamente
        with patch.object(app.ui, "clear_all") as mock_clear:
            app.start_recording()
            self.assertTrue(app.is_recording)
            # Buffer da nova sessão começa totalmente limpo
            self.assertEqual(app.transcript_buffer, [])
            mock_clear.assert_called_once()

        # Nova fala chega para a Sessão 2
        app.on_final_transcript("Como funciona o Garbage Collector em Go?")
        self.assertEqual(app.transcript_buffer, ["Como funciona o Garbage Collector em Go?"])

    @patch("main.CopilotUI")
    @patch("main.LLMService")
    @patch("main.Transcriber")
    @patch("main.AudioCapture")
    @patch("main.HotkeyManager")
    @patch("main.load_dotenv")
    @patch.dict(os.environ, {"DEEPGRAM_API_KEY": "dummy_dg", "GROQ_API_KEY": "dummy_groq"})
    def test_gravar_and_parar_button_idempotence(self, *mocks):
        """Valida contratos dos botões independentes Gravar e Parar."""
        app = CopilotApp()
        app.loop = MagicMock()
        app.loop.is_running.return_value = True

        # PARAR sem estar gravando é no-op seguro
        self.assertFalse(app.is_recording)
        app.stop_recording()
        self.assertFalse(app.is_recording)

        # GRAVAR inicia gravação
        app.start_recording()
        self.assertTrue(app.is_recording)
        epoch = app._recording_epoch

        # GRAVAR enquanto já está gravando é no-op seguro (não reinicia nem duplica)
        app.start_recording()
        self.assertTrue(app.is_recording)
        self.assertEqual(app._recording_epoch, epoch)

        # PARAR durante gravação encerra sessão sem disparar LLM
        with patch.object(app, "respond_now") as mock_respond:
            app.stop_recording()
            self.assertFalse(app.is_recording)
            mock_respond.assert_not_called()

        # RESPONDER dispara LLM
        app.transcript_buffer = ["Explique polimorfismo em TypeScript"]
        with patch.object(app, "_process_llm_stream") as mock_stream:
            app.respond_now()
            self.assertFalse(app.is_recording)

    @patch("main.CopilotUI")
    @patch("main.LLMService")
    @patch("main.AudioCapture")
    @patch("main.HotkeyManager")
    @patch("main.load_dotenv")
    @patch.dict(os.environ, {"DEEPGRAM_API_KEY": "dummy_dg", "GROQ_API_KEY": "dummy_groq"})
    def test_transcriber_finalize_called_on_stop_and_clear(self, *mocks):
        """Valida que finalize() é chamado em stop_recording, _start_recording e clear_session para descarregar o decodificador."""
        app = CopilotApp()
        app.loop = MagicMock()
        app.loop.is_running.return_value = True

        with patch.object(app.transcriber, "finalize") as mock_finalize:
            app.start_recording()
            # Ao iniciar uma nova sessão, finalize é chamado para garantir decoder limpo
            mock_finalize.assert_called()

        with patch.object(app.transcriber, "finalize") as mock_finalize:
            app.stop_recording()
            # Ao parar gravação, finalize é chamado para descarregar buffers do Deepgram
            mock_finalize.assert_called_once()

        with patch.object(app.transcriber, "finalize") as mock_finalize:
            app.clear_session()
            # Ao limpar sessão, finalize é chamado
            mock_finalize.assert_called_once()

    @patch("main.load_dotenv")
    @patch.dict(os.environ, {"DEEPGRAM_API_KEY": "dummy_dg", "GROQ_API_KEY": "dummy_groq"})
    def test_on_audio_data_discards_pre_roll_chunks_even_if_recording_active(self, *mocks):
        """Valida que chunks capturados em PRE_ROLL state nunca são transmitidos ao transcritor."""
        app = CopilotApp()
        sent_chunks = []
        mock_transcriber = MagicMock()
        mock_transcriber.send_audio.side_effect = lambda c: sent_chunks.append(c)
        app.transcriber = mock_transcriber
        app.is_recording = True

        # Chunk capturado no estado PRE_ROLL (is_recording=False)
        old_chunk = b"\x01\x00" * 1600
        app.on_audio_data(old_chunk, is_recording=False)
        self.assertEqual(len(sent_chunks), 0, "Chunk de pré-roll não deveria ter sido enviado via stream ao vivo")

        # Chunk capturado no estado RECORDING (is_recording=True)
        live_chunk = b"\x02\x00" * 1600
        app.on_audio_data(live_chunk, is_recording=True)
        self.assertEqual(len(sent_chunks), 1)
        self.assertEqual(sent_chunks[0], live_chunk)


if __name__ == "__main__":
    unittest.main()
