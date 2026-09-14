# Architecture Overview

## Design Pattern & Pipeline
The application uses an asynchronous, event-driven pipeline connecting internal audio capture to cloud transcription, LLM generation, and a GUI HUD.

```
[System Output / Meet Audio]
          │
          ▼
┌──────────────────┐
│  AudioCapture    │ (sounddevice / PyAudioWPatch loopback stream @ 16kHz mono)
└─────────┬────────┘
          │ (PCM chunks when is_recording=True)
          ▼
┌──────────────────┐
│   Transcriber    │ (Deepgram WebSocket live stream, nova-2 pt-BR)
└─────────┬────────┘
          │ (interim / final sentence events)
          ▼
┌──────────────────┐
│    CopilotApp    │ (Orchestrator in main.py, manages buffer & state)
└─────────┬────────┘
          │
     ┌────┴──────────────────────────┐
     ▼                               ▼
┌──────────────────┐       ┌──────────────────┐
│    CopilotUI     │       │    LLMService    │ (Groq AsyncOpenAI streaming)
│ (CustomTkinter)  │◄──────┤ (qwen3.8-27b)    │
└──────────────────┘       └──────────────────┘
```

## Architectural Characteristics
1. **Unified Event Loop**: Runs `asyncio` loop concurrently with CustomTkinter's GUI loop without thread blocking (`self.ui.update()` followed by `await asyncio.sleep(0.01)`).
2. **Push-to-Record Control**: Audio streaming to Deepgram is gated by `is_recording`. While recording, chunks flow directly to the active WebSocket.
3. **Dual Transcription Buffering**:
   - `transcript_buffer` stores completed segments from `on_final_transcript`.
   - Interim transcripts are displayed live and appended seamlessly to current finalized text.
4. **Resilient LLM Dispatch**:
   - Triggers streaming on manual stop or "Responder Agora".
   - Active LLM streaming tasks are automatically canceled if a new query is submitted or cleared.
