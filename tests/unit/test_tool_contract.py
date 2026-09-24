"""One row per ``@mcp.tool``: the HTTP request it sends, and the envelope when it fails.

Rows are derived from each tool body and the client method it calls. Two tests
iterate the table: ``test_request_shape`` pins method, host, path, query and JSON
body of the outgoing request; ``test_forced_failure`` answers 404 and pins the
exact key set ``_err`` produces — that executes every tool's ``except`` arm.
"""

from __future__ import annotations

import json
from typing import Any, NamedTuple

import pytest
from httpx import Response

JIRA = "jira.example.com"
CONFLUENCE = "confluence.example.com"
SUBCALS = "/rest/calendar-services/1.0/calendar/subcalendars.json"
EVENTS = "/rest/calendar-services/1.0/calendar/events.json"
MULTIPART = object()  # body sentinel: multipart upload, not JSON

# One leave calendar with one leave child: enough for get_time_off_events to
# reach events.json with subCalendarId=child-1.
_LEAVE_CALENDARS = {
    "payload": [
        {
            "subCalendar": {"id": "cal-1", "name": "Team Leaves"},
            "childSubCalendars": [{"subCalendar": {"id": "child-1", "name": "Vacation leaves"}}],
        }
    ]
}
_EVENTS_PRELUDE = ((SUBCALS, _LEAVE_CALENDARS),)


class Row(NamedTuple):
    tool: str
    args: dict[str, Any]
    method: str
    path: str
    query: Any = ()  # dict, or list of pairs when a key repeats
    body: Any = None  # None = no body; MULTIPART = file upload; else decoded JSON
    host: str = JIRA
    prelude: tuple[tuple[str, Any], ...] = ()  # GET routes that answer 200 first


ROWS = [
    # ── jira_extended.py ──
    Row(
        "jira_get_attachments",
        {"issue_key": "PROJ-1"},
        "GET",
        "/rest/api/2/issue/PROJ-1",
        {"fields": "attachment"},
    ),
    Row(
        "jira_upload_attachment",
        {"issue_key": "PROJ-1", "file_path": "up.txt"},
        "POST",
        "/rest/api/2/issue/PROJ-1/attachments",
        body=MULTIPART,
    ),
    Row(
        "jira_download_attachment",
        {"content_url": f"https://{JIRA}/secure/attachment/1/f.txt", "save_path": "f.txt"},
        "GET",
        "/secure/attachment/1/f.txt",
    ),
    Row("jira_delete_attachment", {"attachment_id": "9"}, "DELETE", "/rest/api/2/attachment/9"),
    Row(
        "jira_search_users",
        {"query": "ali", "max_results": 5, "start_at": 10},
        "GET",
        "/rest/api/2/user/search",
        {"username": "ali", "maxResults": 5, "startAt": 10},
    ),
    Row("jira_list_projects", {}, "GET", "/rest/api/2/project"),
    Row("jira_list_fields", {"search": "x", "custom_only": True}, "GET", "/rest/api/2/field"),
    Row(
        "jira_backlog",
        {"board_id": 42, "max_results": 7, "start_at": 3},
        "GET",
        "/rest/agile/1.0/board/42/backlog",
        {"fields": "*all", "maxResults": 7, "startAt": 3},
    ),
    Row(
        "jira_get_project_versions",
        {"project_key": "PROJ"},
        "GET",
        "/rest/api/2/project/PROJ/versions",
    ),
    Row(
        "jira_create_version",
        {
            "project_key": "PROJ",
            "name": "v1",
            "description": "d",
            "release_date": "2026-01-02",
            "start_date": "2026-01-01",
            "released": True,
            "archived": False,
        },
        "POST",
        "/rest/api/2/version",
        body={
            "project": "PROJ",
            "name": "v1",
            "description": "d",
            "releaseDate": "2026-01-02",
            "startDate": "2026-01-01",
            "released": True,
            "archived": False,
        },
    ),
    Row(
        "jira_update_version",
        {"version_id": "200", "name": "v2", "released": True},
        "PUT",
        "/rest/api/2/version/200",
        body={"name": "v2", "released": True},
    ),
    # ── jira_issues.py ──
    Row(
        "jira_create_issue",
        {
            "project_key": "PROJ",
            "summary": "S",
            "issue_type": "Bug",
            "description": "d",
            "labels": ["a"],
            "priority": "High",
            "custom_fields": {"customfield_1": 5},
        },
        "POST",
        "/rest/api/2/issue",
        body={
            "fields": {
                "project": {"key": "PROJ"},
                "summary": "S",
                "issuetype": {"name": "Bug"},
                "description": "d",
                "labels": ["a"],
                "priority": {"name": "High"},
                "customfield_1": 5,
            }
        },
    ),
    Row(
        "jira_update_issue",
        {"issue_key": "PROJ-1", "fields": {"summary": "s"}, "custom_fields": {"customfield_1": 5}},
        "PUT",
        "/rest/api/2/issue/PROJ-1",
        body={"fields": {"summary": "s", "customfield_1": 5}},
    ),
    Row(
        "jira_create_epic",
        {"project_key": "PROJ", "epic_name": "E", "labels": ["a"]},
        "POST",
        "/rest/api/2/issue",
        body={
            "fields": {
                "project": {"key": "PROJ"},
                "summary": "E",
                "issuetype": {"name": "Epic"},
                "labels": ["a"],
            }
        },
    ),
    Row(
        "jira_create_link",
        {
            "link_type": "Blocks",
            "inward_issue": "PROJ-1",
            "outward_issue": "PROJ-2",
            "comment": "c",
        },
        "POST",
        "/rest/api/2/issueLink",
        body={
            "type": {"name": "Blocks"},
            "inwardIssue": {"key": "PROJ-1"},
            "outwardIssue": {"key": "PROJ-2"},
            "comment": {"body": "c"},
        },
    ),
    Row("jira_delete_link", {"link_id": "5"}, "DELETE", "/rest/api/2/issueLink/5"),
    # ── jira_agile.py ──
    Row("jira_get_board", {"board_id": 42}, "GET", "/rest/agile/1.0/board/42"),
    Row("jira_board_config", {"board_id": 42}, "GET", "/rest/agile/1.0/board/42/configuration"),
    Row("jira_get_sprint", {"sprint_id": 7}, "GET", "/rest/agile/1.0/sprint/7"),
    Row(
        "jira_move_to_sprint",
        {"sprint_id": 7, "issue_keys": ["PROJ-1", "PROJ-2"]},
        "POST",
        "/rest/agile/1.0/sprint/7/issue",
        body={"issues": ["PROJ-1", "PROJ-2"]},
    ),
    # ── confluence_extended.py ──
    Row("confluence_list_calendars", {"filter_type": "leaves"}, "GET", SUBCALS, host=CONFLUENCE),
    Row("confluence_search_calendars", {"query": "team"}, "GET", SUBCALS, host=CONFLUENCE),
    Row(
        "confluence_get_time_off",
        {"start_date": "2024-03-01", "end_date": "2024-03-10", "calendar_name": "Leaves"},
        "GET",
        EVENTS,
        [("start", "2024-03-01"), ("end", "2024-03-10"), ("subCalendarId", "child-1")],
        host=CONFLUENCE,
        prelude=_EVENTS_PRELUDE,
    ),
    Row(
        "confluence_who_is_out",
        {"date": "2024-03-03"},
        "GET",
        EVENTS,
        [("start", "2024-03-03"), ("end", "2024-03-03"), ("subCalendarId", "child-1")],
        host=CONFLUENCE,
        prelude=_EVENTS_PRELUDE,
    ),
    Row(
        "confluence_get_person_time_off",
        {
            "person": "Alice",
            "calendar_name": "Leaves",
            "start_date": "2024-03-01",
            "end_date": "2024-03-10",
        },
        "GET",
        EVENTS,
        [("start", "2024-03-01"), ("end", "2024-03-10"), ("subCalendarId", "child-1")],
        host=CONFLUENCE,
        prelude=_EVENTS_PRELUDE,
    ),
    Row(
        "confluence_sprint_capacity",
        {"team_members": ["Alice"], "sprint_start": "2024-03-04", "sprint_end": "2024-03-08"},
        "GET",
        EVENTS,
        [("start", "2024-03-04"), ("end", "2024-03-08"), ("subCalendarId", "child-1")],
        host=CONFLUENCE,
        prelude=_EVENTS_PRELUDE,
    ),
]

_IDS = [r.tool for r in ROWS]


def _pairs(query: Any) -> list[tuple[str, str]]:
    items = query.items() if isinstance(query, dict) else query
    return sorted((k, str(v)) for k, v in items)


def _mock(router, row: Row, status: int):
    for path, payload in row.prelude:
        router.get(path).mock(return_value=Response(200, json=payload))
    return router.route(method=row.method, path=row.path).mock(
        return_value=Response(status, json={})
    )


async def _call(client, row: Row) -> Any:
    result = await client.call_tool(row.tool, row.args)
    return json.loads(result.content[0].text)


@pytest.fixture
def _cwd(tmp_path, monkeypatch):
    """Upload reads, download writes — both relative to cwd."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / "up.txt").write_text("hello")


@pytest.mark.usefixtures("_cwd")
@pytest.mark.parametrize("row", ROWS, ids=_IDS)
async def test_request_shape(tool_client, row: Row):
    client, router = tool_client
    route = _mock(router, row, 200)

    parsed = await _call(client, row)

    assert "error" not in parsed, parsed
    req = route.calls.last.request
    assert (req.method, req.url.host, req.url.path) == (row.method, row.host, row.path)
    assert sorted(req.url.params.multi_items()) == _pairs(row.query)
    if row.body is MULTIPART:
        assert req.headers["content-type"].startswith("multipart/form-data")
    elif row.body is None:
        assert not req.content
    else:
        assert json.loads(req.content) == row.body


@pytest.mark.usefixtures("_cwd")
@pytest.mark.parametrize("row", ROWS, ids=_IDS)
async def test_forced_failure(tool_client, row: Row):
    client, router = tool_client
    _mock(router, row, 404)

    parsed = await _call(client, row)

    assert set(parsed) == {"error", "status_code", "body", "hint"}
    assert parsed["status_code"] == 404
