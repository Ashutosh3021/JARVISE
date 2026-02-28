---
phase: 02-core-hardware
plan: 02
type: execute
wave: 1
depends_on: []
files_modified: [core/config.py]
autonomous: true
requirements: [HW-02, HW-03]
---

<objective>
Create configuration system with .env loading and automatic profile selection based on VRAM.
</objective>

<context>
@.planning/phases/02-core-hardware/02-RESEARCH.md
@.env.example
@requirements.txt
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create configuration module with pydantic-settings</name>
  <files>core/config.py</files>
  <action>
Create core/config.py with:
- Profile enum: CPU, LOW_GPU, MID_GPU, HIGH_GPU
- Config class using pydantic-settings BaseSettings with:
  - ollama_host (default: "http://localhost:11434")
  - ollama_model (default: "llama3.2:latest")
  - wake_word (default: "jarvis")
  - whisper_model (default: "base")
  - kokoro_voice (default: "af_sarah")
  - tts_speed (default: 1.0)
  - chroma_persist_directory (default: "./data/chromadb")
  - memory_file (default: "./data/MEMORY.md")
  - ui_host (default: "0.0.0.0")
  - ui_port (default: 8000)
  - log_level (default: "INFO")
  - log_file (default: "./data/jarvis.log")
  - vram_mb (default: 0) - set at runtime
  - profile (default: Profile.CPU) - set at runtime
- select_profile() method with thresholds: CPU (<2GB), LOW_GPU (2-4GB), MID_GPU (4-8GB), HIGH_GPU (>8GB)
- load_config() function that creates Config and selects profile
- Export Config, Profile, load_config
  </action>
  <verify>
python -c "from core.config import load_config, Profile; c = load_config(); print(f'Profile: {c.profile.value}')"
  </verify>
  <done>Config loads from .env (or defaults), profile selection works based on VRAM thresholds</done>
</task>

</tasks>

<verification>
- [ ] core/config.py exists with Config class
- [ ] Config can load from .env file
- [ ] select_profile() correctly applies VRAM thresholds
- [ ] Profile enum has CPU, LOW_GPU, MID_GPU, HIGH_GPU values
</verification>

<success_criteria>
Configuration profile is automatically selected based on VRAM (CPU/Low GPU/Mid GPU/High GPU).
</success_criteria>

<output>
After completion, create .planning/phases/02-core-hardware/02-02-SUMMARY.md
</output>
