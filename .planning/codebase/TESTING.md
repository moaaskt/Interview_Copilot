---
last_mapped_commit: 2408b9a93be90063fd0b7bab5ee0e721ddd47b9e
last_mapped_at: 2026-09-15
---

# Testing Strategy & Verification

**Analysis Date:** 2026-09-15

## Testing Architecture
The codebase employs a three-tier testing strategy:
1. **Automated Unit & Integration Test Suite** (`tests/`): Fast, headless tests using Python's standard `unittest` and mocks to validate widget behaviors, math formulas, and state machines.
2. **Autonomous Hardware Diagnostic CLI** (`src/diagnostic.py`): Hardware and network validation script testing audio drivers and API connectivity without requiring a GUI.
3. **Manual Verification Protocol (UAT)**: Real-time interview simulation checking audio clarity, visual overlay contrast, and hotkey ergonomics.

## Automated Test Suite (`tests/`)

### Running All Tests
```bash
python -m unittest discover -s tests -p "test_*.py"
```
*(Total: 21 tests running in ~3.2 seconds)*

### Test Modules

#### 1. Audio Resilience & VU-Meter (`tests/test_audio_resilience.py`)
- `test_audio_meter_silence`: Confirms RMS `< 150` yields `🎙 ···` in `#585B70`.
- `test_audio_meter_low`: Confirms RMS `150..800` yields `🎙 ▃··` in `#94E2D5`.
- `test_audio_meter_medium`: Confirms RMS `800..2500` yields `🎙 ▃▅·` in `#A6E3A1`.
- `test_audio_meter_high`: Confirms RMS `> 2500` yields `🎙 ▃▅█` in `#89B4FA`.
- `test_rms_calculation_synthetic_pcm`: Validates PCM byte conversion and mathematical RMS computation.
- `test_transcriber_handle_disconnect_triggers_callback`: Verifies socket drop invokes `on_connection_change(False)`.
- `test_main_on_connection_change`: Asserts status badge reflects `"Reconectando"` and `"Pronto"`.

#### 2. UI Shortcuts & Bindings (`tests/test_ui_shortcuts.py`)
- `test_handler_toggle_recording_returns_break`: Confirms `Ctrl+Space` / `F9` returns `"break"` to prevent key bleeding.
- `test_handler_respond_now_returns_break`: Confirms `Ctrl+Enter` returns `"break"`.
- `test_handler_clear_returns_break`: Confirms `Esc` / `Ctrl+Backspace` returns `"break"`.
- `test_button_labels_contain_shortcuts`: Verifies button visual text displays shortcut legends.
- `test_recording_state_toggles_button_text`: Verifies recording toggle alters button text and colors.
- `test_global_bindings_registered`: Confirms global keybinds are registered on the root window.

#### 3. Overlay UX & Positioning (`tests/test_ui_ux_overlay.py`)
- `test_cycle_opacity`: Validates 4-stage opacity toggle (`0.92` -> `1.0` -> `0.75` -> `0.85` -> `0.92`).
- `test_cycle_window_position`: Asserts geometry updates across 4 presets (`top-center`, `top-right`, `top-left`, `center`).
- `test_shortcuts_f8_and_f10_bound`: Checks bindings for `F8` (position cycle) and `F10` (opacity cycle).
- `test_adaptive_auto_scroll_following_tokens`: Asserts `.see("end")` is invoked during normal token generation.
- `test_adaptive_auto_scroll_pauses_when_scrolled_up`: Asserts auto-scroll is suspended when `yview()[1] < 0.98`.
- `test_drag_smooth_delta_calculation`: Validates absolute coordinate difference calculations and `after_idle` scheduling.
- `test_multi_monitor_bounds_detection`: Validates parsing of screen boundaries.

## Standalone Diagnostic CLI (`src/diagnostic.py`)
Runs without launching the GUI:
```bash
python src/diagnostic.py
```
Performs three automated checks:
1. **Audio Capture Test (5s)**: Captures from PulseAudio/PipeWire sink monitor, computes average dBFS, and asserts `avg_db > -60.0 dBFS`.
2. **Batch STT Test**: Streams buffered PCM audio into Deepgram WebSocket to ensure credentials and socket handshake work.
3. **Full Live Streaming Test (10s)**: Streams live system output to Deepgram, printing interim and final hypotheses.

## Manual UAT Protocol
1. Launch application: `python src/main.py`.
2. Verify floating HUD appears without window borders and stays atop browser/terminal windows.
3. Play a YouTube video or Google Meet test call: verify mini VU-meter (`🎙 ▃▅█`) reacts to speech audio in real time.
4. Press `Ctrl+Space` to start recording: verify badge turns pink (`● Ouvindo Pergunta...`).
5. Press `Ctrl+Space` again to stop: verify transcription settles and Groq streams answer token-by-token in green text.
6. Press `F8` to cycle positions (e.g. snapping under webcam).
7. Press `F10` to cycle opacity profiles (testing stealth/discreet modes).
8. Press `Esc` to clear session and reset state.
