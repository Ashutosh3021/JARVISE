# JARVIS CLI

Command-line interface for JARVIS AI Assistant

## Installation

```bash
pip install -e .
```

## Usage

### Interactive Shell Mode
```bash
jarvis shell
```

### Chat Mode
```bash
jarvis chat "Hello, how are you?"
```

### Memory Management
```bash
jarvis memory list              # List all memories
jarvis memory search "python"   # Search memories
jarvis memory stats             # Show memory statistics
jarvis memory clear             # Clear all memories
```

### System Stats
```bash
jarvis stats
```

### Settings
```bash
jarvis settings show
```

## Requirements

- Python 3.10+
- aiohttp
- websockets
- requests
- prompt-toolkit (optional, for enhanced shell)

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black cli/
ruff check cli/
```
