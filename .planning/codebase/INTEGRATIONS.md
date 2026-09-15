---
last_mapped_commit: 2408b9a93be90063fd0b7bab5ee0e721ddd47b9e
last_mapped_at: 2026-09-15
---

# External Integrations & System Interfaces

**Analysis Date:** 2026-09-15

## Deepgram Live Transcription API
- **Protocol & Endpoint**: WebSocket connection to `wss://api.deepgram.com/v1/listen`.
- **SDK**: `deepgram-sdk` (v3 namespace: `client.listen.live.v("1")`).
- **Authentication**: `DEEPGRAM_API_KEY` loaded from `.env`.
- **Live Stream Options**:
  - `model`: `"nova-2"`
  - `language`: `"pt-BR"` (optimizes recognition for Brazilian Portuguese technical terms)
  - `smart_format`: `True` (formats punctuation, capitalization, and numbers automatically)
  - `interim_results`: `True` (streams real-time partial hypotheses before sentences conclude)
  - `endpointing`: `300` (ms of silence before emitting a final sentence boundary)
  - `encoding`: `"linear16"`
  - `channels`: `1` (mono)
  - `sample_rate`: `16000` (16 kHz PCM)
  - `keepalive`: `"true"` (maintains socket liveness during speech pauses)
- **Lifecycle & Events**:
  - `LiveTranscriptionEvents.Transcript`: Dispatches `interim` results to update typing animations and `final` results to append to `transcript_buffer`.
  - `LiveTranscriptionEvents.Error`: Triggers logger and invokes `_handle_disconnect()`.
  - `LiveTranscriptionEvents.Close`: Invokes `_handle_disconnect()` to initiate automatic recovery.
- **Resilience & Auto-Reconnect**:
  - `_reconnect_loop()`: Asynchronous background loop using exponential backoff (starting at 2.0s, scaled by 1.5x up to 10.0s).
  - Status Propagation: `on_connection_change(bool)` triggers visual cues on the HUD (`🔄 Reconectando áudio...` vs `● Pronto`).

## Groq Cloud AI API (OpenAI Compatible)
- **Endpoint**: `https://api.groq.com/openai/v1` via `openai.AsyncOpenAI`.
- **Authentication**: `GROQ_API_KEY` (fallback to `OPENAI_API_KEY`).
- **Model Selection**: Default is `qwen/qwen3.8-27b`, configurable at runtime via `GROQ_MODEL` environment variable.
- **Inference Configuration**:
  - `stream`: `True` (token-by-token generation for immediate UI feedback).
  - `temperature`: `0.3` (deterministic, grounded responses without creative drift).
  - `max_tokens`: `250` (enforces concise, punchy answers suitable for spoken interview delivery).
- **Prompt Engineering & System Persona**:
  - Specialized persona for **Moacir Neto**, Full Stack Junior Developer.
  - Background includes PHP (CodeIgniter 4, Laravel), TypeScript, Next.js, Python, PostgreSQL, MySQL, and production experience at Evento Santo / Doar Digital.
  - Mandates 3 to 4 concise sentences, first-person phrasing, humble and direct delivery, and strict avoidance of fabricated metrics.

## Host Operating System Subsystems

### Linux Audio (PulseAudio / PipeWire)
- **Sink Monitor Discovery**: Automatically determines the active playback sink via `subprocess` calls:
  1. `pactl list short sinks` scanning for `RUNNING` sinks.
  2. Fallback to `pactl get-default-sink`.
  3. Sets `PULSE_SOURCE = <sink_name>.monitor`.
- **Environment Override**: Honors pre-set `PULSE_SOURCE` if defined in environment or `.env`.

### Linux Window Management (X11 / XWayland)
- **True Window Opacity**: Since `attributes("-alpha")` can be ignored or cause artifacts on borderless X11/XWayland windows in certain window managers, `_apply_opacity()` applies `_NET_WM_WINDOW_OPACITY` directly via `xprop` across the window and its parent IDs detected via `xwininfo`.
- **Multi-Monitor Geometry Detection**: Parses `xrandr --current` geometry strings (`(\d+)x(\d+)\+(\d+)\+(\d+)`) to calculate real screen boundaries, preventing windows from anchoring in dead zones between varied display layouts.
- **Input Throttling**: Uses `after_idle(self._apply_drag)` to decouple mouse move events (`event.x_root`) from window movement, eliminating runaway lag and cursor detachment on high-refresh-rate displays.

### Windows Audio & Window Management (WASAPI / Win32)
- **Loopback Capture**: `pyaudiowpatch.PyAudio()` inspects `paWASAPI` host API to locate default output speakers and attaches a loopback stream without requiring third-party virtual cables (VB-Cable).
- **HUD Attributes**: Native Win32 support for `-topmost` and `-alpha` ensures transparent floating overlay behavior above other applications.
