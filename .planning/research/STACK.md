# Stack Research

**Domain:** Windows AI Voice Assistant with Local LLMs
**Researched:** 2026-02-28
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.11+ | Primary language | Best ecosystem for local AI, Ollama support, extensive libraries |
| Ollama | latest | Local LLM runtime | Simplest way to run LLMs locally, excellent Python SDK, Windows native support |
| faster-whisper | 1.0+ | Speech-to-text | 4x faster than original Whisper, CTranslate2 backend, GPU support |
| Kokoro | v1.0 | Text-to-speech | 82M parameter model, runs locally, 31 voices, best open-source TTS |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| chromadb | 1.5.0+ | Vector store | Memory/embedding storage |
| langchain | 0.3+ | LLM orchestration | Tool calling, prompt management |
| langchain-community | 0.3+ | LangChain integrations | Ollama, Chroma integrations |
| pyaudio | latest | Audio input/output | Microphone input, speaker output |
| numpy | latest | Audio processing | Required by Kokoro, faster-whisper |
| sounddevice | latest | Audio I/O | Alternative to pyaudio, more reliable on Windows |
| pvporcupine | latest | Wake word detection | Low-power wake word, "JARVIS" custom wake word support |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| VS Code + Pylance | IDE | Best Python support on Windows |
| uv | Package manager | Faster than pip, better dependency resolution |
| nvidia-smi | GPU detection | VRAM detection for model selection |

### AI Models (via Ollama)

| Model | VRAM Required | Use Case |
|-------|---------------|----------|
| llama3.2:1b | 2GB | CPU fallback, fast responses |
| llama3.2:3b | 4GB | Balanced performance |
| qwen2.5:7b | 8GB | High quality, mainstream GPU |
| mistral:7b | 8GB | Fast inference, good reasoning |

## Installation

```bash
# Core dependencies
pip install ollama faster-whisper chromadb langchain langchain-community
pip install pyaudio sounddevice numpy pvporcupine

# Install Kokoro (separate - requires GitHub)
git clone https://github.com/hexgrad/kokoro-82m.git
cd kokoro-82m
pip install -r requirements.txt

# Pull recommended LLM models
ollama pull llama3.2:3b
ollama pull mistral:7b
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Ollama | llama.cpp directly | Need maximum control over quantization |
| faster-whisper | openai-whisper | When GPU not available, accept slower speed |
| Kokoro | Coqui TTS | Need more voice variety |
| chromadb | FAISS | When persistence not needed, in-memory only |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Cloud LLMs (OpenAI API) | Violates privacy requirement | Ollama with local models |
| vosk | Lower accuracy than Whisper | faster-whisper |
| pyttsx3 | Robotic quality, limited voices | Kokoro |
| gTTS | Requires internet | Kokoro |
| SQL-based vector search | Poor semantic search | ChromaDB |

## Stack Patterns by Variant

**If CPU-only (no GPU):**
- Use llama3.2:1b or tinyllama
- Use faster-whisper with CPU (slower but works)
- Kokoro still works on CPU (slower)

**If 4GB VRAM:**
- Use llama3.2:3b
- Use faster-whisper with GPU
- Kokoro with CPU processing

**If 8GB+ VRAM:**
- Use mistral:7b or qwen2.5:7b
- Full GPU acceleration throughout
- Best responsiveness

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| Python | 3.11, 3.12 | 3.10 may have compatibility issues |
| chromadb | 1.5.0+ | Breaking changes in 1.x |
| langchain | 0.3.x | API changed significantly in 0.3 |
| faster-whisper | 1.0+ | Requires Python 3.9+ |

## Sources

- InsiderLLM guide (2026-02-11) — local AI assistant stack overview
- SYSTRAN/faster-whisper GitHub — STT implementation details
- hexgrad/Kokoro-82M — TTS model documentation
- Ollama official docs — LLM runtime
- ChromaDB 1.5.0 release — vector store

---
*Stack research for: JARVIS Windows AI Voice Assistant*
*Researched: 2026-02-28*
