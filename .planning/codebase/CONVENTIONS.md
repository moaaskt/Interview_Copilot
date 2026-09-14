# Coding Conventions & Patterns

## Language & Style
- **Python Version**: Python 3.10+ (using type hints like `int | None`, `Optional[T]`, `Callable`).
- **Code Style**: PEP 8 compliant, 4-space indentation, clear docstrings for classes and methods.
- **Comments & Log Messages**: Written in Brazilian Portuguese (`pt-BR`) for logs and user alerts; code symbols and identifiers in English (`CopilotApp`, `AudioCapture`, `Transcriber`, `LLMService`).

## Concurrency & Thread-Safety
- **Thread Boundaries**: Audio input streams run in background native threads (via sounddevice/PortAudio callbacks).
- **Callback Marshalling**: Never update Tkinter widgets directly from background worker threads. Always dispatch using `loop.call_soon_threadsafe(callback, *args)`.
- **Cooperative Polling**: `ui.update()` runs inside the main `asyncio` task paired with `await asyncio.sleep(0.01)` to prevent CPU pinning while maintaining 60+ FPS UI responsiveness.

## Error Handling & Resilience
- Graceful fallbacks in audio device detection: scans running pulse sinks, then default sink, then warns user.
- LLM streaming exceptions wrapped in try/except blocks yielding user-visible error markers without crashing the UI.
- Task cancellation handling (`asyncio.CancelledError`) for quick interruption of outdated AI responses.
