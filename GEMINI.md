# mcp-atlassian-extended — Gemini CLI Extension Context

MCP server providing 23 tools, 15 resources, and 5 prompts for Jira and Confluence operations beyond core CRUD. Focuses on agile workflows, file attachments, team calendars, and sprint planning.

## Tool Categories

### Jira
- **Attachments** — get, upload, download, delete issue attachments
- **Users & Fields** — search users, list project fields
- **Agile** — backlog management, get/configure boards, get/create/update sprints, move issues to sprints
- **Issues** — create, update, create/delete issue links, create epics

### Confluence
- **Calendars** — list and search calendars
- **Time Off** — get time-off entries, check who is out, get person-specific time off
- **Sprint Capacity** — calculate team capacity for sprint planning

## Common Workflows

- **Sprint planning**: `jira_get_board` -> `jira_backlog` -> `confluence_sprint_capacity` -> `jira_create_sprint` -> `jira_move_to_sprint`
- **Attachment management**: `jira_get_attachments` -> `jira_download_attachment` -> `jira_upload_attachment` -> `jira_delete_attachment`
- **Team availability**: `confluence_who_is_out` -> `confluence_get_person_time_off` -> `confluence_sprint_capacity`
- **Issue linking**: `jira_create_issue` -> `jira_create_link` -> `jira_create_epic` -> `jira_move_to_sprint`
- **Board configuration**: `jira_get_board` -> `jira_board_config` -> `jira_get_sprint` -> `jira_backlog`

## Notes

- Set `ATLASSIAN_READ_ONLY=true` to restrict all operations to read-only.
- For Atlassian Cloud, use API tokens (`JIRA_API_TOKEN` / `CONFLUENCE_API_TOKEN`) with `JIRA_USERNAME` / `CONFLUENCE_USERNAME` instead of PATs.
- For Atlassian Data Center / Server, use personal access tokens (`JIRA_PAT` / `CONFLUENCE_PAT`).
- Default request timeout is 30 seconds per product; override with `JIRA_TIMEOUT` / `CONFLUENCE_TIMEOUT`.
- Jira and Confluence connections are independent — you can configure one without the other.
