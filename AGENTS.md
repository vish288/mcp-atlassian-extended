# mcp-atlassian-extended — Agent Context

Extended MCP tools for Jira and Confluence, complementing mcp-atlassian with 23 tools.

## Architecture

- **Entry point**: `src/mcp_atlassian_extended/__init__.py` — click CLI
- **Clients**: `src/mcp_atlassian_extended/clients/` — `JiraExtendedClient`, `ConfluenceExtendedClient`
- **Tools**: `src/mcp_atlassian_extended/servers/` — four modules: `jira_extended`, `jira_agile`, `jira_issues`, `confluence_extended`
- **Helpers**: `src/mcp_atlassian_extended/servers/_helpers.py` — shared `_get_jira`, `_get_confluence`, `_check_write`, `_ok`, `_err`
- **Config**: `src/mcp_atlassian_extended/config.py` — `JiraConfig`, `ConfluenceConfig` from env

## Patterns

- All tools are `async def` returning JSON strings
- Shared helpers extracted to `servers/_helpers.py` — all server modules import from there
- Error handling: try/except wrapping every tool, returning `{"error": ...}` JSON
- Write access control: `_check_write(ctx)` raises `WriteDisabledError` when `ATLASSIAN_READ_ONLY=true`
- Tags: every tool tagged with `{"jira"|"confluence", "<category>", "read"|"write"}`
- Parameters use `Annotated[type, Field(description=...)]`
- Confluence tools include `_resolve_date()` for relative dates ("today", "+14d", "next week")

## MCP Compliance Rules

### Tool Annotations (MANDATORY)
Every tool MUST have `annotations={}` with at minimum `readOnlyHint`.
- Read tools: `annotations={"readOnlyHint": True, "idempotentHint": True}`
- Non-destructive write tools: `annotations={"readOnlyHint": False}`
- Destructive write tools: `annotations={"destructiveHint": True, "readOnlyHint": False}`
- Idempotent writes (PUT/update): add `idempotentHint: True`

### Tool Descriptions
- 1-2 sentences. Front-load what it does AND what it returns.
- Bad: "This tool gets attachments."
- Good: "List attachments on a Jira issue. Returns id, filename, size, content URL."

### Error Handling
- Every tool MUST wrap in try/except and return `_err(e)` — never raise.
- Error text MUST be actionable: include what went wrong and suggest a fix.
- Never expose stack traces, tokens, or internal paths.

### Parameter Design
- Use `Annotated[type, Field(description="...")]` on every parameter.
- Use `Literal[...]` for known value sets instead of plain `str`.
- Every optional parameter must have a default.
- Flatten — no nested dicts unless truly necessary (like `custom_fields`).

### Read-Only Mode
- Every write tool MUST call `_check_write(ctx)` before any mutation.
- `jira_download_attachment` is tagged "write" because it writes to local disk.

### Naming Convention
- Pattern: `{service}_{verb}_{resource}` (snake_case)
- Verbs: create, get, list, search, update, delete, move, upload, download

### Adding New Tools
- Add to the appropriate server module (or create a new one registered in `servers/__init__.py`)
- Import helpers from `._helpers` — never duplicate `_get_jira`, `_ok`, `_err`, etc.
- Always include `annotations={}` on the `@mcp.tool()` decorator
- Tag with service, category, and read/write

## Tool Categories

- Jira Issues (3): create (with custom fields), update (with custom fields), create-epic
- Jira Links (2): create-link, delete-link
- Jira Attachments (4): get, upload, download, delete
- Jira Users (1): search
- Jira Metadata (3): list-projects, list-fields, backlog
- Jira Agile (4): get-board, board-config, get-sprint, move-to-sprint
- Confluence Calendars (6): list, search, time-off, who-is-out, person-time-off, sprint-capacity

## Environment Variables

- `JIRA_URL` + `JIRA_USERNAME` + `JIRA_API_TOKEN` — Jira Cloud (Basic auth)
- `JIRA_URL` + `JIRA_PAT` — Jira Data Center (Bearer token)
- `CONFLUENCE_URL` + `CONFLUENCE_USERNAME` + `CONFLUENCE_API_TOKEN` — Confluence Cloud
- `CONFLUENCE_URL` + `CONFLUENCE_PAT` — Confluence Data Center
- `ATLASSIAN_READ_ONLY` — disable mutations

## Known Limitations / Future Work

- `models/` package is empty. Define Pydantic response models if response trimming is needed.
- No tool-level tests. Client and config tests exist.
- `jira_search_users` uses `username` parameter which may not work on Jira Cloud v3 (works on Data Center).
- Errors are returned as successful tool results with `{"error": ...}` (soft-error pattern). Callers must inspect JSON content.
