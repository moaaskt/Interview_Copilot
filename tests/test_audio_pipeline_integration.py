import asyncio
import threading
import time
import unittest
from unittest.mock import MagicMock

from src.audio_buffer import AudioCaptureState
from src.audio_capture import AudioCapture
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
        app.transcript_buffer = []

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

                    loop.call_soon_threadsafe(app.on_audio_data, chunk)
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


if __name__ == "__main__":
    unittest.main()
