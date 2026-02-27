# mcp-atlassian-extended

[![PyPI version](https://img.shields.io/pypi/v/mcp-atlassian-extended)](https://pypi.org/project/mcp-atlassian-extended/)
[![PyPI downloads](https://img.shields.io/pypi/dm/mcp-atlassian-extended)](https://pypi.org/project/mcp-atlassian-extended/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-atlassian-extended)](https://pypi.org/project/mcp-atlassian-extended/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/vish288/mcp-atlassian-extended/actions/workflows/tests.yml/badge.svg)](https://github.com/vish288/mcp-atlassian-extended/actions/workflows/tests.yml)
[![MCP Registry](https://img.shields.io/badge/MCP-Registry-blue)](https://registry.modelcontextprotocol.io/servers/io.github.vish288/mcp-atlassian-extended)

<!-- mcp-name: io.github.vish288/mcp-atlassian-extended -->

**mcp-atlassian-extended** is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that extends [mcp-atlassian](https://github.com/sooperset/mcp-atlassian) with **23 tools**, **15 resources**, and **5 prompts** for Jira and Confluence: issue creation with custom fields, issue links, attachments, agile boards, sprints, backlog management, user search, calendars, time-off tracking, and sprint capacity planning. Works with Claude Desktop, Claude Code, Cursor, Windsurf, VS Code Copilot, and any MCP-compatible client.

Built with [FastMCP](https://github.com/jlowin/fastmcp), [httpx](https://www.python-httpx.org/), and [Pydantic](https://docs.pydantic.dev/).

## Relationship to mcp-atlassian

This project runs alongside [mcp-atlassian](https://github.com/sooperset/mcp-atlassian), not as a replacement. Configure both servers:

- **mcp-atlassian** handles: issues, search, transitions, comments, worklog, pages, Confluence search
- **mcp-atlassian-extended** handles: attachments, agile, users, fields, calendars, time-off

There is no tool overlap — this server only implements tools that mcp-atlassian lacks.

## 1-Click Installation

[![Install in Cursor](https://cursor.com/deeplink/mcp-install-dark.svg)](https://vish288.github.io/mcp-install?server=mcp-atlassian-extended&install=cursor)

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vish288.github.io/mcp-install?server=mcp-atlassian-extended&install=vscode) [![Install in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Install_Server-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://vish288.github.io/mcp-install?server=mcp-atlassian-extended&install=vscode-insiders)

> **💡 Tip:** For other AI assistants (Claude Code, Windsurf, IntelliJ), visit the **[Atlassian Extended MCP Installation Gateway](https://vish288.github.io/mcp-install?server=mcp-atlassian-extended)**.

<details>
<summary><b>Manual Setup Guides (Click to expand)</b></summary>
<br/>

> Prerequisite: Install `uv` first (required for all `uvx` install flows). [Install uv](https://docs.astral.sh/uv/getting-started/installation/).

### Claude Code

```bash
claude mcp add atlassian-extended -- uvx mcp-atlassian-extended
```

### Windsurf & IntelliJ

**Windsurf:** Add to `~/.codeium/windsurf/mcp_config.json`
**IntelliJ:** Add to `Settings | Tools | MCP Servers`

> **Note:** The actual server config starts at `atlassian-extended` inside the `mcpServers` object.

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
        "CONFLUENCE_API_TOKEN": "your_api_token"
      }
    }
  }
}
```

### pip / uv

```bash
uv pip install mcp-atlassian-extended
```

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

### Optional settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ATLASSIAN_READ_ONLY` | `false` | Set to `true` to globally disable write operations across tools |
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

## Tools (23)

| Category | Count | Tools |
|----------|-------|-------|
| **Jira Issues** | 3 | create (with custom fields), update (with custom fields), create epic |
| **Jira Links** | 2 | create link, delete link |
| **Jira Attachments** | 4 | get, upload, download, delete |
| **Jira Users** | 1 | search by name/email |
| **Jira Metadata** | 3 | list projects, list fields, backlog |
| **Jira Agile** | 4 | get board, board config, get sprint, move to sprint |
| **Confluence Calendars** | 6 | list, search, time-off, who-is-out, person time-off, sprint capacity |

<details>
<summary>Full tool reference (click to expand)</summary>

### Jira Issues
| Tool | Description |
|------|-------------|
| `jira_create_issue` | Create issue with standard and custom fields |
| `jira_update_issue` | Update issue fields and custom fields |
| `jira_create_epic` | Create an epic (sets issue type automatically) |

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

### Confluence Calendars
| Tool | Description |
|------|-------------|
| `confluence_list_calendars` | List all calendars |
| `confluence_search_calendars` | Search calendars by name/space |
| `confluence_get_time_off` | Get time-off events for date range |
| `confluence_who_is_out` | Check who is out on a date |
| `confluence_get_person_time_off` | Get person's time-off events |
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
→ jira_create_epic(project_key="PROJ", epic_name="Q1 Auth Overhaul")
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
    save_path="./downloads/report.pdf")
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

### Time-Off & Sprint Capacity

```
"Who is out today?"
→ confluence_who_is_out(date="today")

"Get team time-off for the next two weeks"
→ confluence_get_time_off(start_date="today", end_date="+14d", group_by_person=True)

"Calculate sprint capacity accounting for PTO"
→ confluence_sprint_capacity(
    team_members=["Alice", "Bob", "Carol"],
    sprint_start="2025-03-03", sprint_end="2025-03-14")
```

## Security Considerations

- **Token scope**: For Jira Cloud, use API tokens scoped to the minimum required permissions. For Data Center, use PATs with project-level access.
- **Read-only mode**: Set `ATLASSIAN_READ_ONLY=true` to disable all write operations (create, update, delete, upload). Enforced server-side before any API call.
- **File upload validation**: `jira_upload_attachment` validates file paths (no traversal, max 100MB, file must exist).
- **Download path restriction**: `jira_download_attachment` only accepts relative paths resolved within the working directory. Absolute paths and path traversal (`../`) are rejected.
- **Download URL validation**: Attachment download URLs are validated against the configured Jira URL domain to prevent SSRF.
- **SSL verification**: Enabled by default for both Jira and Confluence. Only disable for self-signed certificates in trusted networks.
- **MCP tool annotations**: Each tool declares `readOnlyHint`, `destructiveHint`, and `idempotentHint` for client-side permission prompts.
- **No credential storage**: Tokens are read from environment variables at startup and never persisted.

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
| Confluence calendars/time-off | View space content |

## CLI & Transport Options

```bash
# Default: stdio transport (for MCP clients)
uvx mcp-atlassian-extended

# HTTP transport (SSE or streamable-http)
uvx mcp-atlassian-extended --transport sse --host 127.0.0.1 --port 8000
uvx mcp-atlassian-extended --transport streamable-http --port 9000

# CLI overrides for config
uvx mcp-atlassian-extended --jira-url https://jira.example.com --jira-token xxx --read-only
```

The server loads `.env` files from the working directory automatically via `python-dotenv`.

**Partial configuration**: If only Jira credentials are set, the server starts with Jira tools only (no Confluence tools). The reverse also works — set only Confluence credentials to get calendar/time-off tools without Jira.

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
