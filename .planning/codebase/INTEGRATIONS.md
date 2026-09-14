# External Integrations

## Deepgram Live Transcription API
- **Endpoint**: WebSocket `wss://api.deepgram.com/v1/listen`
- **SDK**: `deepgram-sdk` (v3)
- **Model**: `nova-2`
- **Configuration**:
  - `language`: `pt-BR`
  - `smart_format`: `True`
  - `interim_results`: `True`
  - `endpointing`: `300ms`
  - `encoding`: `linear16`
  - `sample_rate`: `16000Hz` mono PCM
  - `keepalive`: `true`
- **Events Handled**:
  - `LiveTranscriptionEvents.Transcript`: Handles interim transcripts (live typing) and final transcripts (completed clauses/sentences).
  - `LiveTranscriptionEvents.Error`: Logs errors and updates state.
  - `LiveTranscriptionEvents.Close`: Handles socket termination.

## Groq Cloud AI (OpenAI Compatible API)
- **Endpoint**: `https://api.groq.com/openai/v1` via `openai.AsyncOpenAI`
- **Authentication**: `GROQ_API_KEY` (with fallback to `OPENAI_API_KEY`)
- **Default Model**: `qwen/qwen3.8-27b` (configurable via `GROQ_MODEL` env var)
- **Inference Mode**: Streaming (`stream=True`) with `temperature=0.3`, `max_tokens=250`
- **System Persona**: Moacir Neto (Full Stack Junior Developer profile, STAR interview method, 3-4 sentence strict concise response rules).

## Operating System Audio Subsystems
- **Linux Audio Server**:
  - PulseAudio / PipeWire integration via `pactl list short sinks` and `pactl get-default-sink`.
  - Automatic resolution of `.monitor` sources for capturing internal output (meetings/browsers).
  - Environmental override support via `PULSE_SOURCE`.
- **Windows Audio Subsystem**:
  - Windows Audio Session API (WASAPI) loopback capture via `pyaudiowpatch`.
