# J.A.R.V.I.S

> **Just A Rather Very Intelligent System**  
> A personal AI assistant built in Python — voice-controlled, system-aware, and always on call.

---

## What is J.A.R.V.I.S?

J.A.R.V.I.S is a locally-run AI assistant that responds to your voice, answers your questions, and controls your system — no cloud subscription, no nonsense. Think less "smart speaker" and more "personal command center."

- 🎙️ **Voice commands** — talk to it naturally, it listens and responds
- 🖥️ **System control** — open apps, manage files, run tasks
- 🤖 **AI chat / Q&A** — ask it anything, get intelligent answers
- ⚡ **Fast & local** — runs on your machine, your rules

---

## Demo

```
You:    "Hey J.A.R.V.I.S, open VS Code"
JARVIS: "Opening Visual Studio Code, sir."

You:    "What's the capital of Japan?"
JARVIS: "Tokyo, sir. Population approximately 14 million."

You:    "Open the downloads folder"
JARVIS: "Done."
```

---

## Install

```bash
git clone https://github.com/yourusername/JARVIS.git
cd JARVIS
pip install -r requirements.txt
```

### Requirements

```bash
pip install speechrecognition pyttsx3 openai pyaudio psutil
```

> **Note:** `pyaudio` may require extra setup on some systems.  
> - **Windows:** `pip install pipwin && pipwin install pyaudio`  
> - **Linux:** `sudo apt install portaudio19-dev && pip install pyaudio`  
> - **Mac:** `brew install portaudio && pip install pyaudio`

---

## Usage

```bash
python jarvis.py
```

Then just speak. J.A.R.V.I.S will listen, process, and respond.

### Example Commands

| You say | J.A.R.V.I.S does |
|---------|-----------------|
| `"Open Chrome"` | Launches Google Chrome |
| `"Open my downloads"` | Opens the Downloads folder |
| `"What time is it?"` | Tells you the current time |
| `"Search for Python tutorials"` | Opens a browser search |
| `"Shut down"` | Exits the assistant |

---

## Project Structure

```
JARVIS/
├── jarvis.py              ← Entry point
├── core/
│   ├── listener.py        ← Voice recognition (SpeechRecognition)
│   ├── speaker.py         ← Text-to-speech (pyttsx3)
│   ├── brain.py           ← AI response logic
│   ├── commands.py        ← System control (apps, files)
│   └── utils.py           ← Helpers (time, date, search)
├── config/
│   └── settings.py        ← Wake word, voice, API keys
├── requirements.txt
└── README.md
```

---

## Configuration

```python
# config/settings.py
WAKE_WORD      = "jarvis"          # Word that activates listening
VOICE_RATE     = 175               # Speech speed (words per minute)
VOICE_VOLUME   = 1.0               # Volume (0.0 to 1.0)
AI_MODEL       = "gpt-3.5-turbo"   # Swap for any model you're using
API_KEY        = "<your-api-key>"  # Your AI provider key
```

---

## Tech Stack

| Tool | Role |
|------|------|
| [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) | Converts voice to text |
| [pyttsx3](https://pypi.org/project/pyttsx3/) | Text-to-speech (offline) |
| [PyAudio](https://pypi.org/project/PyAudio/) | Microphone access |
| [psutil](https://pypi.org/project/psutil/) | System info & process control |
| Python `subprocess` / `os` | Launch apps and manage files |

---

## Roadmap

| Feature | Status |
|---------|--------|
| Voice command recognition | ✅ Done |
| Text-to-speech responses | ✅ Done |
| Open apps & files | ✅ Done |
| AI chat / Q&A | ✅ Done |
| Wake word detection | 🔧 In progress |
| Custom command plugins | 🔲 Planned |
| GUI / HUD overlay | 🔲 Planned |
| Memory across sessions | 🔲 Planned |

---

## Contributing

PRs welcome. If you add a new command module or improve the voice pipeline, open a pull request and let's make it better together.

---

## License

MIT — see [LICENSE](./LICENSE)

---

*"At your service."*