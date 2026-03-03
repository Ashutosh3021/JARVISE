# Phase 7: UI Layer - Research

**Researched:** 2026-03-04
**Domain:** FastAPI backend + React SPA with WebSocket streaming
**Confidence:** HIGH

## Summary

Phase 7 implements a web interface for JARVIS monitoring and control. The recommended stack is FastAPI backend with WebSocket support for real-time token streaming, combined with a React SPA using Vite and Tailwind CSS v4. The existing codebase has strong integration points: `brain/agent.py` already has a `stream_run` method that yields tokens, and `tools/system_monitor.py` provides comprehensive system stats. The key technical decisions involve WebSocket vs SSE for streaming, React component architecture for chat UI, and Tailwind dark mode implementation.

**Primary recommendation:** Use FastAPI WebSocket endpoints for streaming, native WebSocket API in React (or react-use-websocket), Tailwind CSS v4 with class-based dark mode, and a polling interval of 5 seconds for system stats as specified.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **Page structure:** Single-page with panels — Main chat area + collapsible sidebar
- **Navigation:** Sidebar navigation — Icons + labels on left side
- **Color scheme:** Slate dark (#1e1e2e) — Purple-tinted, modern feel
- **Styling:** Tailwind CSS — Utility classes, rapid development
- **Accent color:** Teal (#14b8a6) — JARVIS-y, futuristic
- **Light/dark mode:** Toggle in UI — User can switch manually
- **Message style:** Standard bubbles — User right, JARVIS left with avatars
- **Streaming:** Chunk reveal — Words appear at a time
- **Input controls:** Full toolbar — Text, voice, file upload, emoji picker
- **Thinking state:** Animated dots — Pulsing animation
- **Stats:** CPU, Memory, VRAM — Core metrics
- **Position:** Collapsible — Can hide/show with toggle
- **Update frequency:** Every 5 seconds — Balanced
- **Extra info:** All — Connection status, model in use, session info
- **WebSocket events:** chat.stream, system.stats, voice.state
- **REST API:** Hybrid — REST for CRUD, WebSocket for streaming
- **Authentication:** No auth — Local only, no authentication
- **CORS:** Specific origins — Production-ready

### Claude's Discretion
- Exact component library choices (Radix UI, Headless UI, etc.)
- Exact Tailwind config values
- WebSocket reconnection strategy
- Error boundary implementation

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| UI-01 | FastAPI server with WebSocket support | FastAPI has native WebSocket support via starlette. Existing requirements.txt includes fastapi, uvicorn, websockets. |
| UI-02 | Live token streaming endpoint | Use WebSocket to stream tokens from brain/agent.py stream_run() method to React client. |
| UI-03 | Memory management endpoints | REST endpoints for memory CRUD operations (read MEMORY.md, search vectors, etc.). |
| UI-04 | React single-page application | Vite + React setup with Tailwind CSS v4. |
| UI-05 | Dark-themed status bar | Tailwind dark mode with class strategy, Slate dark (#1e1e2e) as base. |
| UI-06 | Animated waveform display | CSS animations or canvas-based waveform for voice activity. |
| UI-07 | Chat window interface | Chat bubbles component with streaming text reveal. |
| UI-08 | Live system stats display | WebSocket or polling to tools/system_monitor.py every 5 seconds. |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | >=0.109.0 | Backend API framework | Already in requirements.txt, native WebSocket support |
| Uvicorn | >=0.27.0 | ASGI server | Already in requirements.txt |
| React | 18+ | Frontend framework | Industry standard for SPAs |
| Vite | 5+ | Build tool | Fast dev server, standard with React |
| Tailwind CSS | v4 | Styling | User-specified, utility-first |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| react-use-websocket | 4.x | WebSocket hook | Optional - can use native API |
| python-multipart | >=0.0.6 | File uploads | For UI file attachment feature |
| lucide-react | latest | Icons | Sidebar navigation icons |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| WebSocket | SSE (Server-Sent Events) | SSE simpler for one-way streaming but WebSocket handles bi-directional (chat + stats) better |
| react-use-websocket | Native WebSocket API | Native API is sufficient, no extra dependency |
| Tailwind v4 | Tailwind v3 | v4 has cleaner config with @theme directive |

**Installation:**
```bash
# Backend (already in requirements.txt)
pip install fastapi uvicorn websockets python-multipart

# Frontend
npm create vite@latest ui -- --template react-ts
cd ui
npm install
npm install tailwindcss @tailwindcss/vite
npm install lucide-react
```

## Architecture Patterns

### Recommended Project Structure
```
ui/                          # React SPA
├── public/
├── src/
│   ├── components/
│   │   ├── Chat/           # Chat bubble components
│   │   ├── Sidebar/        # Navigation sidebar
│   │   ├── StatusBar/      # System stats display
│   │   ├── Toolbar/        # Input toolbar
│   │   └── Waveform/       # Animated waveform
│   ├── hooks/
│   │   ├── useWebSocket.ts # WebSocket connection hook
│   │   ├── useChat.ts      # Chat logic hook
│   │   └── useSystemStats.ts
│   ├── context/
│   │   └── ThemeContext.tsx
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── index.html
├── vite.config.ts
└── package.json

backend/                     # FastAPI (can be in root or ui/backend)
├── api/
│   ├── routes/
│   │   ├── chat.py         # Chat endpoints
│   │   ├── memory.py       # Memory management
│   │   └── stats.py        # System stats
│   └── websocket/
│       └── manager.py      # WebSocket connection manager
├── main.py
└── requirements.txt
```

### Pattern 1: FastAPI WebSocket Token Streaming
**What:** Stream tokens from LLM to React client in real-time
**When to use:** UI-02 requirement - live token streaming
**Example:**
```python
# backend/api/websocket/manager.py
from fastapi import WebSocket
from typing import List

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_token(self, token: str, websocket: WebSocket):
        await websocket.send_json({"type": "token", "content": token})

    async def broadcast_system_stats(self, stats: dict):
        for connection in self.active_connections:
            await connection.send_json({"type": "stats", "data": stats})
```

```python
# backend/api/routes/chat.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from brain.agent import ReActAgent

router = APIRouter()
manager = ConnectionManager()
agent = ReActAgent()

@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            
            # Stream tokens from agent
            for token, is_final in agent.stream_run(message):
                await manager.send_token(token, websocket)
                if is_final:
                    await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

### Pattern 2: React WebSocket Hook
**What:** Reusable hook for WebSocket connections with auto-reconnect
**When to use:** UI-04, UI-07 - Chat interface with streaming
**Example:**
```typescript
// ui/src/hooks/useChatWebSocket.ts
import { useState, useEffect, useCallback, useRef } from 'react';

interface UseChatWebSocketReturn {
  messages: ChatMessage[];
  isStreaming: boolean;
  sendMessage: (text: string) => void;
  connectionStatus: 'connecting' | 'connected' | 'disconnected';
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export function useChatWebSocket(url: string): UseChatWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');

  useEffect(() => {
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => setConnectionStatus('connected');
    ws.onclose = () => setConnectionStatus('disconnected');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'token') {
        setMessages(prev => {
          const last = prev[prev.length - 1];
          if (last?.role === 'assistant' && !last.id.includes('_streaming')) {
            // Update streaming message
            return [...prev.slice(0, -1), { 
              ...last, 
              content: last.content + data.content 
            }];
          }
          return prev;
        });
        setIsStreaming(true);
      } else if (data.type === 'done') {
        setIsStreaming(false);
      }
    };

    return () => ws.close();
  }, [url]);

  const sendMessage = useCallback((text: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const userMessage: ChatMessage = {
        id: `user_${Date.now()}`,
        role: 'user',
        content: text,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, userMessage]);
      
      // Add placeholder for assistant response
      setMessages(prev => [...prev, {
        id: `assistant_${Date.now()}_streaming`,
        role: 'assistant',
        content: '',
        timestamp: new Date()
      }]);
      
      wsRef.current.send(JSON.stringify({ message: text }));
    }
  }, []);

  return { messages, isStreaming, sendMessage, connectionStatus };
}
```

### Pattern 3: Tailwind CSS v4 Dark Mode
**What:** Class-based dark mode with toggle and persistence
**When to use:** UI-05 - Dark-themed status bar and overall theme
**Example:**
```css
/* ui/src/index.css */
@import "tailwindcss";

@custom-variant dark (&:is(.dark *));

@theme {
  --color-slate-dark: #1e1e2e;
  --color-teal-accent: #14b8a6;
}

@layer base {
  body {
    @apply bg-white dark:bg-slate-dark text-gray-900 dark:text-gray-100;
    transition: background-color 0.2s, color 0.2s;
  }
}
```

```typescript
// ui/src/context/ThemeContext.tsx
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem('theme');
    return (saved as Theme) || 'dark';
  });

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => setTheme(t => t === 'dark' ? 'light' : 'dark');

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}
```

### Pattern 4: System Stats Polling
**What:** Poll backend for system stats at regular intervals
**When to use:** UI-08 - Live system stats display (5 second updates)
**Example:**
```typescript
// ui/src/hooks/useSystemStats.ts
import { useState, useEffect } from 'react';

interface SystemStats {
  cpu: { percent: number };
  memory: { percent: number; used_gb: number; total_gb: number };
  vram?: { percent: number; used_gb: number; total_gb: number };
}

export function useSystemStats(pollIntervalMs: number = 5000) {
  const [stats, setStats] = useState<SystemStats | null>(null);

  useEffect(() => {
    let mounted = true;

    const fetchStats = async () => {
      try {
        const res = await fetch('/api/stats/current');
        if (mounted) {
          setStats(await res.json());
        }
      } catch (error) {
        console.error('Failed to fetch stats:', error);
      }
    };

    fetchStats();
    const interval = setInterval(fetchStats, pollIntervalMs);

    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [pollIntervalMs]);

  return stats;
}
```

### Pattern 5: Status Bar Component
**What:** Collapsible status bar showing CPU/Memory/VRAM
**When to use:** UI-05, UI-08
**Example:**
```tsx
// ui/src/components/StatusBar/StatusBar.tsx
import { useSystemStats } from '../../hooks/useSystemStats';
import { Cpu, HardDrive, MemoryStick } from 'lucide-react';

export function StatusBar() {
  const [collapsed, setCollapsed] = useState(false);
  const stats = useSystemStats(5000);

  return (
    <div className="border-t border-gray-700 bg-slate-800 dark:bg-slate-dark">
      <button 
        onClick={() => setCollapsed(!collapsed)}
        className="w-full px-4 py-1 flex items-center justify-between text-sm text-gray-400 hover:text-teal-400"
      >
        <span>System Status</span>
        <span>{collapsed ? '▲' : '▼'}</span>
      </button>
      
      {!collapsed && stats && (
        <div className="px-4 py-2 flex gap-6 text-sm">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-teal-400" />
            <span>CPU: {stats.cpu.percent.toFixed(1)}%</span>
          </div>
          <div className="flex items-center gap-2">
            <MemoryStick className="w-4 h-4 text-teal-400" />
            <span>RAM: {stats.memory.percent.toFixed(1)}%</span>
          </div>
          {stats.vram && (
            <div className="flex items-center gap-2">
              <HardDrive className="w-4 h-4 text-teal-400" />
              <span>VRAM: {stats.vram.percent.toFixed(1)}%</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

### Anti-Patterns to Avoid
- **Blocking WebSocket sends:** Always await WebSocket send operations
- **Memory leaks in streaming:** Clean up WebSocket on component unmount
- **Missing reconnection logic:** WebSocket connections can drop; implement exponential backoff
- **Synchronous state updates during streaming:** Use functional updates or refs for streaming text
- **No error boundaries:** React components can crash; wrap Chat in error boundary

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| WebSocket connection | Custom connection manager | FastAPI WebSocket + native JS | FastAPI has battle-tested starlette WebSocket |
| Icons | Custom SVG icons | lucide-react | Consistent, accessible, tree-shakeable |
| Theme toggle | Custom dark mode | Tailwind dark mode + context | Built into Tailwind, persisted in localStorage |
| Build tooling | CRA or custom webpack | Vite | Faster dev, better DX, standard in React ecosystem |

**Key insight:** The existing `brain/agent.py` already has a `stream_run()` method that yields (token, is_final) tuples. The UI backend just needs to pipe these to WebSocket clients.

## Common Pitfalls

### Pitfall 1: WebSocket Reconnection Race Conditions
**What goes wrong:** Multiple WebSocket connections created on rapid reconnection attempts
**Why it happens:** No debounce on reconnection, component remounts trigger new connections
**How to avoid:** Use a ref to track connection state, implement debounced reconnect with exponential backoff
**Warning signs:** "WebSocket connection already in progress" errors, multiple WS connections in network tab

### Pitfall 2: Streaming Text State Corruption
**What goes wrong:** Chat messages get jumbled when tokens arrive out of order or during rapid state updates
**Why it happens:** React state updates are async; multiple streaming messages can conflict
**How to avoid:** Use refs for current streaming message, update final message only on 'done' event
**Warning signs:** Messages appearing with missing/changed characters, console warnings about state updates

### Pitfall 3: Tailwind Dark Mode Not Working
**What goes wrong:** Dark mode classes don't apply even with .dark class on html
**Why it happens:** Tailwind v4 requires explicit `@custom-variant dark` declaration
**How to avoid:** Add `@custom-variant dark (&:is(.dark *));` to index.css
**Warning signs:** No dark styling despite dark class present

### Pitfall 4: CORS Blocking WebSocket
**What goes wrong:** WebSocket fails to connect, no error or cryptic error
**Why it happens:** FastAPI CORS middleware doesn't cover WebSocket by default
**How to avoid:** Configure CORS with allow_origins for WebSocket upgrade requests
**Warning signs:** "Connection closed before upgrade" in browser console

## Code Examples

### FastAPI with CORS and WebSocket
```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize connections
    yield
    # Shutdown: cleanup

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### React Chat Component with Streaming
```tsx
// ui/src/components/Chat/ChatWindow.tsx
import { useChatWebSocket } from '../../hooks/useChatWebSocket';
import { motion } from 'framer-motion';  // For animated dots

export function ChatWindow() {
  const { messages, isStreaming, sendMessage, connectionStatus } = useChatWebSocket('ws://localhost:8000/ws/chat');
  const [input, setInput] = useState('');

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map(msg => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[70%] rounded-lg px-4 py-2 ${
              msg.role === 'user' 
                ? 'bg-teal-600 text-white' 
                : 'bg-slate-700 text-gray-100'
            }`}>
              {msg.content}
              {msg.id.includes('_streaming') && isStreaming && (
                <span className="animate-pulse">▊</span>
              )}
            </div>
          </div>
        ))}
        {isStreaming && !messages.some(m => m.id.includes('_streaming')) && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex gap-1"
          >
            <span className="w-2 h-2 bg-teal-400 rounded-full animate-bounce" />
            <span className="w-2 h-2 bg-teal-400 rounded-full animate-bounce [animation-delay:0.1s]" />
            <span className="w-2 h-2 bg-teal-400 rounded-full animate-bounce [animation-delay:0.2s]" />
          </motion.div>
        )}
      </div>
      
      <form onSubmit={handleSubmit} className="border-t border-gray-700 p-4">
        <input
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder="Type a message..."
          className="w-full bg-slate-800 border border-gray-600 rounded-lg px-4 py-2 text-white focus:border-teal-400 focus:outline-none"
        />
      </form>
    </div>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| REST polling for chat | WebSocket streaming | 2023+ | Real-time token display |
| CRA (Create React App) | Vite | 2021+ | 10x faster dev server |
| Tailwind v3 config | Tailwind v4 @theme | 2024 | CSS-first configuration |
| Socket.io | Native WebSocket / SSE | 2022+ | Simpler, less overhead |

**Deprecated/outdated:**
- **Socket.io for this use case:** Overkill for one-way token streaming; native WebSocket or SSE suffices
- **Create React App:** Slow dev server, maintenance issues; Vite is standard now

## Open Questions

1. **VRAM Detection on Windows**
   - What we know: tools/system_monitor.py uses psutil for CPU/memory; nvidia-ml-py for GPU
   - What's unclear: Whether VRAM detection works reliably on all Windows configs
   - Recommendation: Add graceful fallback in UI if vram endpoint returns null

2. **Voice State WebSocket Events**
   - What we know: CONTEXT.md specifies voice.state WebSocket event
   - What's unclear: Exact voice state values to broadcast (listening, speaking, idle)
   - Recommendation: Define voice state enum early; integrate with voice pipeline

3. **Production CORS Origins**
   - What we know: "Specific origins" per CONTEXT.md
   - What's unclear: What origins in production?
   - Recommendation: Use environment variable for allowed origins; default to localhost dev

## Sources

### Primary (HIGH confidence)
- FastAPI WebSocket docs: https://fastapi.tiangolo.com/advanced/websockets/
- Tailwind CSS v4 dark mode: https://tailwindcss.com/docs/dark-mode
- react-use-websocket npm: https://www.npmjs.com/package/react-use-websocket
- Vite React setup: https://vitejs.dev/guide/

### Secondary (MEDIUM confidence)
- FastAPI + React streaming: https://medium.com/@o39joey/full-stack-rag-streaming-with-fastapi-react-part-2
- SSE for LLM streaming: https://medium.com/@hadiyolworld007/fastapi-sse-for-llm-tokens-smooth-streaming-without-websockets
- Stock market dashboard reference: https://github.com/joravetz/stock-market-dashboard

### Tertiary (LOW confidence)
- Various web tutorials on FastAPI WebSocket - needs validation for production use

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Technologies are well-established, already in requirements.txt
- Architecture: HIGH - Patterns from existing codebase (agent.py stream_run, system_monitor.py)
- Pitfalls: MEDIUM - Identified common issues but haven't tested in this specific project

**Research date:** 2026-03-04
**Valid until:** 2026-04-04 (30 days for stable stack)
