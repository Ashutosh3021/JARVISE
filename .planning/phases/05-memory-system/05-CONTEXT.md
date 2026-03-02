# Phase 5: Memory System - Context

**Gathered:** 2026-03-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Persistent vector and file-based memory storage. ChromaDB for conversation embeddings, MEMORY.md for permanent facts. MemoryManager unifies both. Provides context retrieval for LLM prompts. Integrates with Brain (Phase 4) and enables system tools (Phase 6).

</domain>

<decisions>
## Implementation Decisions

### Vector Storage
- **Data embedded**: Conversations + important facts
- Conversations get embedded after each exchange
- Important facts extracted and stored separately
- ChromaDB as vector database (per requirements)

### Context Retrieval
- **Method**: Semantic similarity search
- Use ChromaDB's native similarity search
- Retrieve top-K most relevant memories based on query
- Feed retrieved context to prompt builder for LLM

### Memory Persistence
- **Retention**: Last 30 days + important facts
- Conversations older than 30 days archived (not deleted, just not in active vector store)
- Important facts persist indefinitely
- Summary of older conversations kept in MEMORY.md

### File vs Vector Balance
- **MEMORY.md**: Permanent facts, user preferences, ongoing tasks, user profile
- **ChromaDB**: Recent conversations, semantic context
- Human-editable content goes to MEMORY.md
- Machine-queryable content goes to ChromaDB

### Claude's Discretion
- Exact embedding model choice (all-MiniLM-L6-v2 or similar)
- Chunk size for conversations
- Number of memories to retrieve (top-K value)
- How to extract "important facts" from conversation

</decisions>

<specifics>
## Specific Ideas

- "Remember previous sessions via MEMORY.md" — From Phase 4 discussion
- Persistent cross-session memory for user preferences and facts
- Semantic search for relevant context retrieval

</specifics>

# Existing Code Insights

### Reusable Assets
- `brain/prompt_builder.py` — Already has memory_context parameter for injecting context
- `core/config.py` — Has chroma_persist_directory and memory_file settings
- `core/logger.py` — Can be used for memory system logging

### Established Patterns
- Phase 2: Configuration via pydantic-settings
- Phase 3: Voice pipeline with TTS
- Phase 4: Brain layer with ReAct agent

### Integration Points
- Input: Brain layer (Phase 4) — receives memory context for prompts
- Output: Brain layer — returns extracted facts for storage
- Storage: ChromaDB + MEMORY.md file

</code_context>

<deferred>
## Deferred Ideas

- Conversation summarization for very long sessions (future enhancement)
- Memory encryption at rest (security enhancement)
- Export/import memory backup (utility feature)

</deferred>

---

*Phase: 05-memory-system*
*Context gathered: 2026-03-01*
