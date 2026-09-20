# mcp-atlassian-extended — Agent Context

MCP server exposing 26 tools, 15 resources, and 5 prompts for Jira and Confluence
operations beyond core CRUD. Complements [mcp-atlassian](https://github.com/sooperset/mcp-atlassian)
with zero tool overlap: issue creation/update with custom fields, issue links,
attachments, agile boards and sprints, project versions, team calendars, and sprint
capacity planning. Built on FastMCP + httpx + Pydantic.

## Layout

| Path | Contents |
| --- | --- |
| `src/mcp_atlassian_extended/__init__.py` | click CLI entry point (`main`) |
| `src/mcp_atlassian_extended/config.py` | `JiraConfig`, `ConfluenceConfig` — dataclasses built from env |
| `src/mcp_atlassian_extended/clients/` | `JiraExtendedClient`, `ConfluenceExtendedClient` (httpx) |
| `src/mcp_atlassian_extended/servers/__init__.py` | `FastMCP` instance, `lifespan`, `_register_tools()` |
| `src/mcp_atlassian_extended/servers/_helpers.py` | shared `_get_jira`, `_get_confluence`, `_check_write`, `_ok`, `_err`, `_paginated`, `_load_file`, Jira URL parsers |
| `src/mcp_atlassian_extended/servers/jira_extended.py` | 11 tools — attachments, users, metadata, versions, backlog |
| `src/mcp_atlassian_extended/servers/jira_agile.py` | 4 tools — boards, sprints |
| `src/mcp_atlassian_extended/servers/jira_issues.py` | 5 tools — issues, epics, links |
| `src/mcp_atlassian_extended/servers/confluence_extended.py` | 6 tools — calendars, time off, capacity |
| `src/mcp_atlassian_extended/servers/resources.py` | 15 MCP resources |
| `src/mcp_atlassian_extended/servers/prompts.py` | 5 MCP prompts |
| `src/mcp_atlassian_extended/resources/*.md` | resource bodies (+ `prompts/` subdir for prompt bodies) |
| `src/mcp_atlassian_extended/models/` | empty package (see Known Limitations) |
| `tests/unit/` | unit + FastMCP in-process client tests (~155 tests; `test_tools.py` alone has 66) |
| `tests/test_links.py` | CI link checker — fetches every URL in README, pyproject, server.json, llms*.txt |
| `evaluations/eval.xml` | tool-selection eval fixtures |

Tools are registered purely by import side effect: `_register_tools()` in
`servers/__init__.py` imports each module so its `@mcp.tool` decorators run. A new
module is invisible until added there.

`resources.py` runs `_validate_resources()` at import and raises `RuntimeError` if any
expected `.md` is missing — a packaging error fails at startup, not at first read.

## Development

```bash
uv sync --all-extras
uv run pytest --cov            # asyncio_mode = "auto"; no @pytest.mark.asyncio needed
uv run ruff check .
uv run ruff format --check .
```

CI: `tests.yml` (matrix 3.10–3.13) and `lint.yml` run on every push and PR.
Ruff is line-length 100, target py310, rules `E,F,B,W,I,N,UP,S,C4,EM,ISC`.
`tests/**` ignores `S101`, `S105`, `S106`.

Shared fixtures live in `tests/conftest.py`: `jira_config`, `confluence_config`,
`jira_client`, `confluence_client` — all pointed at `*.example.com` with a dummy token.
HTTP is stubbed with `respx`.

Run the server locally:

```bash
uvx mcp-atlassian-extended                                            # stdio (default)
uvx mcp-atlassian-extended --transport sse --host 127.0.0.1 --port 8000
uvx mcp-atlassian-extended --transport streamable-http --port 8000
uvx mcp-atlassian-extended --read-only
```

`--host`/`--port` are ignored on stdio. Every connection CLI flag has an env-var
equivalent and simply writes into `os.environ` before the server module is imported.

## Patterns

- Every tool is `async def`, takes `ctx: Context` first, and returns a JSON **string**.
- Tools never raise: wrap the body in `try/except Exception as e: return _err(e)`.
- `_ok(data)` for single objects, `_paginated(items)` for lists (adds `items` + `count`).
- `_err` attaches an actionable `hint` keyed off the exception type and HTTP status
  (401/403, 404, 400, 409, 422, 429). Extend it there, not in individual tools.
- Import helpers from `._helpers` — never re-declare `_get_jira`, `_ok`, `_err`, etc.
- Jira tools accept either a key/ID or a browser URL: `_parse_jira_issue_url`,
  `_parse_jira_project_url`, `_parse_jira_board_url` pass non-URLs through unchanged.
- Confluence date params go through `_resolve_date()` (in `confluence_extended.py`),
  which accepts `"today"`, `"+14d"`, `"next week"`, or ISO dates.

## MCP compliance rules

### Annotations (mandatory)

Every `@mcp.tool()` needs `annotations={}`. House style:

- Read: `{"readOnlyHint": True, "idempotentHint": True, "openWorldHint": True}`
- Non-destructive write: `{"readOnlyHint": False, "openWorldHint": True}`
- Idempotent write (PUT/update): add `"idempotentHint": True`
- Destructive write (DELETE): add `"destructiveHint": True`

`openWorldHint: True` on everything — all tools hit a remote Atlassian instance.

### Tags

Every tool carries `tags={"jira"|"confluence", "<category>", "read"|"write"}`.

### Descriptions

1–2 sentences, front-loading what it does **and** what it returns.

- Bad: "This tool gets attachments."
- Good: "List attachments on a Jira issue. Returns id, filename, size, content URL."

### Parameters

- `Annotated[type, Field(description="...")]` on every parameter, with constraints
  where they apply (`ge=1` for IDs).
- `Literal[...]` over bare `str` for known value sets.
- Every optional parameter gets a default.
- Keep them flat — no nested dicts unless genuinely required (e.g. `custom_fields`).

### Naming

`{service}_{verb}_{resource}`, snake_case. Verbs: create, get, list, search, update,
delete, move, upload, download.

### Read-only mode

- Every write tool calls `_check_write(ctx, "jira")` or `_check_write(ctx, "confluence")`
  before any mutation. The second argument is mandatory and must name the product the
  tool writes to — the helper reads that product's config, and the two read-only flags
  are independent even though both default from `ATLASSIAN_READ_ONLY`.
- `jira_download_attachment` is tagged `write` because it writes to local disk.
- All current write tools are Jira tools; the six Confluence tools are read-only.

### Errors

Never leak stack traces, tokens, or internal paths in error text.

## Tools (26)

| Category | Count | Tools |
| --- | --- | --- |
| Jira Issues | 3 | `jira_create_issue`, `jira_update_issue`, `jira_create_epic` (all support custom fields) |
| Jira Links | 2 | `jira_create_link`, `jira_delete_link` |
| Jira Attachments | 4 | `jira_get_attachments`, `jira_upload_attachment`, `jira_download_attachment`, `jira_delete_attachment` |
| Jira Users | 1 | `jira_search_users` |
| Jira Metadata | 3 | `jira_list_projects`, `jira_list_fields`, `jira_backlog` |
| Jira Agile | 4 | `jira_get_board`, `jira_board_config`, `jira_get_sprint`, `jira_move_to_sprint` |
| Jira Versions | 3 | `jira_get_project_versions`, `jira_create_version`, `jira_update_version` |
| Confluence Calendars | 6 | `confluence_list_calendars`, `confluence_search_calendars`, `confluence_get_time_off`, `confluence_who_is_out`, `confluence_get_person_time_off`, `confluence_sprint_capacity` |

### Upstream APIs

- Jira issues, attachments, users, projects, fields, versions: `/rest/api/2/…`
  (v2, not v3 — works on both Server/DC and Cloud).
- Boards, sprints, backlog: `/rest/agile/1.0/…`.
- Confluence calendars and time off: `/rest/calendar-services/1.0/…` — this is the
  **Team Calendars** add-on. Confluence instances without it return 404 for all six
  Confluence tools.
- Attachment uploads are capped at 100 MB client-side (`clients/jira.py`).

### Common workflows

- Sprint planning: `jira_get_board` → `jira_backlog` → `confluence_sprint_capacity` → `jira_move_to_sprint`
- Board inspection: `jira_get_board` → `jira_board_config` → `jira_get_sprint` → `jira_backlog`
- Attachments: `jira_get_attachments` → `jira_download_attachment` → `jira_upload_attachment` → `jira_delete_attachment`
- Team availability: `confluence_who_is_out` → `confluence_get_person_time_off` → `confluence_sprint_capacity`
- Issue linking: `jira_create_issue` → `jira_create_link` → `jira_create_epic` → `jira_move_to_sprint`
- Versions: `jira_get_project_versions` → `jira_create_version` → `jira_update_version`

Sprint *creation* is not exposed — create sprints in Jira, then use `jira_move_to_sprint`.

### Adding a tool

1. Add it to the appropriate server module, or create a new module and import it in
   `servers/__init__.py::_register_tools`.
2. Import helpers from `._helpers`.
3. Include `annotations={}` and `tags={}` on the decorator.
4. Update the docs listed under Documentation Freshness in the same commit.

## Resources (15)

Markdown bodies in `src/mcp_atlassian_extended/resources/`, loaded via the cached,
traversal-guarded `_load_file()`. URI namespaces:

- `resource://rules/…` (6) — jira-hierarchy, jira-ticket-writing, acceptance-criteria,
  sprint-hygiene, jira-workflow, issue-linking
- `resource://guides/…` (8) — story-points, definition-of-done, jira-labels,
  jql-library, custom-fields, confluence-spaces, agile-ceremonies, git-jira-integration
- `resource://templates/…` (1) — confluence-pages

Adding one means adding the `.md`, the `@mcp.resource` function, **and** the filename
to `_RESOURCE_FILES` — otherwise `_validate_resources()` will not catch a packaging miss.

## Prompts (5)

Same pattern as resources: bodies live in `resources/prompts/*.md`, loaded by
`servers/prompts.py` via `_load_prompt()` and registered with `@mcp.prompt()`. Each
returns `list[Message]` — a user message (the workflow template) plus an assistant
acknowledgment. Prompt arguments are injected with
`string.Template(...).safe_substitute()`, so bodies use `$name` placeholders and an
unmatched `$` is left intact rather than raising.

| Prompt | Purpose | Tags |
| --- | --- | --- |
| `create_ticket` | Guided ticket creation | jira, create |
| `plan_sprint` | Sprint planning workflow | jira, agile |
| `close_ticket` | Ticket closure checklist | jira, workflow |
| `team_availability` | Availability report | confluence, capacity |
| `manage_attachments` | Attachment management | jira, attachments |

## Environment variables

| Variable | Notes |
| --- | --- |
| `JIRA_URL` | Trailing slash stripped |
| `JIRA_PAT` | Bearer auth (Data Center / Server). Aliases: `JIRA_PERSONAL_TOKEN`, `JIRA_TOKEN` |
| `JIRA_USERNAME` + `JIRA_API_TOKEN` | Basic auth (Cloud) |
| `JIRA_TIMEOUT` | Seconds, default `30` |
| `JIRA_SSL_VERIFY` | `false`/`0`/`no` disables verification |
| `CONFLUENCE_URL` | Cloud URLs usually need the `/wiki` suffix |
| `CONFLUENCE_PAT` | Bearer auth. Aliases: `CONFLUENCE_PERSONAL_TOKEN`, `CONFLUENCE_TOKEN` |
| `CONFLUENCE_USERNAME` + `CONFLUENCE_API_TOKEN` | Basic auth (Cloud) |
| `CONFLUENCE_TIMEOUT` | Seconds, default `30` |
| `CONFLUENCE_SSL_VERIFY` | As above |
| `ATLASSIAN_READ_ONLY` | `true`/`1`/`yes` disables writes; read by both configs |

Gotchas:

- Basic wins. If both the username and API token are set, `auth_header` returns Basic and
  the PAT is ignored; Bearer is used only when the Cloud pair is incomplete. To force
  Bearer, leave `*_USERNAME`/`*_API_TOKEN` unset.
- `_check_write(ctx, service)` takes the service explicitly (`"jira"` or `"confluence"`)
  and reads that product's config. Pass the one the calling tool writes to — the two
  read-only flags are independent even though both default from `ATLASSIAN_READ_ONLY`.
- All six Confluence calendar tools hit `/rest/calendar-services/1.0/`, which only exists
  with the Team Calendars add-on. A 404 there raises `TeamCalendarsUnavailableError` so
  the user gets an explanation instead of a bare 404.
- Jira and Confluence are configured independently. An unconfigured client is `None`,
  and its tools return a "not configured" error rather than failing at startup.
- `.env` is loaded by the CLI via `load_dotenv()` from the working directory. The repo
  ships no `.env.example`; the variable tables above are the reference.

## Release workflow

Releases run through GitHub Actions. Never bump versions or create tags by hand.

```bash
gh workflow run release.yml -f bump=patch                  # 0.6.14 → 0.6.15
gh workflow run release.yml -f bump=minor                  # 0.6.14 → 0.7.0
gh workflow run release.yml -f bump=major                  # 0.6.14 → 1.0.0
gh workflow run release.yml -f version=0.7.0               # explicit, overrides bump
gh workflow run release.yml -f bump=minor -f dry_run=true  # preview changelog, no push
```

1. `release.yml` (workflow_dispatch) bumps `pyproject.toml`, rewrites the version line in
   `llms.txt` / `llms-full.txt`, bumps `server.json` (top level + each package) and
   `gemini-extension.json`, regenerates `uv.lock`, generates `CHANGELOG.md`, then creates
   the release commit and tag through the GitHub API.
2. `publish.yml` (triggered by the `v*` tag) builds the wheel, publishes to PyPI, and
   creates the GitHub Release.

Rules:

- The workflow owns every version string listed above — do not edit them in a PR.
- Conventional commit prefixes (`feat:`, `fix:`, `docs:`, …) are required; the changelog
  is generated from them.
- The release commit is authored by `github-actions[bot]`, message `chore(release): X.Y.Z`.

## Documentation freshness (mandatory)

Any changeset that adds, removes, or renames a tool, resource, or prompt must update all
of these in the same commit:

- `README.md` — count in the heading and intro, tool table, full tool reference, usage
  examples, permissions table
- `llms.txt` — count in the tagline and documentation link
- `llms-full.txt` — count in the tagline, documentation link, and full tool reference
- `AGENTS.md` — count in the intro, layout table, Tools table
- `server.json` — `description` (≤100 chars) and `environmentVariables`
- `gemini-extension.json` — `description` and `settings`

Checklist: registered tool count matches the documented count; the category list is
complete; new tools appear in every reference section with their parameters and
annotations.

## Known limitations

- `models/` is an empty package. Add Pydantic response models there if responses ever
  need trimming or validation.
- `jira_search_users` uses the `username` query parameter, which works on Data Center but
  may not on Jira Cloud (which prefers `query`/`accountId`).
- Errors come back as *successful* tool results carrying `{"error": …, "hint": …}` (soft
  errors). Callers must inspect the JSON body, not just the call status.
- Confluence tools depend on the Team Calendars add-on being installed.
