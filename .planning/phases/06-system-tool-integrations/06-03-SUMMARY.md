---
phase: 06-system-tool-integrations
plan: 03
subsystem: tools
tags: [outlook, microsoft-graph, system-monitor, tool-registry]
dependency_graph:
  requires:
    - 06-01 (core tools)
    - 06-02 (Google auth module)
  provides:
    - ST-07: Microsoft Outlook integration
    - ST-08: System monitor tool
    - ST-09: Tool registry with all tools
  affects:
    - brain/tools.py
    - tools/__init__.py
tech_stack:
  added:
    - azure-identity (Microsoft auth)
    - msgraph-sdk (Microsoft Graph API)
  patterns:
    - DeviceCodeCredential for CLI OAuth2
    - GraphServiceClient for Microsoft Graph
    - psutil for system diagnostics
    - ToolRegistry with create_tools_registry()
key_files:
  created:
    - tools/auth/microsoft.py (MicrosoftAuth class)
    - tools/microsoft_outlook.py (MicrosoftOutlookTool)
    - tools/system_monitor.py (SystemMonitorTool)
  modified:
    - brain/tools.py (added create_tools_registry)
    - tools/__init__.py (added exports)
decisions:
  - CLI-based auth using DeviceCodeCredential
  - File-based token caching
  - Async support with callbacks
  - Full logging with loguru
  - Detailed error messages with suggestions
metrics:
  duration: ~5 minutes
  completed: 2026-03-02
---

# Phase 6 Plan 3: Microsoft Outlook + System Monitor + ToolRegistry Summary

## One-liner

Microsoft Outlook integration via Microsoft Graph API, system diagnostics using psutil, and all tools registered in the ToolRegistry.

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Microsoft OAuth2 auth | 57d2cce | tools/auth/microsoft.py |
| 2 | Microsoft Outlook tool | 57d2cce | tools/microsoft_outlook.py |
| 3 | System Monitor tool | 0e6ba66 | tools/system_monitor.py |
| 4 | Register all tools | 7feac4b | brain/tools.py |
| 5 | Update exports | 0840173 | tools/__init__.py |

## Artifacts Created

### tools/auth/microsoft.py
- **MicrosoftAuth** class using `DeviceCodeCredential` for Azure AD auth
- Device code flow for CLI-based authentication
- Token caching for persistence across sessions
- Supports scopes: Mail.Read, Mail.Send, Calendars.Read, Calendars.ReadWrite

### tools/microsoft_outlook.py
- **MicrosoftOutlookTool** class for Microsoft Graph API
- Read emails via `list_emails()`, `get_email()`
- Send emails via `send_email()`
- Calendar events via `list_calendar_events()`, `create_calendar_event()`
- Uses msgraph-sdk for Microsoft Graph API

### tools/system_monitor.py
- **SystemMonitorTool** class using psutil
- `get_cpu_usage()` - CPU percentage, per-core, frequency
- `get_memory_usage()` - total, available, used, percent (in GB)
- `get_disk_usage()` - disk statistics per partition
- `get_network_stats()` - bytes sent/received, packets
- `get_all()` - comprehensive system stats in one call
- Async support with streaming callbacks

### brain/tools.py
- Added `create_tools_registry()` factory function
- Registers 10 tools with descriptive strings
- All tools available for agent context

## Deviations from Plan

None - plan executed exactly as written.

## Dependencies Required

- **ST-07**: Microsoft OAuth integration via `azure-identity` + `msgraph-sdk`
- **ST-08**: System monitoring via `psutil` (already in requirements.txt)
- **ST-09**: Tool registry - all tools registered

## Notes

- Microsoft tools show warnings when dependencies not installed (expected)
- System monitor verified working on Windows (CPU, memory, disk, network)
- All 10 tools registered: browser, web_search, filesystem, execute_code, google_calendar, google_email, outlook, system_monitor, get_time, get_date
- MICROSOFT_CLIENT_ID environment variable required for Outlook authentication
