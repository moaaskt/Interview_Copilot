---
last_mapped_commit: 2408b9a93be90063fd0b7bab5ee0e721ddd47b9e
last_mapped_at: 2026-09-15
---

# Directory & File Structure

**Analysis Date:** 2026-09-15

## Repository Layout
```
helpIA/
├── .env                         # Local environment variables & API keys (gitignored)
├── .env.example                 # Template for required environment variables
├── .gitignore                   # Ignore rules (venv, .env, __pycache__, logs)
├── README.md                    # Project overview, installation, and operation guide
├── requirements.txt             # Python dependencies with platform conditional markers
├── .vscode/
│   └── settings.json            # Editor configuration and workspace paths
├── .planning/
│   └── codebase/                # Codebase intelligence documents (7 core maps)
├── src/                         # Core application source code
│   ├── main.py                  # Entry point & asyncio orchestrator (CopilotApp)
│   ├── audio_capture.py         # Multi-platform internal loopback audio capture
│   ├── transcriber.py           # Deepgram WebSocket real-time client & auto-reconnect
│   ├── llm_service.py           # Groq LLM streaming client & interview persona
│   ├── ui.py                    # CustomTkinter floating HUD overlay (CopilotUI)
│   └── diagnostic.py            # Standalone CLI test harness for audio & STT
└── tests/                       # Automated test suite
    ├── test_audio_resilience.py # Tests for audio RMS, VU-meter levels & reconnection
    ├── test_ui_shortcuts.py     # Tests for keyboard shortcuts and button states
    └── test_ui_ux_overlay.py    # Tests for opacity, window presets, dragging & auto-scroll
```

## Detailed File Directory & Responsibilities

### Root Configuration
- **[`.env.example`](file:///c:/Users/Windows%20Lite%20BR/Documents/GitHub/helpIA/.env.example)**: Documents required variables: `DEEPGRAM_API_KEY`, `GROQ_API_KEY` (or `OPENAI_API_KEY`), optional `GROQ_MODEL`, and optional `PULSE_SOURCE`.
- **[`requirements.txt`](file:///c:/Users/Windows%20Lite%20BR/Documents/GitHub/helpIA/requirements.txt)**: Platform-specific markers (`pyaudio` for Linux/macOS, `pyaudiowpatch` for Windows).

### Application Source (`src/`)
- **[`src/main.py`](file:///c:/Users/Windows%20Lite%20BR/Documents/GitHub/helpIA/src/main.py)**:
  - Class: `CopilotApp`
  - Instantiates subsystems, loads configuration, manages the cooperative async loop (`run()`), and safely transfers worker-thread audio data into the main event loop.
- **[`src/audio_capture.py`](file:///c:/Users/Windows%20Lite%20BR/Documents/GitHub/helpIA/src/audio_capture.py)**:
  - Class: `AudioCapture`
  - Resolves Linux pulse sinks via `pactl` or Windows WASAPI loopback devices via `pyaudiowpatch`. Emits raw 16-bit PCM chunks (100ms at 16kHz).
- **[`src/transcriber.py`](file:///c:/Users/Windows%20Lite%20BR/Documents/GitHub/helpIA/src/transcriber.py)**:
  - Class: `Transcriber`
  - Connects to Deepgram live streaming endpoint. Handles interim vs final transcription events, captures network disconnects, and manages exponential backoff auto-reconnects.
- **[`src/llm_service.py`](file:///c:/Users/Windows%20Lite%20BR/Documents/GitHub/helpIA/src/llm_service.py)**:
  - Class: `LLMService`
  - Prepares the interview system prompt embedding Moacir Neto's resume details and strict answering constraints. Invokes Groq completions via `stream=True`.
- **[`src/ui.py`](file:///c:/Users/Windows%20Lite%20BR/Documents/GitHub/helpIA/src/ui.py)**:
  - Class: `CopilotUI`
  - Frameless HUD window (`overrideredirect=True`) featuring custom title bar with mini VU-meter, status badge, drag handler with `after_idle`, opacity switcher, position presets, and textboxes.
- **[`src/diagnostic.py`](file:///c:/Users/Windows%20Lite%20BR/Documents/GitHub/helpIA/src/diagnostic.py)**:
  - Automated diagnostic harness capable of testing hardware loopback volume (dBFS) and Deepgram STT responsiveness without firing Tkinter.

### Test Suite (`tests/`)
- **[`tests/test_audio_resilience.py`](file:///c:/Users/Windows%20Lite%20BR/Documents/GitHub/helpIA/tests/test_audio_resilience.py)**:
  - Asserts RMS calculation formulas, VU-meter emoji/color state transitions, and transcriber disconnect callbacks.
- **[`tests/test_ui_shortcuts.py`](file:///c:/Users/Windows%20Lite%20BR/Documents/GitHub/helpIA/tests/test_ui_shortcuts.py)**:
  - Asserts that keyboard bindings (`Ctrl+Space`, `Ctrl+Enter`, `Esc`, `F8`, `F10`) call respective handlers and return `"break"`.
- **[`tests/test_ui_ux_overlay.py`](file:///c:/Users/Windows%20Lite%20BR/Documents/GitHub/helpIA/tests/test_ui_ux_overlay.py)**:
  - Asserts opacity switching (92% -> 100% -> 75% -> 85%), screen preset positioning, 1:1 drag math, and adaptive auto-scroll behavior.
