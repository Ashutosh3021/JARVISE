---
phase: 02-core-hardware
plan: 03
type: execute
wave: 1
depends_on: []
files_modified: [core/logger.py]
autonomous: true
requirements: [HW-04]
---

<objective>
Create centralized logging system with console and file output using loguru.
</objective>

<context>
@.planning/phases/02-core-hardware/02-RESEARCH.md
@requirements.txt
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create logging module with loguru</name>
  <files>core/logger.py</files>
  <action>
Create core/logger.py with:
- setup_logging(log_level: str, log_file: str) function that:
  - Removes default loguru handler
  - Adds console handler with colored format: "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
  - Adds file handler with format: "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
  - File rotation at midnight, retention 7 days, compression to zip
  - Creates log directory if it doesn't exist
- Export setup_logging and import logger from loguru for use throughout app
  </action>
  <verify>
python -c "from core.logger import setup_logging; setup_logging('INFO', './data/test.log'); from loguru import logger; logger.info('Test message')"
  </verify>
  <done>Logging system writes to both console and file with proper formatting</done>
</task>

</tasks>

<verification>
- [ ] core/logger.py exists with setup_logging function
- [ ] Console output shows colored logs with timestamp and level
- [ ] File output is written to ./data/ directory
- [ ] Log rotation and retention configured
</verification>

<success_criteria>
Logs are written to both console and file with proper formatting.
</success_criteria>

<output>
After completion, create .planning/phases/02-core-hardware/02-03-SUMMARY.md
</output>
