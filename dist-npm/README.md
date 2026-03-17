# JARVIS AI - Node.js Package

Your personal AI assistant - npm package

## Installation

```bash
npm install jarvis-ai
# or
npm install -g jarvis-ai  # For CLI
```

## Usage

### CLI

```bash
# Interactive shell
jarvis shell

# Send a message
jarvis chat "Hello!"

# Open web UI
jarvis web

# View stats
jarvis stats

# Start server
jarvis server start
```

### As a Module

```javascript
const { JarvisClient } = require('jarvis-ai');

const jarvis = new JarvisClient({
  url: 'http://localhost:8000'
});

// Chat
const response = await jarvis.chat('Hello!');
console.log(response);

// Get stats
const stats = await jarvis.getStats();
console.log(stats);

// Get memories
const memories = await jarvis.getMemories();
```

## Environment Variables

```bash
export JARVIS_URL=http://localhost:8000
```

## Features

- Interactive shell mode
- One-liner chat commands
- WebSocket streaming
- Memory management
- System stats
- Web UI launcher

## License

MIT
