# Directory & File Structure

```
helpIA/
├── .env                  # Environment variables & private API keys (gitignored)
├── .env.example          # Sample environment configuration template
├── .gitignore            # Git exclusion rules
├── README.md             # Project documentation & execution guide
├── requirements.txt      # Core Python package dependencies
├── venv/                 # Python 3.12 virtual environment directory
├── .planning/            # Project planning & codebase intelligence
│   └── codebase/         # Codebase map documents
└── src/                  # Application source code
    ├── __init__.py       # (Optional) Package marker
    ├── main.py           # Application entrypoint & asyncio orchestrator (CopilotApp)
    ├── audio_capture.py  # Cross-platform internal loopback audio capture (AudioCapture)
    ├── transcriber.py    # Deepgram WebSocket real-time transcription client (Transcriber)
    ├── llm_service.py    # Groq LLM streaming integration & interview persona (LLMService)
    ├── ui.py             # CustomTkinter transparent floating HUD overlay (CopilotUI)
    └── diagnostic.py     # Standalone diagnostic & testing utility for audio & Deepgram
```

## Module Responsibilities
- `src/main.py`: Coordinates the application lifecycle, bridges callbacks between audio, STT, LLM, and GUI, and runs the unified async loop.
- `src/audio_capture.py`: Selects pulse/pipewire monitor sinks on Linux or WASAPI devices on Windows, pushing 100ms PCM chunks at 16kHz.
- `src/transcriber.py`: Encapsulates Deepgram WebSocket events, managing connection lifecycles and interim/final transcription events.
- `src/llm_service.py`: Formats interview prompts with candidate background and streams token completions from Groq.
- `src/ui.py`: Manages the borderless floating overlay, drag-and-drop window movements, and thread-safe text widget updates.
- `src/diagnostic.py`: Autonomous script verifying audio capture levels (RMS dBFS) and Deepgram STT responsiveness without launching the GUI.
