---
phase: 06-system-tool-integrations
plan: 02
subsystem: auth, google_integration
tags: [oauth2, google-calendar, gmail, encryption, token-storage]
dependency_graph:
  requires:
    - 06-01 (core tools must exist)
  provides:
    - ST-05: Google Calendar integration
    - ST-06: Google Email integration
  affects:
    - tools/__init__.py
    - requirements.txt
tech_stack:
  added:
    - google-auth-oauthlib
    - cryptography
  patterns:
    - Fernet symmetric encryption for token storage
    - OAuth2 CLI flow with access_type='offline'
    - Separate token storage per provider (google, google_gmail)
key_files:
  created:
    - tools/auth/__init__.py
    - tools/auth/token_manager.py
    - tools/auth/oauth.py
    - tools/google_calendar.py
    - tools/google_email.py
  modified:
    - tools/__init__.py
    - requirements.txt
decisions:
  - Token storage: Encrypted JSON in data/tokens/ directory
  - Token refresh: Automatic using refresh_token grant
  - First-time auth: CLI-based flow (print URL, paste code)
  - Provider separation: google (Calendar) and google_gmail (Email)
---

# Phase 06 Plan 02: Google Integrations Summary

## Objective

Implement Google Calendar and Email integrations with OAuth2 authentication and encrypted token storage.

## Execution Summary

All 4 tasks completed successfully. The plan implements:

1. **Auth module with TokenManager** - Encrypted token storage using Fernet
2. **Google OAuth2 CLI flow helper** - Print URL, paste code flow
3. **Google Calendar tool (ST-05)** - Full CRUD for calendar events
4. **Google Email tool (ST-06)** - Read and send Gmail messages

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create auth module with TokenManager | 3ecba0b | tools/auth/__init__.py, tools/auth/token_manager.py |
| 2 | Implement Google OAuth2 flow helper | 770a269 | tools/auth/oauth.py |
| 3 | Implement Google Calendar tool (ST-05) | 9c9cfb2 | tools/google_calendar.py |
| 4 | Implement Google Email tool (ST-06) | d91166b | tools/google_email.py |

## Deviation from Plan

None - plan executed exactly as written.

## Auth Gates

No authentication gates encountered. The tools are implemented and ready but require user setup:

- **GOOGLE_CLIENT_SECRETS**: OAuth2 credentials from Google Cloud Console
- **API Enablement**: Calendar and Gmail APIs must be enabled in Google Cloud Console

## Usage

### First-time Authentication

1. Get OAuth2 credentials from Google Cloud Console
2. Enable Google Calendar API and Gmail API
3. Set `GOOGLE_CLIENT_SECRETS` env var or place client_secrets.json in data/
4. Run tool - it will print authorization URL
5. Visit URL, grant permissions, paste code

### Calendar Operations

```python
from tools.google_calendar import GoogleCalendarTool

calendar = GoogleCalendarTool()

# List events
result = calendar.execute("list", max_results=10)

# Create event
result = calendar.execute("create", 
    title="Meeting",
    start_time="2026-03-15T10:00:00Z",
    end_time="2026-03-15T11:00:00Z",
    description="Team sync"
)
```

### Email Operations

```python
from tools.google_email import GoogleEmailTool

email = GoogleEmailTool()

# List messages
result = email.execute("list", max_results=10, query="is:unread")

# Send message
result = email.execute("send",
    to="recipient@example.com",
    subject="Hello",
    body="Email body"
)
```

## Technical Details

- **Token Storage**: Encrypted with Fernet (AES 128), key stored in data/tokens/.key
- **Token Refresh**: Automatic via google-auth-oauthlib when access_token expires
- **Scopes**: 
  - Calendar: `https://www.googleapis.com/auth/calendar.events`, `calendar.readonly`
  - Gmail: `https://www.googleapis.com/auth/gmail.readonly`, `gmail.send`
- **Error Handling**: Detailed messages with suggestions per ToolError pattern
- **Logging**: Full logging via loguru with component binding

## Requirements Fulfilled

- [x] ST-05: Google Calendar integration with OAuth2
- [x] ST-06: Google Email integration with OAuth2
- [x] Encrypted token storage in data/
- [x] Automatic token refresh
- [x] CLI-based first-time auth flow
