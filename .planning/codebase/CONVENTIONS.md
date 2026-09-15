---
last_mapped_commit: 2408b9a93be90063fd0b7bab5ee0e721ddd47b9e
last_mapped_at: 2026-09-15
---

# Coding Conventions & Patterns

**Analysis Date:** 2026-09-15

## Language & Formatting Standards
- **Python Standard**: Python 3.10+ strict typing.
- **Type Annotations**: Type hints on all class fields, function parameters, and return types (`Callable[[bytes], None]`, `Optional[int]`, `str | None`, `tuple[int, int, int, int]`).
- **Naming Conventions**:
  - Classes: `PascalCase` (`CopilotApp`, `AudioCapture`, `Transcriber`, `LLMService`, `CopilotUI`).
  - Functions & Variables: `snake_case` (`on_audio_data`, `cycle_window_position`, `_apply_opacity`).
  - Constants & Enums: `UPPER_SNAKE_CASE` (`IS_WINDOWS`).
  - Private Members: Prefixed with a single underscore (`_reconnect_loop`, `_drag_target_x`).
- **Language / Localization Rules**:
  - Code, comments, variable names, and documentation: English.
  - UI Labels, status messages, console logs, and candidate persona: Brazilian Portuguese (`pt-BR`).

## Concurrency & Thread Boundary Rules
- **The GUI Golden Rule**: Never mutate Tkinter or CustomTkinter widgets directly from PortAudio or background worker threads.
- **Threadsafe Dispatching**: When worker threads (such as the audio stream callback in `audio_capture.py`) receive data, they dispatch to the UI thread using:
  ```python
  loop.call_soon_threadsafe(self.audio_callback, data_bytes)
  ```
- **Cooperative Main Loop**:
  - `CopilotUI` does **not** invoke `ui.mainloop()`.
  - Instead, `main.py` runs a continuous async loop:
  ```python
  while True:
      self.ui.update()
      await asyncio.sleep(0.01)
  ```
  This guarantees responsive GUI rendering (up to 100 FPS) alongside native `asyncio` networking without GIL thrashing.

## Event Handling & Widget Conventions
- **Event Interception**: Keyboard shortcut handlers and mouse dragging handlers must return `"break"` to prevent default Tk event propagation:
  ```python
  def _handle_toggle_recording(self, event=None) -> Optional[str]:
      if self.on_toggle_recording:
          self.on_toggle_recording()
      return "break"
  ```
- **Idle-Throttled Dragging**:
  - Mouse movement events (`<B1-Motion>`) record target offsets (`event.x_root - offset`) and schedule updates with `self.after_idle(self._apply_drag)`.
  - This prevents high-frequency polling events from overwhelming the window manager queue on high-refresh monitors (144Hz+) and XWayland sessions.
- **Adaptive Auto-Scroll**:
  - When appending streaming tokens into textboxes, inspect the vertical scroll fraction (`self.ai_textbox._textbox.yview()`).
  - If `bottom < 0.98`, the user has manually scrolled up to read previous text—suspend auto-scrolling to prevent viewport hijacking.

## Error Handling & Resilience Conventions
- **Network Resilience**: Long-running network connections (Deepgram WebSockets) must implement automatic recovery with backoff.
- **Task Cancellation**: Active background tasks (such as Groq LLM streaming) must be stored in `self.current_llm_task` and cancelled (`task.cancel()`) before dispatching new inferences. Handlers must catch `asyncio.CancelledError`.
- **Hardware Fallbacks**: Sound input queries must fall back gracefully from preferred named devices (Pulse/PipeWire/WASAPI) to default system devices with explanatory warning logs rather than crashing.
