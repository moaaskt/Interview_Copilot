# Testing Strategy & Diagnostics

## Testing Approach
- Currently, automated unit/integration test suites (e.g., `pytest`) are not formally configured.
- The project relies on an automated hardware/network verification script: `src/diagnostic.py`.

## Diagnostic Suite (`src/diagnostic.py`)
Provides a three-phase diagnostic test without needing GUI interaction:
1. **Audio Capture Test**:
   - Records 5 seconds from the detected PulseAudio/PipeWire sink.
   - Computes RMS dBFS to confirm non-silent audio capture (`avg_db > -60.0 dBFS`).
2. **Batch STT Test**:
   - Sends recorded PCM chunks to Deepgram over WebSocket.
   - Asserts interim and final transcript events are received.
3. **Full Live Streaming Test**:
   - Streams live input to Deepgram for 10 seconds.
   - Asserts real-time transcription throughput.

## Manual Verification
- Launch application via `python3 src/main.py`.
- Check console logs for PulseAudio sink detection and Deepgram WebSocket connection.
- Click "🎙 Gravar Pergunta", speak or play meeting audio, verify interim and final text appearing in the overlay.
- Stop recording or click "⚡ Responder Agora", verify real-time token streaming from Groq into the lower textbox.
