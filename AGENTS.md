# mcp-atlassian-extended — Agent Context

MCP server exposing 22 tools, 15 resources, and 5 prompts for Jira and Confluence
operations beyond core CRUD. Complements [mcp-atlassian](https://github.com/sooperset/mcp-atlassian)
with zero tool overlap: issue creation/update with custom fields, issue links,
attachments, agile boards and sprints, project versions, team calendars, and sprint
capacity planning. Built on FastMCP + httpx + Pydantic.

## Protocol support

- The server implements the MCP **2026-07-28** specification (MCP 2.0). It stays
  compatible with **2025-11-25** clients. A fastmcp client pinned to `2026-07-28` and a
  legacy client both list every tool and reach the API over stdio. The code PR's
  regression test checks `tools/list` with an in-memory client pinned to `2026-07-28`; it
  does not cover stdio or HTTP.
- Transports: `stdio` (default) and `streamable-http` (recommended for remote). `sse`
  still works, but the 2026-07-28 specification deprecates it, so the server prints a
  warning.
- The server uses no roots, sampling, logging, elicitation, or resource subscriptions.
  The 2026-07-28 deprecations do not affect it.
- Built on FastMCP 4.x and the MCP Python SDK 2.x.

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
| `src/mcp_atlassian_extended/servers/jira_issues.py` | 4 tools — issues, links |
| `src/mcp_atlassian_extended/servers/confluence_extended.py` | 3 tools — calendars, time off, capacity |
| `src/mcp_atlassian_extended/servers/resources.py` | 15 MCP resources |
| `src/mcp_atlassian_extended/servers/prompts.py` | 5 MCP prompts |
| `src/mcp_atlassian_extended/resources/*.md` | resource bodies (+ `prompts/` subdir for prompt bodies) |
| `tests/unit/` | unit + FastMCP in-process client tests (~155 tests; `test_tools.py` alone has 66) |
| `tests/test_links.py` | CI link checker — fetches every URL in README, pyproject, server.json, llms*.txt |
| `evaluations/eval.xml` | tool-selection eval fixtures |

`_register_tools()` in `servers/__init__.py` registers every tool by import side effect:
it imports each module so the `@mcp.tool` decorators run. A new module stays invisible
until you add it there.

A missing resource `.md` surfaces when a client first reads it (and in the assembly test,
which reads every URI). It does not fail at import, so one absent file never takes down
the whole server.

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
`respx` stubs HTTP.

Run the server locally:

```bash
uvx mcp-atlassian-extended                                            # stdio (default)
uvx mcp-atlassian-extended --transport sse --host 127.0.0.1 --port 8000  # deprecated by MCP 2026-07-28
uvx mcp-atlassian-extended --transport streamable-http --port 8000
uvx mcp-atlassian-extended --read-only
```

On stdio the server ignores `--host` and `--port`. Every connection CLI flag has an
env-var equivalent. The CLI builds the configs from the environment, applies any explicit
flags on top, and hands them to the lifespan directly. The four token flags
(`--jira-token`, `--jira-api-token`, `--confluence-token`, `--confluence-api-token`) are
deprecated and hidden from `--help`; they still work and warn on stderr. Use the env vars
(`JIRA_PAT`, `JIRA_API_TOKEN`, `CONFLUENCE_PAT`, `CONFLUENCE_API_TOKEN`) so the token does
not land in `ps` or shell history.

## Patterns

- Every tool is `async def`, takes `ctx: Context` first, and returns a `ToolResult` on
  success (via `_ok`/`_paginated`): the pretty JSON as text content plus the same object
  as `structuredContent`. No `outputSchema` is advertised — upstream fields pass through
  untyped; a typed schema is opt-in per tool via `output_schema=`. A JSON-array payload
  (the multi-file upload response) carries text only, as `structuredContent` must be an object.
- Tools do not handle their own errors — the `@tool_result` decorator does. Expected
  failures (`AtlassianError`, `ValueError`, `FileNotFoundError`) become an `isError: true`
  `ToolResult` whose text content is `_err`'s envelope, with no `structuredContent`;
  any other exception is logged with a traceback and re-raised as `ToolError`. Let the
  body raise; do not wrap it in `try/except`.
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

- `MCP_READ_ONLY` (shared across the mcp-* servers) or `ATLASSIAN_READ_ONLY` locks the
  server read-only: either being truthy resolves `read_only=True` once in `_config_for`,
  and the lifespan hides every write tool and write-workflow prompt by name
  (`server.disable(names=…)`). Write tools are not listed and calling one returns "Unknown
  tool". A falsy value never unlocks when another source is truthy, and an unrecognised
  value fails closed (locks) — the lock can only be raised, never cleared, from the client.
  Only a launch the deployer owns enforces it (`managed-mcp.json` `env`, container/k8s env).
- Every write tool still calls `_check_write(ctx, "jira")` or `_check_write(ctx, "confluence")`
  before any mutation (defence in depth). The second argument is mandatory and must name
  the product the tool writes to — the helper reads that product's config, and the two
  read-only flags are independent even though both default from `MCP_READ_ONLY` /
  `ATLASSIAN_READ_ONLY`.
- `jira_download_attachment` carries the `write` tag because it writes to local disk.
- All current write tools are Jira tools; the three Confluence tools are read-only.

### Errors

Never leak stack traces, tokens, or internal paths in error text.

## Tools (22)

| Category | Count | Tools |
| --- | --- | --- |
| Jira Issues | 2 | `jira_create_issue` (custom fields; `issue_type="Epic"` for epics), `jira_update_issue` |
| Jira Links | 2 | `jira_create_link`, `jira_delete_link` |
| Jira Attachments | 4 | `jira_get_attachments`, `jira_upload_attachment`, `jira_download_attachment`, `jira_delete_attachment` |
| Jira Users | 1 | `jira_search_users` |
| Jira Metadata | 3 | `jira_list_projects`, `jira_list_fields`, `jira_backlog` |
| Jira Agile | 4 | `jira_get_board`, `jira_board_config`, `jira_get_sprint`, `jira_move_to_sprint` |
| Jira Versions | 3 | `jira_get_project_versions`, `jira_create_version`, `jira_update_version` |
| Confluence Calendars | 3 | `confluence_list_calendars` (type/search filter), `confluence_get_time_off` (date range, optional `person`), `confluence_sprint_capacity` |

### Upstream APIs

- Jira issues, attachments, users, projects, fields, versions: `/rest/api/2/…`
  (v2, not v3 — works on both Server/DC and Cloud).
- Boards, sprints, backlog: `/rest/agile/1.0/…`.
- Confluence calendars and time off: `/rest/calendar-services/1.0/…` — this is the
  **Team Calendars** add-on. Confluence instances without it return 404 for all three
  Confluence tools.
- The client caps attachment uploads and downloads at 100 MB (`clients/jira.py`).

### Common workflows

- Sprint planning: `jira_get_board` → `jira_backlog` → `confluence_sprint_capacity` → `jira_move_to_sprint`
- Board inspection: `jira_get_board` → `jira_board_config` → `jira_get_sprint` → `jira_backlog`
- Attachments: `jira_get_attachments` → `jira_download_attachment` → `jira_upload_attachment` → `jira_delete_attachment`
- Team availability: `confluence_get_time_off` (group_by_person) → `confluence_get_time_off` (per `person`) → `confluence_sprint_capacity`
- Issue linking: `jira_create_issue` → `jira_create_link` → `jira_move_to_sprint`
- Versions: `jira_get_project_versions` → `jira_create_version` → `jira_update_version`

The server does not expose sprint creation. Create sprints in Jira, then use `jira_move_to_sprint`.

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

To add one, add the `.md` and one `Resource(...)` row to `RESOURCES` in
`servers/resources.py`. The loop registers it and the assembly test reads it back.

## Prompts (5)

Same pattern as resources: bodies live in `resources/prompts/*.md`, loaded by
`servers/prompts.py` via `_load_prompt()` and registered with `@mcp.prompt()`. Each
returns `list[Message]` — a user message (the workflow template) plus an assistant
acknowledgment. `string.Template(...).safe_substitute()` injects the prompt arguments, so
bodies use `$name` placeholders. An unmatched `$` stays intact and does not raise.

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
| `MCP_READ_ONLY` | Same as `ATLASSIAN_READ_ONLY`; shared name across the mcp-* servers. Either being truthy locks read-only; nothing unlocks it at runtime |
| `ATLASSIAN_READ_ONLY` | Truthy (anything but `false`/`0`/`no`/`off`/empty) locks writes; read by both configs |
| `ATLASSIAN_UPLOAD_DIR` | Upload root for `jira_upload_attachment`; default the working directory. Relative values resolve against cwd |
| `ATLASSIAN_DOWNLOAD_DIR` | Download directory for `jira_download_attachment`; default `./atlassian-downloads/`, created on first use |

Gotchas:

- **Attachment roots.** `jira_upload_attachment` reads only files resolved inside the
  upload root (`ATLASSIAN_UPLOAD_DIR`, else cwd) — symlinks are resolved first, dotfiles
  refused. `jira_download_attachment` writes only bare file names into the download
  directory (`ATLASSIAN_DOWNLOAD_DIR`, else `./atlassian-downloads/`) and never overwrites
  (numeric suffix). **Desktop-client caveat:** stdio clients (e.g. Claude Desktop) run with
  cwd `/` or `$HOME`, which widens the default upload root to most of the filesystem — set
  `ATLASSIAN_UPLOAD_DIR` explicitly for them. **Migration 0.11 → 0.12:** uploads outside the
  root and all dotfiles are now rejected; downloads moved from cwd to `./atlassian-downloads/`
  and `save_path` is a file name only.

- Basic wins. If you set both the username and API token, `auth_header` returns Basic and
  ignores the PAT. `auth_header` uses Bearer only when the Cloud pair is incomplete. To
  force Bearer, leave `*_USERNAME` and `*_API_TOKEN` unset.
- `_check_write(ctx, service)` takes the service explicitly (`"jira"` or `"confluence"`)
  and reads that product's config. Pass the one the calling tool writes to — the two
  read-only flags are independent even though both default from `MCP_READ_ONLY` /
  `ATLASSIAN_READ_ONLY`.
- All three Confluence calendar tools hit `/rest/calendar-services/1.0/`, which only exists
  with the Team Calendars add-on. A 404 there raises `TeamCalendarsUnavailableError` so
  the user gets an explanation instead of a bare 404.
- You configure Jira and Confluence independently. An unconfigured client is `None`,
  and its tools return a "not configured" error rather than failing at startup.
- The CLI loads `.env` via `load_dotenv()` from the working directory. The repo
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

1. `release.yml` (workflow_dispatch) first runs `tests.yml` and `lint.yml` via
   `workflow_call` and gates the release on them, then bumps `pyproject.toml`, rewrites the
   version line in `llms.txt` / `llms-full.txt`, bumps `server.json` (top level + each
   package) and `gemini-extension.json`, regenerates `uv.lock`, generates `CHANGELOG.md`,
   then creates the release commit and tag through the GitHub API, and dispatches
   `publish.yml` on the new tag.
2. `publish.yml` runs as split, idempotent jobs (`status → build → pypi →
   github-release → registry`): each target is checked first and written only when not
   already done, so PyPI, the GitHub release and the MCP Registry each complete
   independently and recoverably.
3. Recovery of a failed publish is `gh run rerun <id> --failed` or `gh workflow run
   publish.yml --ref refs/tags/vX.Y.Z`; both are no-ops for targets that are already done.
4. `reconcile.yml` does this unattended — about 5 min after a failed publish run, then every
   6 h on a schedule — scanning the last three tags and dispatching `publish.yml` as needed,
   capped at 8 failed attempts per tag before it asks for a human.

Rules:

- The workflow owns every version string listed above — do not edit them in a PR.
- Use conventional commit prefixes (`feat:`, `fix:`, `docs:`, …); the changelog generator
  reads them.
- The release commit is created through the GitHub API with `GITHUB_TOKEN` and no custom
  author/committer, so GitHub signs it as `github-actions[bot]` (Verified) with message
  `chore(release): X.Y.Z`; `release.yml` hard-fails if that commit is not verified. Only
  the ref moves (main fast-forward and the tag) use `RELEASE_PAT` — needed to bypass the
  branch ruleset; `release.yml` dispatches `publish.yml`, and the PAT's tag push is a
  duplicate that no-ops.
- `Vish` commits on `main` that came through a rebase-merged PR show as unsigned: GitHub
  rewrites the committer during rebase and cannot sign the result. PR review plus the
  required checks are the integrity control there.

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

- `jira_search_users` picks the user-search parameter by deployment: `query` on Cloud
  (`username` was removed in the GDPR migration) and `username` on Server/Data Center.
  Deployment is detected from the URL host (`JiraConfig.is_cloud`): `*.atlassian.net` /
  `api.atlassian.com` is Cloud. Auth mode is not used — DC also supports basic auth.
- Expected failures are `isError: true` results whose text content is the `{"error",
  "hint", …}` object; `structuredContent` is not set on error results (a strict MCP client
  validates it against the tool's output schema even on `isError`, and the envelope would
  fail that schema). Successful results do carry the payload object as `structuredContent`;
  no `outputSchema` is advertised, so nothing is validated against it. Genuine bugs are
  `isError: true` with `TypeName: message` text, logged with a traceback.
- Confluence tools depend on the Team Calendars add-on.
