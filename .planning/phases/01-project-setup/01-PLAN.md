---
phase: 01-project-setup
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: []
autonomous: true
requirements: ["PS-01", "PS-02", "PS-03", "PS-04", "PS-05"]

must_haves:
  truths:
    - "Developer can run `pip install -e .` and get all dependencies installed without errors"
    - "`.env` file can be created from `.env.example` template and loaded successfully"
    - "Project directory structure exists with all required folders (core/, voice/, brain/, memory/, tools/, ui/, data/, tests/)"
  artifacts:
    - path: "requirements.txt"
      provides: "Pinned Python dependencies"
    - path: "setup.py"
      provides: "Virtual environment setup and package installation"
    - path: ".env.example"
      provides: "API keys and configuration template"
    - path: ".gitignore"
      provides: "Git ignore rules for sensitive files"
    - path: "core/"
      provides: "Core module directory"
    - path: "voice/"
      provides: "Voice pipeline module directory"
    - path: "brain/"
      provides: "Brain layer module directory"
    - path: "memory/"
      provides: "Memory system module directory"
    - path: "tools/"
      provides: "System tools module directory"
    - path: "ui/"
      provides: "UI layer module directory"
    - path: "data/"
      provides: "Data storage directory"
    - path: "tests/"
      provides: "Test suite directory"
  key_links:
    - from: "setup.py"
      to: "requirements.txt"
      via: "install_requires"
      pattern: "install_requires=.*requirements"
---

<objective>
Scaffold the JARVIS project with directory structure, dependencies, and configuration templates.

Purpose: Establish the foundation for the entire project with proper Python packaging, environment configuration, and organized module structure.

Output: Complete project skeleton with all required directories, requirements.txt, setup.py, .env.example, and .gitignore.
</objective>

<execution_context>
@C:/Users/ashut/.config/opencode/get-shit-done/workflows/execute-plan.md
@C:/Users/ashut/.config/opencode/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/ROADMAP.md
@.planning/REQUIREMENTS.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create project directory structure</name>
  <files>core/__init__.py, voice/__init__.py, brain/__init__.py, memory/__init__.py, tools/__init__.py, ui/__init__.py, data/.gitkeep, tests/__init__.py</files>
  <action>
    Create the following directory structure with empty __init__.py files:
    - core/ - Core hardware detection and configuration
    - voice/ - Voice input/output pipeline (STT, TTS, wake word)
    - brain/ - LLM client and ReAct agent
    - memory/ - ChromaDB and MEMORY.md storage
    - tools/ - System tool integrations
    - ui/ - FastAPI + React web interface
    - data/ - Data storage (vector DB, audio files)
    - tests/ - Unit and integration tests
    
    Also create data/.gitkeep to preserve the data directory in git.
  </action>
  <verify>
    <automated>ls -la && ls -la core/ voice/ brain/ memory/ tools/ ui/ data/ tests/</automated>
  </verify>
  <done>All 8 directories exist with __init__.py files in Python package directories</done>
</task>

<task type="auto">
  <name>Task 2: Create requirements.txt with dependencies</name>
  <files>requirements.txt</files>
  <action>
    Create requirements.txt with pinned Python dependencies for the JARVIS project:
    
    Core dependencies:
    - pydantic>=2.0.0
    - python-dotenv>=1.0.0
    - pyyaml>=6.0.0
    
    Voice (STT/TTS):
    - faster-whisper>=1.0.0
    - kokoro>=0.9.0
    - sounddevice>=0.4.0
    - numpy>=1.24.0
    
    LLM:
    - ollama>=0.1.0
    
    Memory:
    - chromadb>=0.4.0
    - sentence-transformers>=2.2.0
    
    Tools:
    - playwright>=1.40.0
    - google-api-python-client>=2.100.0
    - msgraph-sdk>=1.0.0
    
    UI:
    - fastapi>=0.109.0
    - uvicorn[standard]>=0.27.0
    - websockets>=12.0.0
    - python-multipart>=0.0.6
    
    Testing:
    - pytest>=8.0.0
    - pytest-asyncio>=0.23.0
    - pytest-cov>=4.1.0
    
    Utilities:
    - loguru>=0.7.0
    - aiofiles>=23.2.0
    - httpx>=0.26.0
  </action>
  <verify>
    <automated>cat requirements.txt | head -30</automated>
  </verify>
  <done>requirements.txt exists with all major dependencies listed</done>
</task>

<task type="auto">
  <name>Task 3: Create setup.py for installation</name>
  <files>setup.py</files>
  <action>
    Create setup.py with:
    - Package name: jarvis
    - Version: 0.1.0
    - Description: Windows AI Voice Assistant
    - Author: Developer
    - Python requires: >=3.11
    - install_requires reading from requirements.txt
    - packages=find_packages()
    - include_package_data=True for data files
    - Entry points for console script if needed
  </action>
  <verify>
    <automated>cat setup.py</automated>
  </verify>
  <done>setup.py exists and is valid Python</done>
</task>

<task type="auto">
  <name>Task 4: Create .env.example template</name>
  <files>.env.example</files>
  <action>
    Create .env.example with all required configuration:
    
    # Ollama Configuration
    OLLAMA_HOST=http://localhost:11434
    OLLAMA_MODEL=llama3.2:latest
    
    # Voice Configuration
    WAKE_WORD=jarvis
    WHISPER_MODEL=base
    KOKORO_VOICE=af_sarah
    TTS_SPEED=1.0
    
    # Memory Configuration
    CHROMA_PERSIST_DIRECTORY=./data/chromadb
    MEMORY_FILE=./data/MEMORY.md
    
    # UI Configuration
    UI_HOST=0.0.0.0
    UI_PORT=8000
    
    # Google Calendar (optional)
    GOOGLE_CALENDAR_CREDS_PATH=
    
    # Google Email (optional)
    GOOGLE_EMAIL_CREDS_PATH=
    
    # Microsoft Outlook (optional)
    OUTLOOK_CREDS_PATH=
    
    # Logging
    LOG_LEVEL=INFO
    LOG_FILE=./data/jarvis.log
  </action>
  <verify>
    <automated>cat .env.example</automated>
  </verify>
  <done>.env.example exists with all configuration keys documented</done>
</task>

<task type="auto">
  <name>Task 5: Create .gitignore</name>
  <files>.gitignore</files>
  <action>
    Create .gitignore with:
    
    # Environment
    .env
    .env.local
    
    # Python
    __pycache__/
    *.py[cod]
    *$py.class
    *.so
    .Python
    build/
    develop-eggs/
    dist/
    downloads/
    eggs/
    .eggs/
    lib/
    lib64/
    parts/
    sdist/
    var/
    wheels/
    *.egg-info/
    .installed.cfg
    *.egg
    
    # Virtual environments
    venv/
    env/
    .venv/
    
    # IDE
    .vscode/
    .idea/
    *.swp
    *.swo
    
    # Data and models
    data/chromadb/
    data/*.db
    data/*.log
    models/
    *.bin
    *.onnx
    
    # OS
    .DS_Store
    Thumbs.db
    
    # Testing
    .pytest_cache/
    .coverage
    htmlcov/
  </action>
  <verify>
    <automated>cat .gitignore</automated>
  </verify>
  <done>.gitignore exists with proper exclusions for .env, cache, and model directories</done>
</task>

</tasks>

<verification>
1. Verify directory structure: `ls -la` shows all 8 directories (core, voice, brain, memory, tools, ui, data, tests)
2. Verify requirements.txt: File exists with all dependencies
3. Verify setup.py: File is valid Python and reads requirements.txt
4. Verify .env.example: File contains all configuration keys
5. Verify .gitignore: File excludes .env, data/, models/, __pycache__/
</verification>

<success_criteria>
1. Developer can run `pip install -e .` and get all dependencies installed without errors
2. `.env` file can be created from `.env.example` template and loaded successfully
3. Project directory structure exists with all required folders (core/, voice/, brain/, memory/, tools/, ui/, data/, tests/)
</success_criteria>

<output>
After completion, create `.planning/phases/01-project-setup/01-01-SUMMARY.md`
</output>
