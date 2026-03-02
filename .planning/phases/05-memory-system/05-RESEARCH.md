# Phase 5: Memory System - Research

**Phase:** 05-memory-system  
**Status:** Research  
**Requirement IDs:** MS-01, MS-02, MS-03, MS-04

---

## 1. What Is Phase 5?

Two-tier persistent memory system combining:
- **Vector storage** (ChromaDB): Semantic search for recent conversations
- **File storage** (MEMORY.md): Human-editable permanent facts/preferences

**Integration:**
- Input: Brain layer returns extracted facts for storage
- Output: Memory context retrieved for LLM prompts
- Storage: ChromaDB + MEMORY.md file

---

## 2. Requirement Analysis

### MS-01: ChromaDB Vector Store
- Store conversation embeddings for semantic similarity search
- Persistent storage at `./data/chromadb` (already configured in config.py)
- Collection: `conversations` with metadata (timestamp, user_query, assistant_response)

### MS-02: MEMORY.md Controller
- Read/write operations for permanent facts
- File path: `./data/MEMORY.md` (already configured)
- Template sections: User Profile, Preferences, Important Facts, Ongoing Tasks

### MS-03: MemoryManager Unification
- Single interface exposing both storage types
- `get_context(query)` - retrieve relevant memories
- `save_conversation()` - embed and store exchange
- `save_fact()` - update MEMORY.md

### MS-04: Template MEMORY.md
- Initialize with proper sections
- Human-editable format (markdown)

---

## 3. Technical Implementation

### 3.1 ChromaDB Setup

**Dependencies** (already in requirements.txt):
- `chromadb>=0.4.0`
- Need to add: `sentence-transformers` for embeddings

**Embedding Model:**
- Default: `all-MiniLM-L6-v2` (fast, 384-dim, good quality)
- Alternative: `all-mpnet-base-v2` (slower, 768-dim, better quality)

**Chunk Strategy:**
- Conversations: Store each exchange as single document
- Format: "User: [query]\nAssistant: [response]"
- Metadata: timestamp, session_id, importance_flag

```python
# client setup (PersistentClient for disk persistence)
client = chromadb.PersistentClient(path="./data/chromadb")

# collection with embedding function
embedding_fn = SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_or_create_collection(
    name="conversations",
    embedding_function=embedding_fn
)
```

### 3.2 MEMORY.md Structure

```markdown
# JARVIS Memory

## User Profile
- Name: [user name]
- Role: [occupation/role]

## Preferences
- Communication style: [formal/casual]
- Voice speed: [slow/normal/fast]
- Topics to avoid: [list]

## Important Facts
- [fact 1]
- [fact 2]

## Ongoing Tasks
- [ ] Task 1
- [ ] Task 2

## Notes
[Any additional context]
```

### 3.3 MemoryManager API Design

```python
class MemoryManager:
    def __init__(self, config: Config): ...
    
    # Context retrieval
    def get_context(self, query: str, top_k: int = 5) -> dict[str, str]:
        """Get relevant memories: memory_context + vector_context"""
    
    # Conversation storage
    def save_conversation(self, user_query: str, assistant_response: str) -> None:
        """Embed and store conversation exchange"""
    
    # Fact management
    def save_fact(self, fact: str, category: str = "important_facts") -> None:
        """Add fact to MEMORY.md"""
    
    def update_memory(self, section: str, content: str) -> None:
        """Update specific MEMORY.md section"""
    
    def get_memory(self) -> str:
        """Get full MEMORY.md content"""
```

### 3.4 Context Retrieval Flow

1. Query MEMORY.md → `memory_context` (full file)
2. Query ChromaDB → `vector_context` (semantic similarity)
3. Combine → inject into PromptBuilder

---

## 4. Key Decisions to Make

| Decision | Options | Recommendation |
|----------|---------|----------------|
| Embedding model | all-MiniLM-L6-v2 / all-mpnet-base-v2 | all-MiniLM-L6-v2 (faster) |
| Top-K results | 3-10 | 5 (good balance) |
| Conversation retention | 30 days / 90 days | 30 days per context |
| Memory archiving | Delete / Archive to file | Archive summaries to MEMORY.md |
| Importance extraction | LLM-based / Heuristic | LLM-based (defer to Phase 6) |

---

## 5. File Structure

```
memory/
├── __init__.py           # MemoryManager export
├── chroma_store.py       # Vector store wrapper
├── memory_file.py        # MEMORY.md controller
└── MEMORY.md            # Template (created on init)
```

---

## 6. Integration Points

| Component | File | Integration |
|-----------|------|-------------|
| Config | core/config.py | Already has chroma_persist_directory, memory_file |
| PromptBuilder | brain/prompt_builder.py | Already has memory_context, vector_context params |
| Logger | core/logger.py | Use for memory operations logging |

---

## 7. Testing Strategy

- Unit tests for MemoryManager methods
- Mock ChromaDB client for testing
- Test MEMORY.md read/write operations
- Integration test: full context retrieval

---

## 8. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| ChromaDB version breaking changes | Pin to 0.4.x, test on upgrade |
| Large vector store slow query | Use HNSW index (default), limit top_k |
| MEMORY.md file corruption | Keep backup, validate on read |
| Embedding model download | Bundle or download at first run |

---

## 9. Next Steps

1. Add `sentence-transformers` to requirements.txt
2. Create `memory/chroma_store.py` - VectorStore class
3. Create `memory/memory_file.py` - MemoryFileController class
4. Create `memory/MemoryManager.py` - unified interface
5. Create `memory/MEMORY.md` template
6. Write unit tests
7. Verify integration with PromptBuilder

---

*Research completed: 2026-03-02*
