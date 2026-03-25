# How to Run JARVIS

This guide explains how to run JARVIS on your local machine.

---

## Prerequisites

- **Python 3.11+** - Download from python.org
- **Ollama** - For local LLM inference
  - Download from: https://ollama.com
  - Must be running on `localhost:11434`
- **Node.js 18+** (optional) - For CLI npm package

---

## Local Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd JARVISE
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux/Mac
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
# Required: Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=llama3.2:latest

# Optional: UI Configuration
UI_HOST=127.0.0.1
UI_PORT=8000
```

### 5. Start Ollama

Ensure Ollama is running with your chosen model:

```bash
ollama serve
ollama pull llama3.2
```

---

## Running JARVIS

### Option 1: Full Application (Recommended)

Starts both backend API and web UI:

```bash
python main.py
```

Then open **http://localhost:8000** in your browser.

---

### Option 2: Backend Only

For API-only access:

```bash
python -m backend.main
```

The API will be available at **http://localhost:8000**

---

### Option 3: CLI Shell

Interactive terminal interface:

```bash
# Using installed package
jarvis shell

# Or using Python module
python -m cli shell
```

Commands:
- Type normally to chat
- `:help` - Show help
- `:stats` - System statistics
- `:memory` - View memories
- `:clear` - Clear conversation
- `:quit` - Exit

---

### Option 4: One-liner Chat

Send a single message:

```bash
jarvis chat "Hello, how are you?"
```

---

## Running the Web UI (Alternative)

The frontend is a React application. To run it separately:

```bash
# Navigate to UI directory
cd ui

# Install dependencies
npm install

# Build for production
npm run build

# The built files are served by the backend (main.py)
```

---

## Troubleshooting

### Ollama Not Running

```bash
# Check if Ollama is running
ollama list

# Start Ollama
ollama serve
```

### Port Already in Use

Change the port in `.env`:

```bash
UI_PORT=8001
```

### Memory Issues

If you encounter VRAM issues, use a smaller model:

```bash
OLLAMA_MODEL=llama3.2:1b
```

---

## Next Steps

- See **README.md** for full feature documentation
- Check **Docs/** folder for advanced topics
- Configure API key for remote access in `.env`

---

*For more information, see README.md*
