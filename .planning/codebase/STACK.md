---
last_mapped_commit: 2408b9a93be90063fd0b7bab5ee0e721ddd47b9e
last_mapped_at: 2026-09-15
---

# Technology Stack

**Analysis Date:** 2026-09-15

## Core Technologies
- **Language**: Python 3.12 (compatible with Python 3.10+)
- **Runtime Environments**:
  - **Linux**: Ubuntu / Debian / Pop!_OS / Fedora with PulseAudio or PipeWire audio servers, X11 or XWayland display servers.
  - **Windows**: Windows 10 / Windows 11 with WASAPI audio loopback and native Tkinter rendering.
- **Concurrency & Event Loop**: Native `asyncio` event loop integrated with `customtkinter` main event loop via cooperative non-blocking cycles (`self.ui.update()` followed by `await asyncio.sleep(0.01)`) and thread-safe dispatchers (`loop.call_soon_threadsafe`).

## Key Libraries & Dependencies
- **Audio Capture**:
  - `sounddevice` (`>=0.5.0`): Used on Linux for low-latency audio capture from PulseAudio/PipeWire sink monitor devices.
  - `pyaudiowpatch` (`>=0.2.12`; Windows only): WASAPI loopback capture implementation allowing recording of internal speaker output without virtual cables.
  - `pyaudio` (`>=0.2.14`; non-Windows platforms): Cross-platform PortAudio bindings.
  - `numpy` (`>=1.24.0`): Efficient audio chunk buffer conversion (`np.int16`), RMS calculation (`np.sqrt(np.mean(...))`), and VU-meter level analysis.
- **Speech-to-Text (STT)**:
  - `deepgram-sdk` (`>=3.0.0, <4.0.0`): Real-time live transcription over WebSocket (`client.listen.live.v("1")`), utilizing Deepgram `nova-2` model with Brazilian Portuguese (`pt-BR`) language support, smart formatting, and interim/final sentence events.
- **LLM / AI Reasoning**:
  - `openai` (`>=1.0.0`): Initialized with Groq API endpoint (`https://api.groq.com/openai/v1`) using `AsyncOpenAI`.
  - Default Model: `qwen/qwen3.8-27b` (configurable via `GROQ_MODEL`, fallback `llama3-8b-8192`), streaming responses token-by-token with temperature 0.3.
- **Graphical User Interface**:
  - `customtkinter` (`>=5.2.0`): Modern dark mode HUD overlay window (`overrideredirect=True`, `-topmost=True`, `-alpha=0.92`).
  - Native `tkinter`: Underlying Tk widgets (`Frame`, `Label`) utilized for zero-latency dragging and event interception.
- **Configuration & Environment**:
  - `python-dotenv` (`>=1.0.0`): Loads `.env` configuration from project root with `override=True`.

## Testing Stack
- **Test Framework**: Python standard library `unittest`.
- **Mocking & Isolation**: `unittest.mock.MagicMock` and `unittest.mock.patch` for decoupled validation of GUI events, audio buffers, and socket callbacks.

## System Dependencies & Prerequisites
- **Linux**:
  - Audio packages: `portaudio19-dev`, `python3-pyaudio`, `pulseaudio-utils` (`pactl`).
  - GUI packages: `python3-tk`.
  - X11 utilities: `xprop` (for compositor opacity `_NET_WM_WINDOW_OPACITY`), `xwininfo` (for window hierarchy inspection), `xrandr` (for multi-monitor detection).
- **Windows**:
  - C++ Build Tools or pre-built wheels for `pyaudiowpatch`.
