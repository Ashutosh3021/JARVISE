# Phase 7: UI Layer - Context

**Gathered:** 2026-03-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Web interface for JARVIS monitoring and control — FastAPI backend with React SPA, dark theme, WebSocket streaming, system stats display. This phase creates the user-facing web UI that interacts with the existing backend components (brain, voice, memory, tools).

</domain>

<decisions>
## Implementation Decisions

### Layout & Navigation
- **Page structure:** Single-page with panels — Main chat area + collapsible sidebar
- **Navigation:** Sidebar navigation — Icons + labels on left side
- **Views:** Single page app — All features accessible from one screen
- **Responsive:** Fully responsive — Same experience on all devices

### Theme & Styling
- **Color scheme:** Slate dark (#1e1e2e) — Purple-tinted, modern feel
- **Styling:** Tailwind CSS — Utility classes, rapid development
- **Accent color:** Teal (#14b8a6) — JARVIS-y, futuristic
- **Light/dark mode:** Toggle in UI — User can switch manually

### Chat Interface
- **Message style:** Standard bubbles — User right, JARVIS left with avatars
- **Streaming:** Chunk reveal — Words appear at a time
- **Input controls:** Full toolbar — Text, voice, file upload, emoji picker
- **Thinking state:** Animated dots — Pulsing animation

### Status Bar
- **Stats:** CPU, Memory, VRAM — Core metrics
- **Position:** Collapsible — Can hide/show with toggle
- **Update frequency:** Every 5 seconds — Balanced
- **Extra info:** All — Connection status, model in use, session info

### API & WebSocket
- **WebSocket events:** chat.stream, system.stats, voice.state
- **REST API:** Hybrid — REST for CRUD, WebSocket for streaming
- **Authentication:** No auth — Local only, no authentication
- **CORS:** Specific origins — Production-ready

### Claude's Discretion
- Exact component library choices (Radix UI, Headless UI, etc.)
- Exact Tailwind config values
- WebSocket reconnection strategy
- Error boundary implementation

</decisions>

<specifics>
## Specific Ideas

- Sidebar should be collapsible to maximize chat area
- JARVIS avatar on left, user avatar on right in chat bubbles
- Teal accent color for buttons, links, and active states
- Status bar at bottom with toggle button to collapse/expand

</specifics>

## Existing Code Insights

### Reusable Assets
- requirements.txt: fastapi, uvicorn, websockets already listed
- tools/: System monitor tool from Phase 6 can provide CPU/Memory/VRAM stats

### Integration Points
- UI backend connects to brain/agent.py for chat
- UI connects to voice/ for voice state
- UI connects to memory/ for memory context
- UI connects to tools/ for system stats

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-ui-layer*
*Context gathered: 2026-03-02*
