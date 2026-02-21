# mcp-atlassian-extended

[![PyPI version](https://img.shields.io/pypi/v/mcp-atlassian-extended)](https://pypi.org/project/mcp-atlassian-extended/)
[![PyPI downloads](https://img.shields.io/pypi/dm/mcp-atlassian-extended)](https://pypi.org/project/mcp-atlassian-extended/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-atlassian-extended)](https://pypi.org/project/mcp-atlassian-extended/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/vish288/mcp-atlassian-extended/actions/workflows/tests.yml/badge.svg)](https://github.com/vish288/mcp-atlassian-extended/actions/workflows/tests.yml)

**mcp-atlassian-extended** is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that extends [mcp-atlassian](https://github.com/sooperset/mcp-atlassian) with **22 additional tools** for Jira and Confluence: attachments, agile boards, sprints, backlog management, user search, calendars, time-off tracking, and sprint capacity planning. Works with Claude Desktop, Claude Code, Cursor, Windsurf, VS Code Copilot, and any MCP-compatible client.

Built with [FastMCP](https://github.com/jlowin/fastmcp), [httpx](https://www.python-httpx.org/), and [Pydantic](https://docs.pydantic.dev/).

## Relationship to mcp-atlassian

This project runs alongside [mcp-atlassian](https://github.com/sooperset/mcp-atlassian), not as a replacement. Configure both servers:

- **mcp-atlassian** handles: issues, search, transitions, comments, worklog, pages, Confluence search
- **mcp-atlassian-extended** handles: attachments, agile, users, fields, calendars, time-off

There is no tool overlap — this server only implements tools that mcp-atlassian lacks.

## Quick Install

### Cursor

[![Install MCP Server](https://cursor.com/deeplink/mcp-install-dark.svg)](cursor://anysphere.cursor-deeplink/mcp/install?name=mcp-atlassian-extended&config=eyJtY3BTZXJ2ZXJzIjogeyJhdGxhc3NpYW4tZXh0ZW5kZWQiOiB7ImNvbW1hbmQiOiAidXZ4IiwgImFyZ3MiOiBbIm1jcC1hdGxhc3NpYW4tZXh0ZW5kZWQiXSwgImVudiI6IHsiSklSQV9VUkwiOiAiaHR0cHM6Ly95b3VyLWNvbXBhbnkuYXRsYXNzaWFuLm5ldCIsICJKSVJBX1VTRVJOQU1FIjogInlvdXIuZW1haWxAY29tcGFueS5jb20iLCAiSklSQV9BUElfVE9LRU4iOiAieW91ci10b2tlbiJ9fX19)

### Claude Code

```bash
claude mcp add atlassian-extended -- uvx mcp-atlassian-extended
```

### Windsurf / VS Code

Add to your MCP config file:

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

## Configuration

### Jira Cloud (Basic Auth)

| Variable | Required | Description |
|----------|----------|-------------|
| `JIRA_URL` | Yes | Jira instance URL (e.g. `https://your-company.atlassian.net`) |
| `JIRA_USERNAME` | Yes | Email address for Jira Cloud |
| `JIRA_API_TOKEN` | Yes | API token from [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens) |

### Jira Data Center / Self-Hosted (Bearer Token)

| Variable | Required | Description |
|----------|----------|-------------|
| `JIRA_URL` | Yes | Jira instance URL |
| `JIRA_PAT` | Yes | Personal access token |

Also accepts: `JIRA_PERSONAL_TOKEN`, `JIRA_TOKEN`

### Confluence Cloud (Basic Auth)

| Variable | Required | Description |
|----------|----------|-------------|
| `CONFLUENCE_URL` | Yes | Confluence URL (e.g. `https://your-company.atlassian.net/wiki`) |
| `CONFLUENCE_USERNAME` | Yes | Email address for Confluence Cloud |
| `CONFLUENCE_API_TOKEN` | Yes | API token (same as Jira if same Atlassian account) |

### Confluence Data Center / Self-Hosted (Bearer Token)

| Variable | Required | Description |
|----------|----------|-------------|
| `CONFLUENCE_URL` | Yes | Confluence instance URL |
| `CONFLUENCE_PAT` | Yes | Personal access token |

Also accepts: `CONFLUENCE_PERSONAL_TOKEN`, `CONFLUENCE_TOKEN`

### Optional

| Variable | Description |
|----------|-------------|
| `ATLASSIAN_READ_ONLY` | Set to `true` to disable write operations |

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
| **Jira Attachments** | 4 | get, upload, download, delete |
| **Jira Users** | 1 | search by name/email |
| **Jira Metadata** | 3 | list projects, list fields, backlog |
| **Jira Agile** | 4 | get board, board config, get sprint, move to sprint |
| **Confluence Calendars** | 6 | list, search, time-off, who-is-out, person time-off, sprint capacity |

<details>
<summary>Full tool reference (click to expand)</summary>

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
