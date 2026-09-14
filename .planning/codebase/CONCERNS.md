# Known Concerns & Technical Debt

## Linux Audio Server Detection
- **Dynamic Sink Switching**: If headphones/speakers are disconnected or switched while running, `PULSE_SOURCE` is currently resolved at startup. A sink reconnect might require application restart.
- **PipeWire / PulseAudio Compatibility**: PulseAudio utilities (`pactl`) are assumed available on Linux; environments without `pactl` fallback to sounddevice default input.

## Wayland / Desktop Environment Quirks
- **Custom Drag Implementation**: `CopilotUI` implements mouse-delta window drag handling because `overrideredirect(True)` bypasses desktop window manager decorations. On pure Wayland sessions (GNOME/KDE), XWayland is relied upon for absolute coordinate tracking.

## API Limits & Network Latency
- **Deepgram Keepalive**: Deepgram WebSockets will terminate if inactive for too long without keepalive packets or PCM frames. Transcriber currently uses `keepalive: "true"`, but reconnection logic on unexpected socket drop could be enhanced.
- **Groq Token Limits**: System prompt contains detailed persona context; responses are limited to 250 tokens (`max_tokens=250`) to keep answers crisp and avoid exceeding rate limits.

## Test Coverage
- Absence of automated unit tests mocking WebSocket connections and audio device inputs. Introducing `pytest` with audio mocks would ensure regressions are caught before manual testing.
