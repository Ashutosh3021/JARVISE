# Phase 6: System Tool Integrations - Context

**Gathered:** 2026-03-02
**Status:** Ready for planning

<domain>
## Phase Boundary

Executable tools for the JARVIS agent to interact with system — web search, browser automation, filesystem, calendar, email integrations. This phase expands the ToolRegistry in brain/tools.py with real system capabilities.

</domain>

<decisions>
## Implementation Decisions

### Authentication Strategy
- **Token Storage:** File-based (encrypted JSON in data/)
- **Token Refresh:** Automatic using refresh_token grant
- **Auth Separation:** Unified per provider (Google = all Google APIs, Microsoft = all MS APIs)
- **First-time Auth:** CLI-based flow (prints URL, user visits, pastes code)

### Browser Automation
- **Operations:** Full automation (any operation a human can do in browser)
- **Sessions:** Persistent (browser stays open, reuses session)
- **Display:** Visible (user sees browser window)
- **Content:** Text extraction with JARVIS highlighting important details

### Filesystem
- **Access:** User decides each time — interactive path selection
- **Write Confirmation:** Confirm every write before executing
- **Delete Confirmation:** Ask user before deleting anything
- **Path Handling:** Expand ~ to user home directory on Windows

### Tool Execution
- **Result Return:** Streaming + Async callbacks
- **Timeout:** Depends on task complexity (configurable per tool)
- **Logging:** Full logging (log to file + console)
- **Error Handling:** Raise exception with exact issue + suggested solution

### Claude's Discretion
- Exact timeout values per tool type
- Encryption algorithm choice for token storage
- Browser pool size for concurrent requests
- File operation retry logic

</decisions>

<specifics>
## Specific Ideas

- Browser tool should highlight "important details" in extracted content — JARVIS tells user what matters
- All tools should have clear error messages with suggested solutions
- Filesystem tool uses Windows paths properly (C:\Users\... expansion)

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- brain/tools.py: ToolRegistry class with register/execute/parse_action methods
- requirements.txt: playwright, google-api-python-client, msgraph-sdk already listed

### Integration Points
- Tools registered in brain/tools.py ToolRegistry
- Memory context available from Phase 5
- Config from core/config.py

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-system-tool-integrations*
*Context gathered: 2026-03-02*
