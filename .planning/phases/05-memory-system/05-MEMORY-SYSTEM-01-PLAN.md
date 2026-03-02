---
phase: "05-memory-system"
plan: "01"
type: "execute"
wave: 1
depends_on: []
files_modified:
  - memory/__init__.py
  - memory/chroma_store.py
  - memory/memory_file.py
  - memory/MemoryManager.py
  - memory/MEMORY.md
  - requirements.txt
autonomous: true
requirements:
  - MS-01
  - MS-02
  - MS-03
  - MS-04
must_haves:
  truths:
    - Conversations are embedded and stored in ChromaDB vector store
    - MEMORY.md file can be read and written by the system
    - Relevant context is retrieved from memory for LLM prompts
  artifacts:
    - memory/chroma_store.py - VectorStore class for ChromaDB
    - memory/memory_file.py - MemoryFileController for MEMORY.md
    - memory/MemoryManager.py - Unified interface for both storage types
    - memory/MEMORY.md - Template file with sections
    - memory/__init__.py - Module exports
  key_links:
    - "MemoryManager → brain/prompt_builder.py: Provides memory_context and vector_context"
    - "memory/chroma_store.py → core/config.py: Uses chroma_persist_directory setting"
    - "memory/memory_file.py → core/config.py: Uses memory_file setting"
---

<?xml version="1.0" encoding="UTF-8"?>
<tasks>
  <task>
    <id>MS-01-01</id>
    <description>Create memory/chroma_store.py - VectorStore class for ChromaDB</description>
    <priority>critical</priority>
    <requirements>MS-01</requirements>
    <verification>
      <criteria>VectorStore can embed and store conversations, retrieve by similarity</criteria>
      <test_commands>python -c "from memory.chroma_store import VectorStore; v = VectorStore('./data/chromadb'); v.save_conversation('test query', 'test response'); print(v.get_context('test', 3))"</test_commands>
    </verification>
    <must_haves>
      <item>VectorStore class with PersistentClient initialization</item>
      <item>save_conversation() method embedding user/assistant exchange</item>
      <item>get_context() method for similarity search retrieval</item>
      <item>Collection: conversations with timestamp, session_id metadata</item>
      <item>Embedding model: all-MiniLM-L6-v2</item>
    </must_haves>
  </task>

  <task>
    <id>MS-01-02</id>
    <description>Create memory/memory_file.py - MemoryFileController for MEMORY.md</description>
    <priority>critical</priority>
    <requirements>MS-02,MS-04</requirements>
    <verification>
      <criteria>MemoryFileController can read, write, and update MEMORY.md sections</criteria>
      <test_commands>python -c "from memory.memory_file import MemoryFileController; c = MemoryFileController('./data/MEMORY.md'); print(c.get_section('User Profile'))"</test_commands>
    </verification>
    <must_haves>
      <item>MemoryFileController class with file path initialization</item>
      <item>get_section() method for reading specific sections</item>
      <item>update_section() method for writing to sections</item>
      <item>get_full_content() method returning entire MEMORY.md</item>
      <item>save_fact() method for adding facts to Important Facts section</item>
    </must_haves>
  </task>

  <task>
    <id>MS-01-03</id>
    <description>Create memory/MemoryManager.py - Unified interface for vector and file storage</description>
    <priority>critical</priority>
    <requirements>MS-03</requirements>
    <verification>
      <criteria>MemoryManager unifies VectorStore and MemoryFileController, provides get_context()</criteria>
      <test_commands>python -c "from memory.MemoryManager import MemoryManager; from core.config import Config; m = MemoryManager(Config()); print(type(m))"</test_commands>
    </verification>
    <must_haves>
      <item>MemoryManager class wrapping VectorStore and MemoryFileController</item>
      <item>get_context() method combining file and vector context</item>
      <item>save_conversation() delegates to VectorStore</item>
      <item>save_fact() delegates to MemoryFileController</item>
      <item>Accepts Config from core/config.py in __init__</item>
    </must_haves>
  </task>

  <task>
    <id>MS-01-04</id>
    <description>Create memory/MEMORY.md template and update memory/__init__.py</description>
    <priority>high</priority>
    <requirements>MS-04</requirements>
    <verification>
      <criteria>MEMORY.md template exists with required sections, __init__.py exports classes</criteria>
      <test_commands>python -c "from memory import MemoryManager; print('MemoryManager imported successfully')"</test_commands>
    </verification>
    <must_haves>
      <item>MEMORY.md with sections: User Profile, Preferences, Important Facts, Ongoing Tasks, Notes</item>
      <item>memory/__init__.py exports MemoryManager, VectorStore, MemoryFileController</item>
      <item>Auto-create MEMORY.md on first run if missing</item>
    </must_haves>
  </task>
</tasks>
