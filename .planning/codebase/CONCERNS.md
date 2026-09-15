---
last_mapped_commit: 2408b9a93be90063fd0b7bab5ee0e721ddd47b9e
last_mapped_at: 2026-09-15
---

# Known Concerns & Technical Debt

**Analysis Date:** 2026-09-15

## Audio Subsystem Nuances

### 1. Dynamic Sink Hotplugging on Linux
- **Observation**: `_configure_linux_pulse_source()` resolves the active sink once during initialization.
- **Concern**: If the user switches audio outputs mid-interview (e.g. unplugging wired headphones to switch to Bluetooth, or docking a laptop), the `AudioCapture` instance continues monitoring the old sink unless restarted.
- **Mitigation / Next Step**: Implement a dynamic sink change listener or periodic health check verifying that the active sink is still `RUNNING`.

### 2. Windows WASAPI & Bluetooth Audio Modes
- **Observation**: `pyaudiowpatch` attaches to default speakers in loopback mode.
- **Concern**: When Bluetooth headsets enter Hands-Free Profile (HFP) during voice calls (e.g., in certain browser Meet sessions), Windows often changes the default audio output or locks the sample format to 8kHz/16kHz mono, which can trigger WASAPI initialization errors.
- **Mitigation**: Advise running audio through standard stereo profile (A2DP) or verify audio device settings before entering interviews.

## Window Management & Display Protocols

### 1. Pure Wayland vs XWayland
- **Observation**:
  - Window opacity on Linux uses `xprop` setting `_NET_WM_WINDOW_OPACITY`.
  - Multi-monitor boundary detection relies on `xrandr`.
  - Smooth dragging relies on `event.x_root`.
- **Concern**: In pure Wayland environments that do not support X11/XWayland or restrict inter-window positioning, `xprop` and `xrandr` fail silently. In those setups, the HUD falls back to default Tkinter geometry (`winfo_screenwidth()`), and opacity remains fixed.
- **Mitigation**: Future revisions could incorporate Wayland layer shell protocols if transitioning to a Qt/PyGObject architecture.

### 2. Tkinter Test Teardown Warnings
- **Observation**: Running `python -m unittest` outputs transient Tcl errors (`invalid command name ... ("after" script)`).
- **Impact**: Tests pass with 100% success (`OK`), but Tk's delayed event loop queues (`_init_after_id`, `after_idle`) fire after test teardown has destroyed the root window.
- **Mitigation**: Cancel all pending callbacks or mock `after` and `after_idle` entirely during unit test setUp/tearDown.

## AI & API Limits

### 1. Model Token Budget
- **Observation**: `max_tokens` is intentionally restricted to `250` in `src/llm_service.py` to enforce concise, spoken answers (3–4 sentences).
- **Concern**: If an interviewer asks a compound question requiring multiple explanations, the answer might end abruptly at the token boundary.
- **Mitigation**: Add a dynamic token adjustment or a "Continuar resposta" button to stream subsequent sentences if needed.

### 2. Rate Limits & Latency
- **Observation**: Groq Cloud offers extremely fast inference (~300-500 tokens/sec), but free-tier API keys have request-per-minute (RPM) and token-per-minute (TPM) limits.
- **Concern**: Rapid, repeated triggers of `Ctrl+Enter` could temporarily exhaust rate limits.
- **Mitigation**: `CopilotApp` actively cancels the previous LLM task before issuing a new one, mitigating wasted token consumption.

## Security & Secrets Management
- **Observation**: API keys (`DEEPGRAM_API_KEY`, `GROQ_API_KEY`, `OPENAI_API_KEY`) reside in `.env`.
- **Precaution**: Maintain `.env` strictly in `.gitignore`. Ensure diagnostic and logging scripts only print masked keys (`key[:6] + '...'`) in terminal outputs.
