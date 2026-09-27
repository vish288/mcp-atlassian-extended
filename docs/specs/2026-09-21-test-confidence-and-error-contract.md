# mcp-atlassian-extended — spec (test confidence → error contract → dedup)

See the plan at ~/.claude/plans/jiggly-hopping-star.md. Status: harness (0.8.2,
PR #77) and contract (0.9.0, PR #78) shipped; dedup in progress.

## Objective
Prove tool behaviour through the real server (done), split expected failures
from bugs (done), remove drift-prone duplication (this branch): config ×2,
client response handling ×2, resources declared ×3.

## Commands
    uv run pytest -q --cov --cov-fail-under=95
    uv run ruff check . && uv run ruff format --check . && uv build

## Structure
    config.py            AtlassianConfig + _config_for(prefix); JiraConfig / ConfluenceConfig
    clients/_http.py     _raise_for_atlassian(resp, not_found=), _parse_json(resp)
    clients/jira.py, clients/confluence.py
    servers/_helpers.py  tool_result, _ok, _paginated, _err, _check_write
    servers/resources.py RESOURCES table, registered in a loop
    servers/prompts.py   five prompt functions, _PROMPT_FILES
    tests/               conftest fixtures, test_tool_contract (26×2), test_tool_result,
                         test_server_assembly, test_helpers

## Testing strategy
Through `Client(mcp)` with respx. Contract table pins each tool's request and
its 404 envelope. Assembly test scans `src/` for `^@mcp.tool` and reads every
resource live — that is the before/after proof for the resource loop.

## Boundaries
No live-API tests. Never touch release.yml / publish.yml. Ponytail cuts stay
ticket-only (INT-AT-010..014, INT-ALL-*).

## Success criteria (dedup)
- `list_resources()` count unchanged (15) and every URI still reads.
- `test_config.py` passes for both prefixes unchanged.
- Team Calendars 404 still maps to `TeamCalendarsUnavailableError`.
- `--cov-fail-under=95` holds.

## Outcome

- Released versions: 0.8.2 (harness), 0.9.0 (contract), 0.9.1 (dedup)
- Closed issues: #68, #69, #70, #71, #72, #73
