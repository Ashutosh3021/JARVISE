# JARVISE — PyPI Deployment Guide

> First-time publish checklist for `jarvise` on PyPI.

---

## Prerequisites

- [ ] Python 3.11+ installed
- [ ] Ollama installed and working (`ollama list` shows models)
- [ ] PyPI account created at [pypi.org](https://pypi.org)
- [ ] PyPI API token generated (Account Settings → API Tokens)

---

## Step 1 — Run the pre-publish prompt

Paste the pre-publish prompt into your AI coding tool with the full codebase.
Wait for all 8 steps to complete and show PASSED on twine check.

---

## Step 2 — Create PyPI account and token

1. Go to [pypi.org](https://pypi.org) → Register
2. Verify your email
3. Go to **Account Settings → API Tokens → Add API Token**
4. Name: `jarvise-publish`
5. Scope: Entire account (first time)
6. Copy the token — starts with `pypi-`
7. Save it somewhere safe — you only see it once

---

## Step 3 — Build the package

```bash
# Make sure you're in the project root
cd C:\Users\ashut\Downloads\OnGoingProjects\JARVISE

# Activate venv
.venv\Scripts\activate

# Clean previous builds
rmdir /s /q dist build
rmdir /s /q jarvise.egg-info

# Build
python -m build
```

Expected output:
```
Successfully built jarvise-1.0.0.tar.gz and jarvise-1.0.0-py3-none-any.whl
```

---

## Step 4 — Verify the build

```bash
python -m twine check dist/*
```

Expected output:
```
Checking dist/jarvise-1.0.0-py3-none-any.whl: PASSED
Checking dist/jarvise-1.0.0.tar.gz: PASSED
```

If any FAILED — fix the error, rebuild, recheck before proceeding.

---

## Step 5 — Publish to PyPI

```bash
python -m twine upload dist/*
```

When prompted:
```
Enter your username: __token__
Enter your password: pypi-xxxxxxxxxxxx  (paste your token here)
```

Expected output:
```
Uploading jarvise-1.0.0-py3-none-any.whl
Uploading jarvise-1.0.0.tar.gz
View at: https://pypi.org/project/jarvise/1.0.0/
```

---

## Step 6 — Verify the publish

```bash
# Wait 2-3 minutes after upload, then:
pip install jarvise
```

Or check directly: [pypi.org/project/jarvise](https://pypi.org/project/jarvise)

---

## Step 7 — Test the install

```bash
# In a fresh directory with a clean venv
python -m venv test-env
test-env\Scripts\activate
pip install jarvise

# Run it
jarvis --text-only
```

---

## Publishing updates (future versions)

```bash
# 1. Update version in pyproject.toml (e.g. 1.0.1)
# 2. Clean and rebuild
rmdir /s /q dist build
python -m build

# 3. Upload
python -m twine upload dist/*
```

PyPI does not allow re-uploading the same version.
Always bump the version before uploading.

---

## Install options (for README / users)

```bash
# Core only (text + API, no voice)
pip install jarvise

# With voice (Whisper STT + Kokoro TTS)
pip install jarvise[voice]

# With Google Calendar / Gmail tools
pip install jarvise[google]

# With Microsoft Outlook tools
pip install jarvise[microsoft]

# Everything
pip install jarvise[all]
```

---

## Common errors

| Error | Fix |
|-------|-----|
| `File already exists` | Bump version in pyproject.toml |
| `Invalid distribution` | Run `twine check dist/*` and fix warnings |
| `403 Forbidden` | Wrong token or username not `__token__` |
| `No matching distribution` | Package not uploaded yet, wait 2-3 mins |
| `jarvis command not found` | Entry point broken, check pyproject.toml scripts |

---

*Last updated: May 2026*