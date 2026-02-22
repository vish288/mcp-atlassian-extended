# mcp-atlassian-extended — Agent Context

Extended MCP tools for Jira and Confluence, complementing mcp-atlassian with 23 tools.

## Architecture

- **Entry point**: `src/mcp_atlassian_extended/__init__.py` — click CLI
- **Clients**: `src/mcp_atlassian_extended/clients/` — `JiraExtendedClient`, `ConfluenceExtendedClient`
- **Tools**: `src/mcp_atlassian_extended/servers/` — three modules: `jira_extended`, `jira_agile`, `confluence_extended`
- **Config**: `src/mcp_atlassian_extended/config.py` — `JiraConfig`, `ConfluenceConfig` from env

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
