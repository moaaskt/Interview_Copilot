import threading
import time
import unittest

from src.audio_buffer import AudioCaptureState, PreRollAudioBuffer


class TestPreRollAudioBuffer(unittest.TestCase):
    """
    Testes unitários de Nível 1 para o PreRollAudioBuffer e AudioCaptureState.
    """

    def setUp(self):
        # 16kHz, mono, 16-bit (2 bytes/amostra), chunk_duration = 0.1s (1600 frames = 3200 bytes)
        self.sample_rate = 16000
        self.chunk_frames = 1600
        self.chunk_size_bytes = 3200
        self.chunk_duration = 0.1

    def _make_dummy_chunk(self, identifier: int) -> bytes:
        """Cria um chunk PCM sintético de 3200 bytes com cabeçalho identificador."""
        header = f"CHUNK_{identifier:05d}:".encode("utf-8")
        payload = b"\x00" * (self.chunk_size_bytes - len(header))
        return header + payload

    def test_effective_duration_and_tolerance_5s(self):
        """Valida que duration_seconds=5.0 retém 50 chunks (5.0s) descartando os mais antigos."""
        buffer = PreRollAudioBuffer(
            duration_seconds=5.0,
            sample_rate=self.sample_rate,
            chunk_frames=self.chunk_frames,
        )

        # Inserir 80 chunks consecutivos
        for i in range(80):
            buffer.push(self._make_dummy_chunk(i))

        # Deve conter exatamente 50 chunks (5.0s / 0.1s)
        self.assertEqual(buffer.current_chunks_count, 50)
        self.assertAlmostEqual(buffer.current_duration_seconds, 5.0, places=1)

        # Os chunks armazenados devem ser exatamente do índice 30 ao 79 (FIFO)
        chunks = buffer.get_all()
        self.assertEqual(len(chunks), 50)
        self.assertTrue(chunks[0].startswith(b"CHUNK_00030:"))
        self.assertTrue(chunks[-1].startswith(b"CHUNK_00079:"))

    def test_effective_duration_and_tolerance_10s(self):
        """Valida que duration_seconds=10.0 retém 100 chunks (~10.0s)."""
        buffer = PreRollAudioBuffer(
            duration_seconds=10.0,
            sample_rate=self.sample_rate,
            chunk_frames=self.chunk_frames,
        )

        for i in range(120):
            buffer.push(self._make_dummy_chunk(i))

        self.assertEqual(buffer.current_chunks_count, 100)
        self.assertAlmostEqual(buffer.current_duration_seconds, 10.0, places=1)

        chunks = buffer.get_all()
        self.assertEqual(len(chunks), 100)
        self.assertTrue(chunks[0].startswith(b"CHUNK_00020:"))
        self.assertTrue(chunks[-1].startswith(b"CHUNK_00119:"))

    def test_drain_all_atomicity(self):
        """Valida que drain_all() extrai todos os chunks e esvazia o buffer atomicamente."""
        buffer = PreRollAudioBuffer(duration_seconds=5.0, sample_rate=self.sample_rate, chunk_frames=self.chunk_frames)

        c1 = self._make_dummy_chunk(1)
        c2 = self._make_dummy_chunk(2)
        c3 = self._make_dummy_chunk(3)

        buffer.push(c1)
        buffer.push(c2)
        buffer.push(c3)

        self.assertEqual(buffer.current_chunks_count, 3)

        drained = buffer.drain_all()
        self.assertEqual(drained, [c1, c2, c3])
        self.assertEqual(buffer.current_chunks_count, 0)
        self.assertEqual(buffer.get_all(), [])
        self.assertEqual(buffer.drain_all(), [])

    def test_continuity_after_drain(self):
        """Valida que novos chunks continuam sendo aceitos imediatamente após um drain_all()."""
        buffer = PreRollAudioBuffer(duration_seconds=5.0, sample_rate=self.sample_rate, chunk_frames=self.chunk_frames)

        c1 = self._make_dummy_chunk(1)
        c2 = self._make_dummy_chunk(2)
        buffer.push(c1)
        buffer.push(c2)

        drained1 = buffer.drain_all()
        self.assertEqual(drained1, [c1, c2])

        c3 = self._make_dummy_chunk(3)
        c4 = self._make_dummy_chunk(4)
        buffer.push(c3)
        buffer.push(c4)

        self.assertEqual(buffer.get_all(), [c3, c4])
        self.assertEqual(buffer.drain_all(), [c3, c4])
        self.assertEqual(buffer.get_all(), [])

    def test_bypass_when_zero_seconds(self):
        """Valida que pre_roll_seconds=0.0 atua como bypass estrito sem armazenar nada."""
        buffer = PreRollAudioBuffer(duration_seconds=0.0, sample_rate=self.sample_rate, chunk_frames=self.chunk_frames)
        self.assertFalse(buffer.enabled)

        c1 = self._make_dummy_chunk(1)
        buffer.push(c1)

        self.assertEqual(buffer.current_chunks_count, 0)
        self.assertEqual(buffer.current_bytes_count, 0)
        self.assertEqual(buffer.get_all(), [])
        self.assertEqual(buffer.drain_all(), [])

    def test_thread_safety_concurrency(self):
        """Valida ausência de race conditions, exceções ou deadlocks com threads simultâneas."""
        buffer = PreRollAudioBuffer(duration_seconds=2.0, sample_rate=self.sample_rate, chunk_frames=self.chunk_frames)
        num_items = 200
        exceptions = []

        def producer():
            try:
                for i in range(num_items):
                    buffer.push(self._make_dummy_chunk(i))
                    time.sleep(0.001)
            except Exception as e:
                exceptions.append(e)

        def consumer():
            try:
                for _ in range(20):
                    _ = buffer.get_all()
                    _ = buffer.drain_all()
                    time.sleep(0.005)
            except Exception as e:
                exceptions.append(e)

        t1 = threading.Thread(target=producer)
        t2 = threading.Thread(target=producer)
        t3 = threading.Thread(target=consumer)

        t1.start()
        t2.start()
        t3.start()

        t1.join()
        t2.join()
        t3.join()

        self.assertEqual(exceptions, [], f"Exceções capturadas durante execução concorrente: {exceptions}")

    def test_memory_footprint_within_bounds(self):
        """Valida que a memória total ocupada por um buffer de 5s não ultrapassa 160KB + 1 chunk."""
        buffer = PreRollAudioBuffer(duration_seconds=5.0, sample_rate=self.sample_rate, chunk_frames=self.chunk_frames)

        for i in range(100):
            buffer.push(self._make_dummy_chunk(i))

        expected_bytes = 50 * self.chunk_size_bytes  # 160.000 bytes
        max_allowed_bytes = 51 * self.chunk_size_bytes  # tolerância de 1 chunk

        self.assertLessEqual(buffer.current_bytes_count, max_allowed_bytes)
        self.assertEqual(buffer.current_bytes_count, expected_bytes)

    def test_audio_capture_state_enum(self):
        """Valida estados da máquina de estados AudioCaptureState."""
        self.assertEqual(AudioCaptureState.PRE_ROLL.name, "PRE_ROLL")
        self.assertEqual(AudioCaptureState.RECORDING.name, "RECORDING")


if __name__ == "__main__":
    unittest.main()
