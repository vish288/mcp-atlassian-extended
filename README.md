# mcp-atlassian-extended

Extended MCP tools for Jira and Confluence that complement [mcp-atlassian](https://github.com/sooperset/mcp-atlassian).

This server adds tools that mcp-atlassian does not cover: attachments, agile boards/sprints, user search, field metadata, and Confluence calendar/time-off management.

Built with [FastMCP](https://github.com/jlowin/fastmcp), [httpx](https://www.python-httpx.org/), and [Pydantic](https://docs.pydantic.dev/).

## Relationship to mcp-atlassian

This project is designed to run alongside mcp-atlassian, not replace it. Users configure both servers:

- **mcp-atlassian** handles: issues, search, transitions, comments, worklog, pages, Confluence search
- **mcp-atlassian-extended** handles: attachments, agile, users, fields, calendars, time-off

There is no tool overlap — this server only implements tools that mcp-atlassian lacks.

## Installation

```bash
# From PyPI
uv pip install mcp-atlassian-extended

# From source
uv pip install git+https://github.com/vish288/mcp-atlassian-extended.git
```

## Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `JIRA_URL` | For Jira tools | Jira instance URL |
| `JIRA_PAT` | For Jira tools | Jira personal access token |
| `CONFLUENCE_URL` | For Confluence tools | Confluence instance URL |
| `CONFLUENCE_PAT` | For Confluence tools | Confluence personal access token |
| `ATLASSIAN_READ_ONLY` | No | Set to `true` to disable write operations |

## Usage

### Claude Code / Cursor

```json
{
  "mcpServers": {
    "atlassian-extended": {
      "command": "uvx",
      "args": ["mcp-atlassian-extended"],
      "env": {
        "JIRA_URL": "https://your-instance.atlassian.net",
        "JIRA_PAT": "your-token",
        "CONFLUENCE_URL": "https://your-instance.atlassian.net/wiki",
        "CONFLUENCE_PAT": "your-token"
      }
    }
  }
}
```

### Standalone

```bash
mcp-atlassian-extended
mcp-atlassian-extended --transport sse --port 8000
```

## Tools (22)

### Jira Attachments (4)
| Tool | Description |
|------|-------------|
| `jira_get_attachments` | List attachments on an issue |
| `jira_upload_attachment` | Upload file to issue |
| `jira_download_attachment` | Download attachment to local file |
| `jira_delete_attachment` | Delete an attachment |

### Jira Users (1)
| Tool | Description |
|------|-------------|
| `jira_search_users` | Search users by name/email |

### Jira Metadata (3)
| Tool | Description |
|------|-------------|
| `jira_list_projects` | List all accessible projects |
| `jira_list_fields` | List fields (with search/custom filter) |
| `jira_backlog` | Get backlog issues for a board |

### Jira Agile (4)
| Tool | Description |
|------|-------------|
| `jira_get_board` | Get board details |
| `jira_board_config` | Get board column configuration |
| `jira_get_sprint` | Get sprint details |
| `jira_move_to_sprint` | Move issues to a sprint |

### Confluence Calendars (6)
| Tool | Description |
|------|-------------|
| `confluence_list_calendars` | List all calendars |
| `confluence_search_calendars` | Search calendars by name/space |
| `confluence_get_time_off` | Get time-off events for date range |
| `confluence_who_is_out` | Check who is out on a date |
| `confluence_get_person_time_off` | Get person's time-off events |
| `confluence_sprint_capacity` | Calculate sprint capacity with time-off |

## Attribution

This project was inspired by [mcp-atlassian](https://github.com/sooperset/mcp-atlassian) by sooperset. Architecture and patterns follow similar conventions.

## Development

```bash
git clone https://github.com/vish288/mcp-atlassian-extended.git
cd mcp-atlassian-extended
uv sync --all-extras
uv run pytest --cov
uv run ruff check .
```

## License

MIT
