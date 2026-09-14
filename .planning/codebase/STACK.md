# Technology Stack

## Core Technologies
- **Language**: Python 3.12 (compatible with Python 3.10+)
- **Runtime Environment**: Linux (Ubuntu / Pop!_OS / Debian with PulseAudio / PipeWire) & Windows (WASAPI loopback via `pyaudiowpatch`)
- **Concurrency & Event Loop**: Native `asyncio` loop intertwined with `customtkinter` main event loop (`ui.update()` with non-blocking sleeps) and thread-safe dispatchers (`loop.call_soon_threadsafe`).

## Key Libraries & Dependencies
- **Audio Capture**:
  - Linux: `sounddevice` (>=0.5.0) reading PulseAudio/PipeWire sink monitors via `PULSE_SOURCE`.
  - Windows: `pyaudiowpatch` (or fallback `pyaudio`) utilizing WASAPI loopback capture.
  - Signal Math: `numpy` (>=1.24.0) for audio data buffer manipulation and RMS dBFS measurement.
- **Speech-to-Text (STT)**:
  - `deepgram-sdk` (>=3.0.0, <4.0.0): Real-time live transcription over WebSockets (`client.listen.live.v("1")`), utilizing Deepgram `nova-2` model with `pt-BR` language configuration, smart formatting, and interim/final sentence events.
- **LLM / AI Reasoning**:
  - `openai` (>=1.0.0): Initialized with Groq API endpoint (`https://api.groq.com/openai/v1`) using `AsyncOpenAI`.
  - Model: Defaulting to `qwen/qwen3.8-27b` (or fallback `llama3-8b-8192`), streaming responses token-by-token with temperature 0.3.
- **Graphical User Interface**:
  - `customtkinter` (>=5.2.0): Dark mode HUD overlay window (`overrideredirect=True`, `-topmost=True`, `-alpha=0.92`) with custom drag-motion event binding.
- **Configuration & Environment**:
  - `python-dotenv` (>=1.0.0): Loads `.env` environment variables (`DEEPGRAM_API_KEY`, `GROQ_API_KEY`, `OPENAI_API_KEY`, `GROQ_MODEL`, `PULSE_SOURCE`).

## Build & Environment Configuration
- **Virtual Environment**: Standard Python `venv` located at `./venv`.
- **System Packages**: Requires `portaudio19-dev`, `python3-pyaudio`, and `python3-tk` on Linux.
