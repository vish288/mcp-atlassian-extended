# mcp-atlassian-extended

[![PyPI version](https://img.shields.io/pypi/v/mcp-atlassian-extended)](https://pypi.org/project/mcp-atlassian-extended/)
[![PyPI downloads](https://img.shields.io/pypi/dm/mcp-atlassian-extended)](https://pypi.org/project/mcp-atlassian-extended/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-atlassian-extended)](https://pypi.org/project/mcp-atlassian-extended/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/vish288/mcp-atlassian-extended/actions/workflows/tests.yml/badge.svg)](https://github.com/vish288/mcp-atlassian-extended/actions/workflows/tests.yml)
[![MCP Registry](https://img.shields.io/badge/MCP-Registry-blue)](https://registry.modelcontextprotocol.io)

<!-- mcp-name: io.github.vish288/mcp-atlassian-extended -->

**Install:** `uvx mcp-atlassian-extended` | [PyPI](https://pypi.org/project/mcp-atlassian-extended/) | [MCP Registry](https://registry.modelcontextprotocol.io) | [Changelog](https://github.com/vish288/mcp-atlassian-extended/releases)

```bash
uvx mcp-atlassian-extended                          # with writes
MCP_READ_ONLY=true uvx mcp-atlassian-extended       # locked read-only: write tools are not listed
```

**mcp-atlassian-extended** is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server for Jira and Confluence. It gives an AI assistant **22 tools**, **15 resources**, and **5 prompts** for Jira and Confluence work. The tools create and update issues with custom fields, link issues, manage attachments, and search users. They also run agile boards and sprints, track project versions (API v2), read team calendars, and plan sprint capacity. It extends [mcp-atlassian](https://github.com/sooperset/mcp-atlassian) with zero tool overlap. Runs in one of two modes: with writes, or locked read-only (`MCP_READ_ONLY=true`) so the 10 write tools are never offered to the model.

The server supports the MCP **2026-07-28** specification (often called MCP 2.0) and stays compatible with **2025-11-25** clients. It works with Claude Desktop, Claude Code, Cursor, Windsurf, VS Code Copilot, and any MCP-compatible client.

The server supports Jira Cloud, Jira Data Center, Confluence Cloud, and Confluence Data Center (self-hosted). It needs no Atlassian Premium plan.

Built with [FastMCP](https://github.com/jlowin/fastmcp), [httpx](https://www.python-httpx.org/), and [Pydantic](https://docs.pydantic.dev/).

## Protocol support

- The server implements the MCP **2026-07-28** specification, often called MCP 2.0.
- It stays compatible with **2025-11-25** clients.
- Transports: `stdio` (default) and `streamable-http` (recommended for remote clients). The `sse` transport still works, but the 2026-07-28 specification deprecates it, so the server prints a warning.
- The server uses no roots, sampling, logging, elicitation, or resource subscriptions. The 2026-07-28 deprecations do not affect it.
- Built on FastMCP 4.x and the MCP Python SDK 2.x.

### Error results

Expected failures — a 404, a 401/403, a read-only refusal, an invalid argument — come back as a tool result with `isError: true`, so an MCP client sees the failure instead of a result that merely happens to contain the word `error`. The result body is the same `{"error": …, "hint": …}` object as before, with `status_code` and `body` when the failure came from the API; the `hint` names the fix. This object is the result's text content; `structuredContent` is not set, because a strict MCP client validates `structuredContent` against the tool's output schema even when `isError` is true, and the error envelope does not match it. Genuine bugs are still raised as protocol-level tool errors and logged with a traceback.

On success, a tool carries the same pretty-printed JSON as its text content and that JSON object as `structuredContent` — the pre-2.0 `{"result": "<json string>"}` wrapper is gone (a payload that is a JSON array, such as a multi-file upload response, carries text only, since `structuredContent` must be an object). Tools advertise no `outputSchema`: upstream fields pass through untyped, and a typed schema is opt-in per tool via `output_schema=` on `@mcp.tool(...)` when a client needs one.

## Relationship to mcp-atlassian

This project runs alongside [mcp-atlassian](https://github.com/sooperset/mcp-atlassian), not as a replacement. Configure both servers:

- **mcp-atlassian** handles: issues, search, transitions, comments, worklog, pages, Confluence search
- **mcp-atlassian-extended** handles: attachments, agile, users, fields, versions (API v2), calendars, time-off

There is no tool overlap — this server only implements tools that mcp-atlassian lacks.

## 1-Click Installation

[![Install in Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://vish288.github.io/mcp-install?server=mcp-atlassian-extended&install=cursor)

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vish288.github.io/mcp-install?server=mcp-atlassian-extended&install=vscode) [![Install in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Install_Server-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vish288.github.io/mcp-install?server=mcp-atlassian-extended&install=vscode-insiders)

> **💡 Tip:** For other AI assistants (Claude Code, Windsurf, IntelliJ, Gemini CLI), visit the **[Atlassian Extended MCP Installation Gateway](https://vish288.github.io/mcp-install?server=mcp-atlassian-extended)**.

<details>
<summary><b>Manual Setup Guides (Click to expand)</b></summary>
<br/>

> Prerequisite: Install `uv` first (required for all `uvx` install flows). [Install uv](https://docs.astral.sh/uv/getting-started/installation/).

### Claude Code

```bash
# with writes
claude mcp add atlassian-extended \
  -e JIRA_URL=https://your-company.atlassian.net -e JIRA_USERNAME=your.email@company.com -e JIRA_API_TOKEN=your_api_token \
  -- uvx mcp-atlassian-extended
# locked read-only: write tools are not listed
claude mcp add atlassian-extended -e MCP_READ_ONLY=true \
  -e JIRA_URL=https://your-company.atlassian.net -e JIRA_USERNAME=your.email@company.com -e JIRA_API_TOKEN=your_api_token \
  -- uvx mcp-atlassian-extended
```

### Windsurf & IntelliJ

**Windsurf:** Add to `~/.codeium/windsurf/mcp_config.json`
**IntelliJ:** Add to `Settings | Tools | MCP Servers`

> **Note:** The actual server config starts at `atlassian-extended` inside the `mcpServers` object.
> Remove `MCP_READ_ONLY` to allow writes.

```json
{
  "mcpServers": {
    "atlassian-extended": {
      "command": "uvx",
      "args": ["mcp-atlassian-extended"],
      "env": {
        "JIRA_URL": "https://your-company.atlassian.net",
        "JIRA_USERNAME": "your.email@company.com",
        "JIRA_API_TOKEN": "your_api_token",
        "CONFLUENCE_URL": "https://your-company.atlassian.net/wiki",
        "CONFLUENCE_USERNAME": "your.email@company.com",
        "CONFLUENCE_API_TOKEN": "your_api_token",
        "MCP_READ_ONLY": "true"
      }
    }
  }
}
```

### Gemini CLI

```bash
# with writes
gemini mcp add -s user -e JIRA_URL=https://your-company.atlassian.net -e JIRA_USERNAME=your.email@company.com -e JIRA_API_TOKEN=your_api_token -e CONFLUENCE_URL=https://your-company.atlassian.net/wiki -e CONFLUENCE_USERNAME=your.email@company.com -e CONFLUENCE_API_TOKEN=your_api_token atlassian-extended uvx mcp-atlassian-extended
# locked read-only
gemini mcp add -s user -e MCP_READ_ONLY=true -e JIRA_URL=https://your-company.atlassian.net -e JIRA_USERNAME=your.email@company.com -e JIRA_API_TOKEN=your_api_token -e CONFLUENCE_URL=https://your-company.atlassian.net/wiki -e CONFLUENCE_USERNAME=your.email@company.com -e CONFLUENCE_API_TOKEN=your_api_token atlassian-extended uvx mcp-atlassian-extended
```

### VS Code

Add to `.vscode/mcp.json`. Remove `MCP_READ_ONLY` to allow writes.

```json
{
  "servers": {
    "atlassian-extended": {
      "type": "stdio",
      "command": "uvx",
      "args": ["mcp-atlassian-extended"],
      "env": {
        "JIRA_URL": "https://your-company.atlassian.net",
        "JIRA_USERNAME": "your.email@company.com",
        "JIRA_API_TOKEN": "your_api_token",
        "MCP_READ_ONLY": "true"
      }
    }
  }
}
```

### Codex

```bash
# with writes
codex mcp add atlassian-extended --env JIRA_URL=https://your-company.atlassian.net --env JIRA_USERNAME=your.email@company.com --env JIRA_API_TOKEN=your_api_token -- uvx mcp-atlassian-extended
# locked read-only
codex mcp add atlassian-extended --env MCP_READ_ONLY=true --env JIRA_URL=https://your-company.atlassian.net --env JIRA_USERNAME=your.email@company.com --env JIRA_API_TOKEN=your_api_token -- uvx mcp-atlassian-extended
```

### pip / uv

```bash
uv pip install mcp-atlassian-extended
```

Drop `MCP_READ_ONLY` to allow writes. On a shared or hosted server put it in the deployer's env, not the client config.

</details>

## Configuration

### Jira Cloud (Basic Auth)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JIRA_URL` | **Yes** | - | Jira instance URL (e.g. `https://your-company.atlassian.net`) |
| `JIRA_USERNAME` | **Yes** | - | Email address for Jira Cloud |
| `JIRA_API_TOKEN` | **Yes** | - | API token from [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens) |

### Jira Data Center / Self-Hosted (Bearer Token)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `JIRA_URL` | **Yes** | - | Jira instance URL |
| `JIRA_PAT` | **Yes** | - | Personal access token (see fallback order below) |

The server checks these environment variables in order — first match wins:

1. `JIRA_PAT`
2. `JIRA_PERSONAL_TOKEN`
3. `JIRA_TOKEN`

Basic auth wins. If you set both `JIRA_USERNAME` and `JIRA_API_TOKEN`, the server uses
Basic auth and ignores any personal access token. The server uses Bearer auth only when
the Cloud pair is incomplete. To force Bearer, unset `JIRA_USERNAME` and `JIRA_API_TOKEN`.

### Confluence Cloud (Basic Auth)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CONFLUENCE_URL` | **Yes** | - | Confluence URL (e.g. `https://your-company.atlassian.net/wiki`) |
| `CONFLUENCE_USERNAME` | **Yes** | - | Email address for Confluence Cloud |
| `CONFLUENCE_API_TOKEN` | **Yes** | - | API token (same as Jira if same Atlassian account) |

### Confluence Data Center / Self-Hosted (Bearer Token)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `CONFLUENCE_URL` | **Yes** | - | Confluence instance URL |
| `CONFLUENCE_PAT` | **Yes** | - | Personal access token (see fallback order below) |

The server checks these environment variables in order — first match wins:

1. `CONFLUENCE_PAT`
2. `CONFLUENCE_PERSONAL_TOKEN`
3. `CONFLUENCE_TOKEN`

Basic auth wins here too: `CONFLUENCE_USERNAME` + `CONFLUENCE_API_TOKEN` take precedence
over any personal access token.

All Confluence calendar tools require the **Team Calendars** add-on
(`/rest/calendar-services/1.0/`). On instances without it every calendar tool returns a
404 with a hint naming the add-on.

### Optional settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_READ_ONLY` | `false` | Shared name across the mcp-* servers. Any value other than `false`/`0`/`no`/`off`/empty locks the server read-only: the 10 write tools and write-workflow prompts are not listed, and nothing can turn it back off at runtime |
| `ATLASSIAN_READ_ONLY` | `false` | Per-server alias for `MCP_READ_ONLY`; either one locks the server read-only. `--read-only` can only raise the lock |
| `ATLASSIAN_HTTP_BEARER_TOKEN` | - | Bearer token (min 16 chars) required to bind an HTTP transport to a non-loopback host; clients send `Authorization: Bearer <token>` |
| `ATLASSIAN_UPLOAD_DIR` | working directory | Only files under this directory may be uploaded (`jira_upload_attachment`). A relative value is resolved against the working directory. |
| `ATLASSIAN_DOWNLOAD_DIR` | `./atlassian-downloads` | Where `jira_download_attachment` writes. Created on first download. |
| `JIRA_TIMEOUT` | `30` | HTTP request timeout for Jira in seconds |
| `JIRA_SSL_VERIFY` | `true` | Set to `false` to skip SSL verification for Jira |
| `CONFLUENCE_TIMEOUT` | `30` | HTTP request timeout for Confluence in seconds |
| `CONFLUENCE_SSL_VERIFY` | `true` | Set to `false` to skip SSL verification for Confluence |

## Compatibility

| Client | Supported | Install Method |
|--------|-----------|----------------|
| Claude Desktop | Yes | `claude_desktop_config.json` |
| Claude Code | Yes | `claude mcp add` |
| Cursor | Yes | One-click deeplink or `.cursor/mcp.json` |
| Windsurf | Yes | `~/.codeium/windsurf/mcp_config.json` |
| VS Code Copilot | Yes | `.vscode/mcp.json` |
| Any MCP client | Yes | stdio or HTTP transport |

## Tools (22)

| Category | Count | Tools |
|----------|-------|-------|
| **Jira Issues** | 2 | create (with custom fields; `issue_type="Epic"` for epics), update (with custom fields) |
| **Jira Links** | 2 | create link, delete link |
| **Jira Attachments** | 4 | get, upload, download, delete |
| **Jira Users** | 1 | search by name/email |
| **Jira Metadata** | 3 | list projects, list fields, backlog |
| **Jira Agile** | 4 | get board, board config, get sprint, move to sprint |
| **Jira Versions** | 3 | get project versions, create version, update version |
| **Confluence Calendars** | 3 | list (type/search filter), time-off (date range, per-person), sprint capacity |

<details>
<summary>Full tool reference (click to expand)</summary>

### Jira Issues
| Tool | Description |
|------|-------------|
| `jira_create_issue` | Create issue with standard and custom fields (`issue_type="Epic"` creates an epic) |
| `jira_update_issue` | Update issue fields and custom fields |

### Jira Links
| Tool | Description |
|------|-------------|
| `jira_create_link` | Create a link between two issues (Relates, Blocks, etc.) |
| `jira_delete_link` | Delete an issue link by ID |

### Jira Attachments
| Tool | Description |
|------|-------------|
| `jira_get_attachments` | List attachments on an issue |
| `jira_upload_attachment` | Upload file to issue |
| `jira_download_attachment` | Download attachment to local file |
| `jira_delete_attachment` | Delete an attachment |

### Jira Users
| Tool | Description |
|------|-------------|
| `jira_search_users` | Search users by name/email |

### Jira Metadata
| Tool | Description |
|------|-------------|
| `jira_list_projects` | List all accessible projects |
| `jira_list_fields` | List fields (with search/custom filter) |
| `jira_backlog` | Get backlog issues for a board |

### Jira Agile
| Tool | Description |
|------|-------------|
| `jira_get_board` | Get board details |
| `jira_board_config` | Get board column configuration |
| `jira_get_sprint` | Get sprint details |
| `jira_move_to_sprint` | Move issues to a sprint |

### Jira Versions
| Tool | Description |
|------|-------------|
| `jira_get_project_versions` | List all versions for a project (REST API v2, Server/DC + Cloud) |
| `jira_create_version` | Create a new version in a project (REST API v2) |
| `jira_update_version` | Update an existing version (REST API v2) |

### Confluence Calendars
| Tool | Description |
|------|-------------|
| `confluence_list_calendars` | List calendars; optional `filter_type` and name/space `search` |
| `confluence_get_time_off` | Time-off events for a date range; optional `person` (exact match) and `group_by_person` |
| `confluence_sprint_capacity` | Calculate sprint capacity with time-off |

</details>

## Resources (15)

The server exposes curated Jira and Confluence workflow guides as [MCP resources](https://modelcontextprotocol.io/docs/concepts/resources).

| URI | Name | Description |
|-----|------|-------------|
| `resource://rules/jira-hierarchy` | Jira Issue Hierarchy | Epic/story/task/subtask relationships, when to use each level |
| `resource://rules/jira-ticket-writing` | Jira Ticket Writing Standards | Summary format, description structure, acceptance criteria placement |
| `resource://rules/acceptance-criteria` | Acceptance Criteria Standards | Given/When/Then format, testability, DoD vs AC |
| `resource://rules/sprint-hygiene` | Sprint Hygiene Rules | Capacity planning, carryover policy, sprint goals, retrospective items |
| `resource://rules/jira-workflow` | Jira Workflow & Automation | Status transitions, automation triggers, post-functions |
| `resource://rules/issue-linking` | Issue Linking Best Practices | Link types (blocks, relates, duplicates), cross-project links, epic links |
| `resource://guides/story-points` | Story Point Estimation | Fibonacci scale, relative sizing, team calibration, anti-patterns |
| `resource://guides/definition-of-done` | Definition of Done Checklists | Checklist format, team-level vs org-level DoD, verification steps |
| `resource://guides/jira-labels` | Jira Label Taxonomy | Naming conventions, label categories, label vs component |
| `resource://guides/jql-library` | JQL Query Library | Common queries, date functions, custom field syntax, saved filters |
| `resource://guides/custom-fields` | Jira Custom Field Governance | Field types, screen schemes, context, naming standards |
| `resource://guides/confluence-spaces` | Confluence Space Organization | Space types, permission schemes, archiving, templates |
| `resource://guides/agile-ceremonies` | Agile Ceremony Standards | Standup, planning, review, retro formats and time-boxing |
| `resource://guides/git-jira-integration` | Git-Jira Integration Patterns | Smart commits, branch naming, PR linking, status transitions |
| `resource://templates/confluence-pages` | Confluence Page Templates | ADR, runbook, onboarding, postmortem page structures |

## Prompts (5)

The server provides [MCP prompts](https://modelcontextprotocol.io/docs/concepts/prompts) — reusable multi-tool workflow templates that clients can surface as slash commands.

| Prompt | Parameters | Workflow |
|--------|-----------|----------|
| `create_ticket` | `project_key`, `issue_type` | Gather fields → set custom fields (DoD, privacy, security) → create → add links |
| `plan_sprint` | `board_id`, `sprint_id` | Check sprint → review backlog → calculate capacity → suggest scope → move issues |
| `close_ticket` | `issue_key` | Verify DoD → check linked MR → transition statuses → add closing comment |
| `team_availability` | `team_members`, `start_date`, `end_date` | Check who is out → per-person time-off → calculate capacity → flag conflicts |
| `manage_attachments` | `issue_key` | List attachments → identify stale/duplicates → upload/download → clean up |

## Usage Examples

### Issue Management

```
"Create a story in PROJ with custom story points"
→ jira_create_issue(project_key="PROJ", summary="Add OAuth login", issue_type="Story",
    custom_fields={"customfield_10004": 5})

"Update a ticket's priority and add labels"
→ jira_update_issue(issue_key="PROJ-123", fields={"priority": {"name": "High"}, "labels": ["urgent"]})

"Create an epic and link related stories"
→ jira_create_issue(project_key="PROJ", summary="Q1 Auth Overhaul", issue_type="Epic")
→ jira_create_link(link_type="Relates", inward_issue="PROJ-100", outward_issue="PROJ-200")
```

### Attachments

```
"List attachments on PROJ-123"
→ jira_get_attachments(issue_key="PROJ-123")

"Upload a screenshot to a ticket"
→ jira_upload_attachment(issue_key="PROJ-123", file_path="./screenshot.png")

"Download an attachment"
→ jira_download_attachment(content_url="https://jira.example.com/rest/api/2/attachment/content/456",
    save_path="report.pdf")  # lands in ./atlassian-downloads/report.pdf (or ATLASSIAN_DOWNLOAD_DIR)
```

### Agile & Sprint Management

```
"Get the current sprint for board 42"
→ jira_get_board(board_id=42) → jira_get_sprint(sprint_id=7)

"Move tickets into the next sprint"
→ jira_move_to_sprint(sprint_id=8, issue_keys=["PROJ-1", "PROJ-2", "PROJ-3"])

"View backlog for board 42"
→ jira_backlog(board_id=42, max_results=50)
```

### Version Management

```
"List versions for project PROJ"
→ jira_get_project_versions(project_key="PROJ")

"Create a new release version"
→ jira_create_version(project_key="PROJ", name="v2.0.0", release_date="2026-04-01")

"Mark version as released"
→ jira_update_version(version_id="200", released=True)
```

### Time-Off & Sprint Capacity

```
"Who is out today?"
→ confluence_get_time_off(start_date="today", end_date="today", group_by_person=True)

"Get team time-off for the next two weeks"
→ confluence_get_time_off(start_date="today", end_date="+14d", group_by_person=True)

"Calculate sprint capacity accounting for PTO"
→ confluence_sprint_capacity(
    team_members=["Alice", "Bob", "Carol"],
    sprint_start="2025-03-03", sprint_end="2025-03-14")
```

## Security Considerations

- **Token scope**: For Jira Cloud, use API tokens scoped to the minimum required permissions. For Data Center, use PATs with project-level access.
- **Read-only mode**: Set `MCP_READ_ONLY=true` (or `ATLASSIAN_READ_ONLY=true`) in the launch you control and the server starts locked: the 10 write tools and the write-workflow prompts are not listed, a call to one returns "Unknown tool", and the guard refuses any write that still reaches it. Nothing lifts the lock at runtime — not a `false` from another source, not a `.env` file, not tool arguments; any value other than `false`/`0`/`no`/`off`/empty locks, and `--read-only` can only raise it. The lock is only as strong as the launch: set it where users cannot edit it (a managed MCP config such as Claude Code `managed-mcp.json`, a container, k8s or systemd env, or a hosted HTTP deployment). A user who starts the server themselves controls its environment. All write tools are Jira tools; the Confluence tools are read-only in both modes.
- **HTTP transport auth**: An HTTP transport (`--transport streamable-http`/`sse`) serves every tool with the configured Atlassian credentials to anyone who reaches the port, so a non-loopback bind requires a shared bearer token. Set `ATLASSIAN_HTTP_BEARER_TOKEN` (≥ 16 chars; `openssl rand -hex 32`) and clients send it as `Authorization: Bearer <token>`; the token is compared in constant time. Without it the server refuses to start on any host other than `127.0.0.1`/`localhost`/`::1`. The server also validates the `Host`/`Origin` header on HTTP requests (`host_origin_protection="auto"`) so a DNS-rebinding page cannot drive a loopback-bound server.
- **Upload root restriction**: `jira_upload_attachment` only reads files inside the upload root — `ATLASSIAN_UPLOAD_DIR` if set, otherwise the working directory. The path is resolved (following symlinks) before the containment check, so a symlink pointing outside the root is rejected; dotfiles and dot-directories below the root are refused. Size is capped at 100 MB.
- **Download directory restriction**: `jira_download_attachment` writes only into the download directory (`ATLASSIAN_DOWNLOAD_DIR`, default `./atlassian-downloads/`, created on first use). `save_path` must be a bare file name — directories, absolute paths and dotfiles are rejected, not silently stripped. Existing files are never overwritten: a `-1`, `-2` numeric suffix is added and the final path is returned. The downloaded body is capped at 100 MB, mirroring the upload cap. Add `atlassian-downloads/` to your project's `.gitignore`.
- **Desktop-client caveat**: clients such as Claude Desktop launch stdio servers with a working directory of `/` or `$HOME`, which makes most of the filesystem the upload root (dotfiles excepted). Set `ATLASSIAN_UPLOAD_DIR` (and, if you like, `ATLASSIAN_DOWNLOAD_DIR`) explicitly for such clients.
- **Migration (0.11 → 0.12)**: uploads are now restricted to `ATLASSIAN_UPLOAD_DIR` (default: the server's working directory) and dotfiles are refused — if your client uploads from `~/Downloads`, set `ATLASSIAN_UPLOAD_DIR=~/Downloads`. Downloads now land in `./atlassian-downloads/` (or `ATLASSIAN_DOWNLOAD_DIR`) instead of the working directory, `save_path` is a file name only, and existing files are never overwritten.
- **Download URL validation**: The server validates each attachment download URL against the configured Jira URL domain to prevent SSRF.
- **SSL verification**: The server enables SSL verification by default for Jira and Confluence. Disable it only for self-signed certificates in trusted networks.
- **MCP tool annotations**: Each tool declares `readOnlyHint`, `destructiveHint`, and `idempotentHint` for client-side permission prompts.
- **No credential storage**: The server reads tokens from environment variables at startup. It never stores them.

## Rate Limits & Permissions

### Rate Limits

Jira Cloud enforces per-user rate limits. When rate-limited, tools return a 429 error with a hint to wait. Confluence Calendar API calls may be slower due to the Team Calendars plugin architecture.

### Required Permissions

| Operation | Minimum Jira Permission |
|-----------|----------------------|
| List projects, fields, boards | Browse Projects |
| Search users | Browse Users |
| Create/update issues, epics | Create Issues + Edit Issues |
| Create/delete issue links | Link Issues |
| Upload/delete attachments | Create Attachments + Delete Own Attachments |
| Move issues to sprint | Manage Sprints |
| Create/update versions | Administer Projects |
| Confluence calendars/time-off | View space content |

## CLI & Transport Options

```bash
# Default: stdio transport (for MCP clients)
uvx mcp-atlassian-extended

# HTTP transport. Use streamable-http for remote clients.
uvx mcp-atlassian-extended --transport streamable-http --port 9000

# A non-loopback HTTP bind requires a shared bearer token (>= 16 chars).
# Clients send it as "Authorization: Bearer <token>".
ATLASSIAN_HTTP_BEARER_TOKEN=$(openssl rand -hex 32) \
  uvx mcp-atlassian-extended --transport streamable-http --host 0.0.0.0 --port 9000

# sse still works, but the MCP 2026-07-28 spec deprecates it. The server prints a warning.
uvx mcp-atlassian-extended --transport sse --host 127.0.0.1 --port 8000

# CLI overrides for config
JIRA_PAT=xxx uvx mcp-atlassian-extended --jira-url https://jira.example.com --read-only
```

The `--jira-token`, `--jira-api-token`, `--confluence-token` and `--confluence-api-token` flags still work but are deprecated and hidden from `--help`: they expose the token to `ps` and shell history. Set `JIRA_PAT` / `JIRA_API_TOKEN` / `CONFLUENCE_PAT` / `CONFLUENCE_API_TOKEN` instead.

The server loads `.env` files from the working directory automatically via `python-dotenv`.

**Partial configuration**: You configure Jira and Confluence independently. Set either or both. The server always advertises all 22 tools. A tool for an unconfigured product returns a "not configured" error that names the variables to set. The server does not fail at startup.

## Docker

A minimal non-root image is provided. The image defaults to locked read-only (`MCP_READ_ONLY=true`); pass `-e MCP_READ_ONLY=false` to allow writes.

```bash
docker build -t mcp-atlassian-extended .
docker run --rm -i \
  -e JIRA_URL=https://your-company.atlassian.net \
  -e JIRA_USERNAME=your.email@company.com -e JIRA_API_TOKEN=your_api_token \
  mcp-atlassian-extended
```

The entry point is the `mcp-atlassian-extended` command; pass CLI flags after the image name. For an HTTP transport on a published port, also set `ATLASSIAN_HTTP_BEARER_TOKEN` and run with `--transport streamable-http --host 0.0.0.0`.

## FAQ

### Does it support the MCP 2026-07-28 spec (MCP 2.0)?

Yes. It implements the MCP 2026-07-28 specification (MCP 2.0) and stays compatible with 2025-11-25 clients.

### Which transports does it support?

It supports `stdio` (the default) and `streamable-http` (recommended for remote clients). The `sse` transport still works, but the 2026-07-28 specification deprecates it.

### Can I run mcp-atlassian-extended read-only so the assistant cannot change anything?

Yes. Start it with `MCP_READ_ONLY=true` (or `ATLASSIAN_READ_ONLY=true`). The 10 write tools and the write-workflow prompts are then not listed at all, so the model never sees them; a call to one returns "Unknown tool", and nothing can turn writes back on while the process runs. Set it in a launch you control — a managed MCP config, a container or systemd env, or a hosted deployment — because a user who starts the server themselves can start it without the variable.

### Does it work with self-hosted Jira and Confluence?

Yes. It supports Jira Cloud, Jira Data Center, Confluence Cloud, and Confluence Data Center. It uses the Jira REST API v2, which works on both Cloud and Server/Data Center.

### What permissions and token scopes does it need?

It needs a Jira API token (Cloud) or a personal access token (Data Center). Each operation needs the matching Jira permission. See [Required Permissions](#required-permissions).

### Does it replace mcp-atlassian?

No. It runs alongside mcp-atlassian with zero tool overlap. mcp-atlassian handles core search and CRUD. This server adds attachments, agile boards, versions, and calendars.

### Do the Confluence tools need an add-on?

Yes. The three Confluence calendar tools need the Team Calendars add-on. Without it, they return a 404 with a hint that names the add-on.

### How many tools does it provide?

It provides 22 tools, 15 resources, and 5 prompts for Jira and Confluence.

## Related MCP Servers

- [mcp-gitlab](https://github.com/vish288/mcp-gitlab) — GitLab integration (83 tools, 7 resources, 6 prompts)
- [mcp-coda](https://github.com/vish288/mcp-coda) — Coda integration (53 tools, 12 resources, 5 prompts)
- [mcp-argocd](https://github.com/vish288/mcp-argocd) — Argo CD integration (37 tools, 7 resources, 7 prompts)

## Attribution

Inspired by [mcp-atlassian](https://github.com/sooperset/mcp-atlassian) by sooperset. Architecture and patterns follow similar conventions.

## Development

```bash
git clone https://github.com/vish288/mcp-atlassian-extended.git
cd mcp-atlassian-extended
uv sync --all-extras

uv run pytest --cov
uv run ruff check .
uv run ruff format --check .
```

## License

MIT
