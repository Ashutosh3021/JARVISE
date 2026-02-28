---
phase: 02-core-hardware
plan: 01
type: execute
wave: 1
depends_on: []
files_modified: [core/hardware.py]
autonomous: true
requirements: [HW-01]
---

<objective>
Create hardware detection module that detects CPU cores, GPU name, and VRAM at startup.
</objective>

<context>
@.planning/phases/02-core-hardware/02-RESEARCH.md
@requirements.txt
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create hardware detection module</name>
  <files>core/hardware.py</files>
  <action>
Create core/hardware.py with:
- HardwareInfo dataclass with fields: cpu_physical_cores, cpu_logical_cores, cpu_freq_mhz, vram_total_mb, gpu_name, has_nvidia, has_amd
- detect_hardware() function that:
  - Uses psutil for CPU info (physical/logical cores, frequency)
  - Tries nvidia-ml-py (pynvml) first for NVIDIA GPU/VRAM detection
  - Falls back to gpu-list for AMD/Intel GPU detection
  - Returns HardwareInfo with all detected data
- Export HardwareInfo and detect_hardware
  </action>
  <verify>
python -c "from core.hardware import detect_hardware; hw = detect_hardware(); print(f'CPU: {hw.cpu_logical_cores} cores, GPU: {hw.gpu_name}, VRAM: {hw.vram_total_mb}MB')"
  </verify>
  <done>Hardware detection runs without errors and returns CPU/GPU/VRAM info</done>
</task>

</tasks>

<verification>
- [ ] core/hardware.py exists with HardwareInfo dataclass
- [ ] detect_hardware() function is importable and runs
- [ ] Function outputs CPU cores, GPU name, and VRAM amount
</verification>

<success_criteria>
Application can report detected hardware (CPU cores, GPU name, VRAM amount) at startup.
</success_criteria>

<output>
After completion, create .planning/phases/02-core-hardware/02-01-SUMMARY.md
</output>
