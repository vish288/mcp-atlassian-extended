"""Tool-level tests — call @mcp.tool functions via FastMCP Client with mocked API.

Fixtures ``tool_client`` / ``readonly_client`` live in ``tests/conftest.py``.
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest
import respx
from httpx import Response

from mcp_atlassian_extended.clients.confluence import ConfluenceExtendedClient
from mcp_atlassian_extended.config import ConfluenceConfig, JiraConfig
from mcp_atlassian_extended.exceptions import WriteDisabledError
from mcp_atlassian_extended.servers._helpers import _check_write, _get_confluence, _get_jira

TEST_JIRA_URL = "https://jira.example.com"
TEST_CONFLUENCE_URL = "https://confluence.example.com"
TEST_TOKEN = "test-token"


def _parse(result: Any) -> dict | list:
    """Extract JSON from a tool call result."""
    if hasattr(result, "content"):
        for item in result.content:
            if hasattr(item, "text"):
                return json.loads(item.text)
    if hasattr(result, "__iter__") and not isinstance(result, (str, dict)):
        for item in result:
            if hasattr(item, "text"):
                return json.loads(item.text)
    return json.loads(str(result))


def _err_body(result: Any) -> dict:
    """An expected failure is now an ``isError`` result; assert that and return its body.

    Call the tool with ``raise_on_error=False`` so the client hands back the
    result instead of raising ``ToolError``.
    """
    assert result.is_error is True
    return _parse(result)


# ═══════════════════════════════════════════════════════
# Path-injection boundary validation (AT-R01)
# ═══════════════════════════════════════════════════════


class TestIdBoundaryValidation:
    """Path-segment ids/keys are pattern-validated at the tool boundary, so a
    traversal payload is refused before it ever reaches the client."""

    @pytest.mark.parametrize(
        ("tool", "args"),
        [
            ("jira_delete_attachment", {"attachment_id": "../issue/PROJ-1"}),
            ("jira_delete_link", {"link_id": "../issue/PROJ-2?deleteSubtasks=true"}),
            ("jira_get_attachments", {"issue_key": "../../secure/admin"}),
            ("jira_update_version", {"version_id": "1/../issue/PROJ-1", "name": "x"}),
            ("jira_get_project_versions", {"project_key": "../issue"}),
        ],
    )
    async def test_rejects_injection(self, tool_client, tool, args):
        client, router = tool_client
        result = await client.call_tool(tool, args, raise_on_error=False)
        assert result.is_error is True
        # Refused at the boundary (pattern mismatch), not after an HTTP attempt.
        text = "".join(getattr(c, "text", "") for c in result.content).lower()
        assert "pattern" in text or "validation" in text
        assert not router.calls

    async def test_accepts_lowercase_key(self, tool_client):
        """Jira normalises lowercase keys; the boundary must accept them and the
        value must still reach the (escaped) REST path."""
        client, router = tool_client
        route = router.get("/rest/api/2/issue/proj-1").mock(
            return_value=Response(200, json={"fields": {"attachment": []}})
        )
        result = await client.call_tool(
            "jira_get_attachments", {"issue_key": "proj-1"}, raise_on_error=False
        )
        assert result.is_error is False
        assert route.called
        assert route.calls.last.request.url.path == "/rest/api/2/issue/proj-1"


# ═══════════════════════════════════════════════════════
# Attachments
# ═══════════════════════════════════════════════════════


class TestGetAttachments:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.get("/rest/api/2/issue/PROJ-123").mock(
            return_value=Response(
                200,
                json={"fields": {"attachment": [{"id": "1", "filename": "doc.pdf", "size": 1024}]}},
            )
        )
        result = await client.call_tool("jira_get_attachments", {"issue_key": "PROJ-123"})
        parsed = _parse(result)
        assert parsed["count"] == 1
        assert parsed["items"][0]["filename"] == "doc.pdf"

    async def test_not_found(self, tool_client):
        client, router = tool_client
        router.get("/rest/api/2/issue/INVALID-999").mock(
            return_value=Response(404, json={"errorMessages": ["Issue not found"]})
        )
        result = await client.call_tool(
            "jira_get_attachments", {"issue_key": "INVALID-999"}, raise_on_error=False
        )
        parsed = _err_body(result)
        assert "error" in parsed


class TestUploadAttachment:
    # Read-only behaviour (hidden write tools, decorator-level guard) lives in
    # tests/unit/test_read_only_lock.py — it is identical for every write tool.
    async def test_outside_root_rejected(self, tool_client, tmp_path, monkeypatch):
        client, router = tool_client
        work = tmp_path / "work"
        work.mkdir()
        secret = tmp_path / "secret.txt"
        secret.write_text("x")
        monkeypatch.chdir(work)
        # Validation rejects before any HTTP call, so no route is registered.
        result = await client.call_tool(
            "jira_upload_attachment",
            {"issue_key": "PROJ-123", "file_path": str(secret)},
            raise_on_error=False,
        )
        parsed = _err_body(result)
        assert "error" in parsed
        assert "outside the upload directory" in parsed["error"]
        assert "ATLASSIAN_UPLOAD_DIR" in parsed["hint"]

    async def test_dotfile_rejected(self, tool_client, tmp_path, monkeypatch):
        client, router = tool_client
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text("secret")
        result = await client.call_tool(
            "jira_upload_attachment",
            {"issue_key": "PROJ-123", "file_path": ".env"},
            raise_on_error=False,
        )
        parsed = _err_body(result)
        assert "error" in parsed
        assert "hidden" in parsed["error"]


# ═══════════════════════════════════════════════════════
# Issues
# ═══════════════════════════════════════════════════════


class TestCreateIssue:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.post("/rest/api/2/issue").mock(
            return_value=Response(
                201,
                json={"id": "10001", "key": "PROJ-124", "self": "https://..."},
            )
        )
        result = await client.call_tool(
            "jira_create_issue",
            {
                "project_key": "PROJ",
                "summary": "Test issue",
                "issue_type": "Story",
            },
        )
        parsed = _parse(result)
        assert parsed["key"] == "PROJ-124"


class TestUpdateIssue:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.put("/rest/api/2/issue/PROJ-123").mock(return_value=Response(204))
        result = await client.call_tool(
            "jira_update_issue",
            {
                "issue_key": "PROJ-123",
                "fields": {"summary": "Updated title"},
            },
        )
        parsed = _parse(result)
        assert parsed["status"] == "updated"


class TestCreateEpicViaIssueType:
    """jira_create_epic was removed; issue_type="Epic" on jira_create_issue covers it."""

    async def test_epic_issue_type(self, tool_client):
        client, router = tool_client
        route = router.post("/rest/api/2/issue").mock(
            return_value=Response(
                201,
                json={"id": "10002", "key": "PROJ-125", "self": "https://..."},
            )
        )
        result = await client.call_tool(
            "jira_create_issue",
            {"project_key": "PROJ", "summary": "Q1 Auth Overhaul", "issue_type": "Epic"},
        )
        parsed = _parse(result)
        assert parsed["key"] == "PROJ-125"
        body = json.loads(route.calls.last.request.content)
        assert body["fields"]["issuetype"]["name"] == "Epic"


# ═══════════════════════════════════════════════════════
# Issue Links
# ═══════════════════════════════════════════════════════


class TestCreateLink:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.post("/rest/api/2/issueLink").mock(return_value=Response(201))
        result = await client.call_tool(
            "jira_create_link",
            {
                "link_type": "Relates",
                "inward_issue": "PROJ-100",
                "outward_issue": "PROJ-200",
            },
        )
        parsed = _parse(result)
        assert parsed["status"] == "linked"
        assert parsed["type"] == "Relates"


# ═══════════════════════════════════════════════════════
# Agile
# ═══════════════════════════════════════════════════════


class TestGetBoard:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.get("/rest/agile/1.0/board/42").mock(
            return_value=Response(
                200,
                json={"id": 42, "name": "Sprint Board", "type": "scrum"},
            )
        )
        result = await client.call_tool("jira_get_board", {"board_id": 42})
        parsed = _parse(result)
        assert parsed["id"] == 42
        assert parsed["name"] == "Sprint Board"


class TestGetSprint:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.get("/rest/agile/1.0/sprint/7").mock(
            return_value=Response(
                200,
                json={
                    "id": 7,
                    "name": "Sprint 7",
                    "state": "active",
                    "startDate": "2024-01-15",
                    "endDate": "2024-01-29",
                },
            )
        )
        result = await client.call_tool("jira_get_sprint", {"sprint_id": 7})
        parsed = _parse(result)
        assert parsed["id"] == 7
        assert parsed["state"] == "active"


class TestMoveToSprint:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.post("/rest/agile/1.0/sprint/7/issue").mock(return_value=Response(204))
        result = await client.call_tool(
            "jira_move_to_sprint",
            {"sprint_id": 7, "issue_keys": ["PROJ-1", "PROJ-2"]},
        )
        parsed = _parse(result)
        assert parsed["status"] == "moved"
        assert parsed["sprint_id"] == 7


# ═══════════════════════════════════════════════════════
# Users & Metadata
# ═══════════════════════════════════════════════════════


class TestSearchUsers:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.get("/rest/api/2/user/search").mock(
            return_value=Response(
                200,
                json=[
                    {"displayName": "Alice", "accountId": "abc123"},
                    {"displayName": "Bob", "accountId": "def456"},
                ],
            )
        )
        result = await client.call_tool("jira_search_users", {"query": "ali"})
        parsed = _parse(result)
        assert parsed["count"] == 2
        assert parsed["items"][0]["displayName"] == "Alice"


class TestListProjects:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.get("/rest/api/2/project").mock(
            return_value=Response(
                200,
                json=[
                    {"key": "PROJ", "name": "Project Alpha"},
                    {"key": "BETA", "name": "Project Beta"},
                ],
            )
        )
        result = await client.call_tool("jira_list_projects", {})
        parsed = _parse(result)
        assert parsed["count"] == 2
        assert parsed["items"][0]["key"] == "PROJ"


# ═══════════════════════════════════════════════════════
# Error Hints
# ═══════════════════════════════════════════════════════


_ATTACH = ("jira_get_attachments", {"issue_key": "PROJ-123"})
_ATTACH_ROUTE = ("get", "/rest/api/2/issue/PROJ-123")
_CREATE = ("jira_create_issue", {"project_key": "PROJ", "summary": "x"})
_CREATE_ROUTE = ("post", "/rest/api/2/issue")


class TestErrorHints:
    """Each failure mode surfaces a hint naming the fix. Match on a stable fragment,
    not the whole sentence, so rewording a hint does not break the test."""

    @pytest.mark.parametrize(
        ("call", "route", "status", "needles"),
        [
            (_ATTACH, _ATTACH_ROUTE, 401, ["JIRA_PAT"]),
            # The read-only flag is covered by TestReadOnlyGuards below.
            (_ATTACH, _ATTACH_ROUTE, 403, ["precedence", "JIRA_API_TOKEN"]),
            (_ATTACH, _ATTACH_ROUTE, 404, ["not found"]),
            (_ATTACH, _ATTACH_ROUTE, 429, ["Rate limited"]),
            (_CREATE, _CREATE_ROUTE, 409, ["Conflict"]),
            (_CREATE, _CREATE_ROUTE, 422, ["Validation failed"]),
            (
                ("jira_update_issue", {"issue_key": "PROJ-123", "fields": {"summary": ""}}),
                ("put", "/rest/api/2/issue/PROJ-123"),
                400,
                ["Bad request"],
            ),
            # A Confluence 401 must name the Confluence vars, not a Jira-only hint.
            (
                ("confluence_list_calendars", {}),
                ("get", "/rest/calendar-services/1.0/calendar/subcalendars.json"),
                401,
                ["CONFLUENCE_PAT", "CONFLUENCE_API_TOKEN"],
            ),
            # Local validation — no HTTP route is ever hit.
            (
                (
                    "jira_download_attachment",
                    {
                        "content_url": f"{TEST_JIRA_URL}/secure/attachment/1/f.txt",
                        "save_path": "../../../etc/passwd",
                    },
                ),
                None,
                0,
                ["ATLASSIAN_DOWNLOAD_DIR"],
            ),
            # A path outside the upload root names the env var to widen it.
            (
                ("jira_upload_attachment", {"issue_key": "PROJ-123", "file_path": "/no/file"}),
                None,
                0,
                ["ATLASSIAN_UPLOAD_DIR"],
            ),
            # A missing file *inside* the root still reports "File not found".
            (
                ("jira_upload_attachment", {"issue_key": "PROJ-123", "file_path": "nope.txt"}),
                None,
                0,
                ["File not found"],
            ),
        ],
    )
    async def test_hint(self, tool_client, tmp_path, monkeypatch, call, route, status, needles):
        client, router = tool_client
        monkeypatch.chdir(tmp_path)
        if route:
            method, path = route
            getattr(router, method)(path).mock(return_value=Response(status, text="nope"))
        parsed = _err_body(await client.call_tool(*call, raise_on_error=False))
        assert "error" in parsed
        for needle in needles:
            assert needle in parsed["hint"]


# ═══════════════════════════════════════════════════════
# Upload / Download / Delete Attachments
# ═══════════════════════════════════════════════════════


class TestUploadAttachmentHappy:
    async def test_happy_path(self, tool_client, tmp_path, monkeypatch):
        client, router = tool_client
        # Upload root defaults to cwd; point cwd at the dir holding the file.
        monkeypatch.chdir(tmp_path)
        # Create a temp file to upload
        upload_file = tmp_path / "test-upload.txt"
        upload_file.write_text("hello world")

        router.post("/rest/api/2/issue/PROJ-123/attachments").mock(
            return_value=Response(
                200,
                json=[{"id": "1", "filename": "test-upload.txt", "size": 11}],
            )
        )
        result = await client.call_tool(
            "jira_upload_attachment",
            {"issue_key": "PROJ-123", "file_path": str(upload_file)},
        )
        parsed = _parse(result)
        assert isinstance(parsed, list)
        assert parsed[0]["filename"] == "test-upload.txt"


class TestDownloadAttachment:
    URL = f"{TEST_JIRA_URL}/secure/attachment/10000/doc.pdf"

    @staticmethod
    def _mock(router, content: bytes = b"PDF binary content here"):
        router.get("/secure/attachment/10000/doc.pdf").mock(
            return_value=Response(200, content=content)
        )

    async def test_happy_path(self, tool_client, tmp_path, monkeypatch):
        """Default download dir is ./atlassian-downloads/, created on first use."""
        client, router = tool_client
        monkeypatch.chdir(tmp_path)
        file_content = b"PDF binary content here"
        self._mock(router, file_content)

        result = await client.call_tool(
            "jira_download_attachment",
            {"content_url": self.URL, "save_path": "doc.pdf"},
        )
        parsed = _parse(result)
        dest = tmp_path / "atlassian-downloads" / "doc.pdf"
        assert parsed["status"] == "downloaded"
        assert parsed["size"] == len(file_content)
        assert parsed["path"] == str(dest)
        assert dest.read_bytes() == file_content

    async def test_env_dir_wins(self, download_client):
        client, router, dl = download_client
        self._mock(router, b"NEW")
        result = await client.call_tool(
            "jira_download_attachment",
            {"content_url": self.URL, "save_path": "doc.pdf"},
        )
        parsed = _parse(result)
        assert parsed["path"] == str(dl / "doc.pdf")
        assert (dl / "doc.pdf").read_bytes() == b"NEW"

    async def test_no_overwrite_suffix(self, tool_client, tmp_path, monkeypatch):
        client, router = tool_client
        monkeypatch.chdir(tmp_path)
        root = tmp_path / "atlassian-downloads"
        root.mkdir()
        existing = root / "doc.pdf"
        existing.write_bytes(b"ORIGINAL")
        self._mock(router, b"NEW")

        r1 = _parse(
            await client.call_tool(
                "jira_download_attachment", {"content_url": self.URL, "save_path": "doc.pdf"}
            )
        )
        r2 = _parse(
            await client.call_tool(
                "jira_download_attachment", {"content_url": self.URL, "save_path": "doc.pdf"}
            )
        )
        assert existing.read_bytes() == b"ORIGINAL"
        assert r1["path"] == str(root / "doc-1.pdf")
        assert r2["path"] == str(root / "doc-2.pdf")
        assert (root / "doc-1.pdf").read_bytes() == b"NEW"

    @pytest.mark.parametrize(
        ("save_path", "needle"),
        [
            ("sub/doc.pdf", "without directories"),
            (".envrc", "must not start with"),
            (".git/hooks/x", "without directories"),
            ("/etc/passwd", "without directories"),
            ("", "without directories"),
            (".", "without directories"),
            ("..", "without directories"),
        ],
    )
    async def test_rejects_unsafe_save_path(
        self, tool_client, tmp_path, monkeypatch, save_path, needle
    ):
        client, router = tool_client
        monkeypatch.chdir(tmp_path)
        # Validation rejects before any HTTP call, so no route is registered.
        result = await client.call_tool(
            "jira_download_attachment",
            {"content_url": self.URL, "save_path": save_path},
            raise_on_error=False,
        )
        parsed = _err_body(result)
        assert "error" in parsed
        assert needle in parsed["error"]

    async def test_symlink_name_not_followed(self, tool_client, tmp_path, monkeypatch):
        client, router = tool_client
        monkeypatch.chdir(tmp_path)
        root = tmp_path / "atlassian-downloads"
        root.mkdir()
        victim = tmp_path / "victim"
        victim.write_bytes(b"ORIGINAL")
        (root / "doc.pdf").symlink_to(victim)
        self._mock(router, b"NEW")

        result = _parse(
            await client.call_tool(
                "jira_download_attachment", {"content_url": self.URL, "save_path": "doc.pdf"}
            )
        )
        assert victim.read_bytes() == b"ORIGINAL"
        assert result["path"] == str(root / "doc-1.pdf")
        assert (root / "doc-1.pdf").read_bytes() == b"NEW"

    async def test_over_cap_returns_iserror_with_hint(self, tool_client):
        """An oversized attachment is an expected failure: an ``isError`` result
        carrying the size hint, not a raised ToolError. The oversized
        Content-Length is rejected before any body is streamed."""
        client, router = tool_client
        router.get("/secure/attachment/10000/doc.pdf").mock(
            return_value=Response(200, headers={"content-length": str(100 * 1024 * 1024 + 1)})
        )
        result = await client.call_tool(
            "jira_download_attachment",
            {"content_url": self.URL, "save_path": "doc.pdf"},
            raise_on_error=False,
        )
        parsed = _err_body(result)
        assert "too large" in parsed["error"]
        assert parsed["hint"] == "File exceeds the 100MB size limit."


class TestDeleteAttachment:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.delete("/rest/api/2/attachment/123").mock(return_value=Response(204))
        result = await client.call_tool("jira_delete_attachment", {"attachment_id": "123"})
        parsed = _parse(result)
        assert parsed["status"] == "deleted"
        assert parsed["attachment_id"] == "123"


# ═══════════════════════════════════════════════════════
# Metadata: Fields & Backlog
# ═══════════════════════════════════════════════════════


class TestListFields:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.get("/rest/api/2/field").mock(
            return_value=Response(
                200,
                json=[
                    {"id": "summary", "name": "Summary", "custom": False},
                    {"id": "customfield_10001", "name": "Story Points", "custom": True},
                    {"id": "customfield_10002", "name": "Team", "custom": True},
                ],
            )
        )
        result = await client.call_tool("jira_list_fields", {})
        parsed = _parse(result)
        assert parsed["count"] == 3
        assert parsed["items"][0]["id"] == "summary"

    async def test_custom_only_filter(self, tool_client):
        client, router = tool_client
        router.get("/rest/api/2/field").mock(
            return_value=Response(
                200,
                json=[
                    {"id": "summary", "name": "Summary", "custom": False},
                    {"id": "customfield_10001", "name": "Story Points", "custom": True},
                ],
            )
        )
        result = await client.call_tool("jira_list_fields", {"custom_only": True})
        parsed = _parse(result)
        assert parsed["count"] == 1
        assert parsed["items"][0]["id"] == "customfield_10001"

    async def test_search_filter(self, tool_client):
        client, router = tool_client
        router.get("/rest/api/2/field").mock(
            return_value=Response(
                200,
                json=[
                    {"id": "summary", "name": "Summary", "custom": False},
                    {"id": "customfield_10001", "name": "Story Points", "custom": True},
                ],
            )
        )
        result = await client.call_tool("jira_list_fields", {"search": "story"})
        parsed = _parse(result)
        assert parsed["count"] == 1
        assert parsed["items"][0]["name"] == "Story Points"


class TestBacklog:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.get("/rest/agile/1.0/board/42/backlog").mock(
            return_value=Response(
                200,
                json={
                    "issues": [
                        {"key": "PROJ-10", "fields": {"summary": "Backlog item"}},
                    ],
                    "total": 1,
                },
            )
        )
        result = await client.call_tool("jira_backlog", {"board_id": 42})
        parsed = _parse(result)
        # jira_backlog now returns the same envelope as every other list tool
        # instead of leaking the raw Agile payload.
        assert parsed["items"][0]["key"] == "PROJ-10"
        assert parsed["count"] == 1
        assert parsed["total"] == 1
        assert parsed["has_more"] is False
        assert parsed["next_start_at"] is None

    async def test_reports_more_pages(self, tool_client):
        """A capped page must say so, and say where to resume."""
        client, router = tool_client
        router.get("/rest/agile/1.0/board/42/backlog").mock(
            return_value=Response(
                200,
                json={
                    "issues": [{"key": f"PROJ-{n}"} for n in range(50)],
                    "startAt": 0,
                    "total": 120,
                },
            )
        )
        result = await client.call_tool("jira_backlog", {"board_id": 42})
        parsed = _parse(result)
        assert parsed["has_more"] is True
        assert parsed["next_start_at"] == 50
        assert parsed["total"] == 120


# ═══════════════════════════════════════════════════════
# Agile: Board Config
# ═══════════════════════════════════════════════════════


class TestBoardConfig:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.get("/rest/agile/1.0/board/42/configuration").mock(
            return_value=Response(
                200,
                json={
                    "id": 42,
                    "name": "Sprint Board Config",
                    "columnConfig": {
                        "columns": [
                            {"name": "To Do", "statuses": [{"id": "1"}]},
                            {"name": "Done", "statuses": [{"id": "3"}]},
                        ]
                    },
                },
            )
        )
        result = await client.call_tool("jira_board_config", {"board_id": 42})
        parsed = _parse(result)
        assert parsed["id"] == 42
        assert len(parsed["columnConfig"]["columns"]) == 2


# ═══════════════════════════════════════════════════════
# Delete Link happy path
# ═══════════════════════════════════════════════════════


class TestDeleteLinkHappy:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.delete("/rest/api/2/issueLink/12345").mock(return_value=Response(204))
        result = await client.call_tool("jira_delete_link", {"link_id": "12345"})
        parsed = _parse(result)
        assert parsed["status"] == "deleted"
        assert parsed["link_id"] == "12345"


# ═══════════════════════════════════════════════════════
# Confluence: Calendars
# ═══════════════════════════════════════════════════════

# Sample calendar data used across Confluence tests
_SAMPLE_CALENDARS = {
    "payload": [
        {
            "subCalendar": {
                "id": "cal-1",
                "name": "Team Leaves",
                "typeKey": "leaves",
                "spaceKey": "ENG",
                "spaceName": "Engineering",
            },
            "childSubCalendars": [
                {
                    "subCalendar": {
                        "id": "child-1",
                        "name": "Vacation leaves",
                        "typeKey": "leaves",
                    }
                }
            ],
        },
        {
            "subCalendar": {
                "id": "cal-2",
                "name": "Release Calendar",
                "typeKey": "events",
                "spaceKey": "REL",
                "spaceName": "Releases",
            },
            "childSubCalendars": [],
        },
    ]
}

_SAMPLE_EVENTS = {
    "events": [
        {
            "id": "ev-1",
            "title": "Alice Vacation",
            "eventType": "leaves",
            "className": "leaves",
            "start": "2024-03-01T00:00:00",
            "end": "2024-03-05T00:00:00",
            "subCalendarId": "child-1",
            "allDay": True,
            "invitees": [{"displayName": "Alice Smith", "email": "alice@example.com"}],
        },
        {
            "id": "ev-2",
            "title": "Bob PTO",
            "eventType": "leaves",
            "className": "leaves",
            "start": "2024-03-03T00:00:00",
            "end": "2024-03-04T00:00:00",
            "subCalendarId": "child-1",
            "allDay": True,
            "invitees": [{"displayName": "Bob Jones", "email": "bob@example.com"}],
        },
    ]
}


def _mock_confluence_calendars_and_events(router):
    """Set up standard calendar + events mocks on a Confluence router."""
    router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
        return_value=Response(200, json=_SAMPLE_CALENDARS)
    )
    router.get("/rest/calendar-services/1.0/calendar/events.json").mock(
        return_value=Response(200, json=_SAMPLE_EVENTS)
    )


class TestConfluenceListCalendars:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
            return_value=Response(200, json=_SAMPLE_CALENDARS)
        )
        result = await client.call_tool("confluence_list_calendars", {})
        parsed = _parse(result)
        assert parsed["count"] == 2
        assert parsed["items"][0]["name"] == "Team Leaves"
        assert parsed["items"][0]["child_count"] == 1

    async def test_filter_type(self, tool_client):
        client, router = tool_client
        router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
            return_value=Response(200, json=_SAMPLE_CALENDARS)
        )
        result = await client.call_tool("confluence_list_calendars", {"filter_type": "leaves"})
        parsed = _parse(result)
        assert parsed["count"] == 1
        assert parsed["items"][0]["name"] == "Team Leaves"

    async def test_search_by_name(self, tool_client):
        client, router = tool_client
        router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
            return_value=Response(200, json=_SAMPLE_CALENDARS)
        )
        result = await client.call_tool("confluence_list_calendars", {"search": "release"})
        parsed = _parse(result)
        assert parsed["count"] == 1
        assert parsed["items"][0]["name"] == "Release Calendar"

    async def test_search_by_space(self, tool_client):
        client, router = tool_client
        router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
            return_value=Response(200, json=_SAMPLE_CALENDARS)
        )
        result = await client.call_tool("confluence_list_calendars", {"search": "ENG"})
        parsed = _parse(result)
        assert parsed["count"] == 1
        assert parsed["items"][0]["space_key"] == "ENG"


class TestConfluenceGetTimeOff:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        _mock_confluence_calendars_and_events(router)
        result = await client.call_tool(
            "confluence_get_time_off",
            {"start_date": "2024-03-01", "end_date": "2024-03-10"},
        )
        parsed = _parse(result)
        assert parsed["start"] == "2024-03-01"
        assert parsed["end"] == "2024-03-10"
        assert len(parsed["events"]) == 2

    async def test_group_by_person(self, tool_client):
        client, router = tool_client
        _mock_confluence_calendars_and_events(router)
        result = await client.call_tool(
            "confluence_get_time_off",
            {
                "start_date": "2024-03-01",
                "end_date": "2024-03-10",
                "group_by_person": True,
            },
        )
        parsed = _parse(result)
        assert "people" in parsed
        assert "Alice Smith" in parsed["people"]
        assert "Bob Jones" in parsed["people"]

    async def test_free_text_date_rejected(self, tool_client):
        """Free-text dates return a structured error naming the accepted formats."""
        client, _ = tool_client
        result = await client.call_tool(
            "confluence_get_time_off",
            {"start_date": "Jan 1, 2024", "end_date": "2024-03-10"},
            raise_on_error=False,
        )
        parsed = _err_body(result)
        assert "Unrecognised date 'Jan 1, 2024'" in parsed["error"]
        assert "YYYY-MM-DD" in parsed["error"]


class TestConfluenceGetTimeOffPerson:
    """The person filter (formerly confluence_get_person_time_off) matches names exactly."""

    async def test_person_exact_match(self, tool_client):
        client, router = tool_client
        _mock_confluence_calendars_and_events(router)
        result = await client.call_tool(
            "confluence_get_time_off",
            {"start_date": "2024-03-01", "end_date": "2024-03-10", "person": "Alice Smith"},
        )
        parsed = _parse(result)
        assert len(parsed["events"]) == 1
        assert parsed["events"][0]["person_name"] == "Alice Smith"

    async def test_person_partial_name_does_not_match(self, tool_client):
        client, router = tool_client
        _mock_confluence_calendars_and_events(router)
        result = await client.call_tool(
            "confluence_get_time_off",
            {"start_date": "2024-03-01", "end_date": "2024-03-10", "person": "Alice"},
        )
        parsed = _parse(result)
        assert parsed["events"] == []

    async def test_who_is_out_via_single_day(self, tool_client):
        client, router = tool_client
        _mock_confluence_calendars_and_events(router)
        result = await client.call_tool(
            "confluence_get_time_off",
            {"start_date": "2024-03-03", "end_date": "2024-03-03", "group_by_person": True},
        )
        parsed = _parse(result)
        assert set(parsed["people"]) == {"Alice Smith", "Bob Jones"}


class TestConfluenceSprintCapacity:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        _mock_confluence_calendars_and_events(router)
        result = await client.call_tool(
            "confluence_sprint_capacity",
            {
                "team_members": ["Alice Smith", "Bob Jones", "Charlie Brown"],
                "sprint_start": "2024-03-04",
                "sprint_end": "2024-03-15",
            },
        )
        parsed = _parse(result)
        # Sprint 2024-03-04 (Mon) .. 2024-03-15 (Fri), 5-day week: ten working
        # days (two Mon-Fri weeks). Exact numbers pin the weekend mapping
        # (``range(working_days_per_week, 7)``) — a one-day shift there changes
        # working_days and every figure below.
        assert parsed["sprint"]["working_days"] == 10
        assert parsed["team"]["members"] == 3
        assert parsed["team"]["max_capacity_days"] == 30
        # Alice: ev-1 clamps to Mon 03-04 + Tue 03-05 = 2 off. Bob: ev-2 clamps to
        # Mon 03-04 = 1 off. Charlie: none.
        assert parsed["team"]["total_days_off"] == 3
        assert parsed["team"]["available_capacity_days"] == 27
        assert parsed["team"]["capacity_percentage"] == 90.0
        by_member = {m["member"]: m for m in parsed["member_breakdown"]}
        assert by_member["Alice Smith"]["days_off"] == 2
        assert by_member["Alice Smith"]["available_days"] == 8
        assert by_member["Bob Jones"]["days_off"] == 1
        assert by_member["Bob Jones"]["available_days"] == 9
        assert by_member["Charlie Brown"]["days_off"] == 0
        assert by_member["Charlie Brown"]["available_days"] == 10

    async def test_no_time_off(self, tool_client):
        client, router = tool_client
        router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
            return_value=Response(200, json=_SAMPLE_CALENDARS)
        )
        # Return no events
        router.get("/rest/calendar-services/1.0/calendar/events.json").mock(
            return_value=Response(200, json={"events": []})
        )
        result = await client.call_tool(
            "confluence_sprint_capacity",
            {
                "team_members": ["Alice Smith"],
                "sprint_start": "2024-03-04",
                "sprint_end": "2024-03-08",
            },
        )
        parsed = _parse(result)
        assert parsed["team"]["total_days_off"] == 0
        assert parsed["team"]["capacity_percentage"] == 100.0


# A space calendar as Team Calendars returns it: a parent without events and two
# custom children that carry them.
_SPACE_CALENDARS = {
    "payload": [
        {
            "subCalendar": {
                "id": "p-1",
                "name": "Operations",
                "spaceKey": "OPS",
                "customEventTypes": [
                    {"customEventTypeId": "t-maint", "title": "Maintenance window"}
                ],
            },
            "childSubCalendars": [
                {"subCalendar": {"id": "c-maint", "name": "Maintenance windows"}},
                {"subCalendar": {"id": "c-pay", "name": "Payroll"}},
            ],
        },
        {"subCalendar": {"id": "p-2", "name": "Absences", "spaceKey": "OPS"}},
    ]
}

_EVENTS_BY_CALENDAR = {
    "c-maint": {
        "success": True,
        "events": [
            {
                "id": "e-2",
                "title": "SAP maintenance",
                "start": "2024-03-07T22:00:00.000+01:00",
                "end": "2024-03-08T02:00:00.000+01:00",
                "allDay": False,
                "eventType": "custom",
                "className": "campaign",
                "customEventTypeId": "t-maint",
            },
            # events.json pads the range to whole calendar views; this one lies
            # after end_date and must be dropped.
            {
                "id": "e-3",
                "title": "April maintenance",
                "start": "2024-04-03T22:00:00.000+02:00",
                "end": "2024-04-04T02:00:00.000+02:00",
                "eventType": "custom",
                "className": "campaign",
            },
        ],
    },
    "c-pay": {
        "success": True,
        "events": [
            {
                "id": "e-1",
                "title": "Payroll run",
                "start": "2024-03-05T07:00:00.000+01:00",
                "end": "2024-03-05T08:00:00.000+01:00",
                "eventType": "custom",
                "className": "events",
                "invitees": [{"displayName": "Alice Smith"}],
            }
        ],
    },
    # An empty calendar answers without an "events" key.
    "p-2": {"success": True},
}


def _mock_space_calendars(router, *, events: bool = True):
    subcals = router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
        return_value=Response(200, json=_SPACE_CALENDARS)
    )
    if not events:
        return subcals, None
    events_route = router.get("/rest/calendar-services/1.0/calendar/events.json").mock(
        side_effect=lambda request: Response(
            200, json=_EVENTS_BY_CALENDAR[request.url.params["subCalendarId"]]
        )
    )
    return subcals, events_route


class TestConfluenceGetCalendarEvents:
    async def test_all_calendars_one_request_each(self, tool_client):
        client, router = tool_client
        _, events = _mock_space_calendars(router)
        result = await client.call_tool(
            "confluence_get_calendar_events",
            {"start_date": "2024-03-01", "end_date": "2024-03-31"},
        )
        parsed = _parse(result)
        # events.json honours only the first subCalendarId, so each child is
        # queried on its own; the parent with children is never queried. The
        # requests run concurrently, so their order is not fixed.
        queried = sorted(c.request.url.params.get_list("subCalendarId") for c in events.calls)
        assert queried == [["c-maint"], ["c-pay"], ["p-2"]]
        assert parsed["count"] == 2
        assert [e["title"] for e in parsed["events"]] == ["Payroll run", "SAP maintenance"]
        # Category is the custom event type's title when there is one, else className.
        assert [e["category"] for e in parsed["events"]] == ["events", "Maintenance window"]
        first = parsed["events"][0]
        assert first["calendar_name"] == "Payroll"
        assert first["parent_calendar_name"] == "Operations"
        assert first["invitees"] == ["Alice Smith"]

    async def test_space_key_sets_space_context(self, tool_client):
        client, router = tool_client
        subcals, _ = _mock_space_calendars(router)
        await client.call_tool(
            "confluence_get_calendar_events",
            {"start_date": "2024-03-01", "end_date": "2024-03-31", "space_key": "OPS"},
        )
        params = subcals.calls.last.request.url.params
        assert params["calendarContext"] == "spaceCalendars"
        assert params["viewingSpaceKey"] == "OPS"

    async def test_calendar_filter_by_child_name(self, tool_client):
        client, router = tool_client
        _, events = _mock_space_calendars(router)
        result = await client.call_tool(
            "confluence_get_calendar_events",
            {"start_date": "2024-03-01", "end_date": "2024-03-31", "calendar": "maintenance"},
        )
        parsed = _parse(result)
        assert events.call_count == 1
        assert [e["title"] for e in parsed["events"]] == ["SAP maintenance"]

    async def test_calendar_filter_by_parent_expands_children(self, tool_client):
        client, router = tool_client
        _, events = _mock_space_calendars(router)
        result = await client.call_tool(
            "confluence_get_calendar_events",
            {"start_date": "2024-03-01", "end_date": "2024-03-31", "calendar": "p-1"},
        )
        assert events.call_count == 2
        assert _parse(result)["count"] == 2

    async def test_free_text_date_rejected(self, tool_client):
        client, _ = tool_client
        result = await client.call_tool(
            "confluence_get_calendar_events",
            {"start_date": "March", "end_date": "2024-03-31"},
            raise_on_error=False,
        )
        assert "Unrecognised date 'March'" in _err_body(result)["error"]

    async def test_unknown_calendar_is_an_error(self, tool_client):
        client, router = tool_client
        _mock_space_calendars(router, events=False)
        result = await client.call_tool(
            "confluence_get_calendar_events",
            {
                "start_date": "2024-03-01",
                "end_date": "2024-03-31",
                "space_key": "OPS",
                "calendar": "nope",
            },
            raise_on_error=False,
        )
        error = _err_body(result)["error"]
        assert "No calendar matches 'nope' in space 'OPS'" in error
        assert "confluence_list_calendars" in error

    async def test_malformed_calendar_entries(self, tool_client):
        """A child without an id is skipped; a null name does not break matching."""
        client, router = tool_client
        payload = {
            "payload": [
                {
                    "subCalendar": {"id": "p-1", "name": None},
                    "childSubCalendars": [
                        {"subCalendar": {"name": "No id"}},
                        {"subCalendar": {"id": "c-1", "name": None}},
                        {"subCalendar": {"id": "c-2", "name": "Holidays"}},
                    ],
                },
            ]
        }
        router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
            return_value=Response(200, json=payload)
        )
        events = router.get("/rest/calendar-services/1.0/calendar/events.json").mock(
            return_value=Response(200, json={"success": True})
        )
        result = await client.call_tool(
            "confluence_get_calendar_events",
            {"start_date": "2024-03-01", "end_date": "2024-03-31", "calendar": "holi"},
        )
        assert _parse(result)["count"] == 0
        assert [c.request.url.params["subCalendarId"] for c in events.calls] == ["c-2"]


# Real all-day events as events.json returns them (Team Calendars for Data Center,
# userTimeZoneId=Europe/Zurich): "end" is inclusive. A one-day holiday has start
# and end on the same day; a two-day event ends on its second day. The iCal export
# of the same events has the exclusive DTEND (20261226 and 20261211).
_ALL_DAY_EVENTS = {
    "success": True,
    "events": [
        {
            "id": "a-1",
            "title": "Weihnachtstag",
            "allDay": True,
            "start": "2026-12-25T00:00:00.000+01:00",
            "end": "2026-12-25T00:00:00.000+01:00",
            "eventType": "custom",
        },
        {
            "id": "a-2",
            "title": "PI Planning",
            "allDay": True,
            "start": "2026-12-09T00:00:00.000+01:00",
            "end": "2026-12-10T00:00:00.000+01:00",
            "eventType": "custom",
        },
        # A timed event that ends exactly at midnight ends before that day starts.
        {
            "id": "t-1",
            "title": "Night job",
            "allDay": False,
            "start": "2026-12-09T22:00:00.000+01:00",
            "end": "2026-12-10T00:00:00.000+01:00",
            "eventType": "custom",
        },
    ],
}


class TestCalendarEventsRange:
    @pytest.mark.parametrize(
        ("start", "end", "titles"),
        [
            ("2026-12-25", "2026-12-25", ["Weihnachtstag"]),
            # Inclusive end: the one-day holiday on 25 Dec is not in 26-31 Dec.
            ("2026-12-26", "2026-12-31", []),
            # The two-day event runs 9-10 Dec, so a query for the 10th keeps it;
            # the timed event that ends at 00:00 on the 10th does not.
            ("2026-12-10", "2026-12-12", ["PI Planning"]),
            ("2026-12-11", "2026-12-12", []),
            ("2026-12-09", "2026-12-09", ["PI Planning", "Night job"]),
        ],
    )
    async def test_all_day_end_is_inclusive(self, tool_client, start, end, titles):
        client, router = tool_client
        router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
            return_value=Response(
                200, json={"payload": [{"subCalendar": {"id": "c", "name": "C"}}]}
            )
        )
        router.get("/rest/calendar-services/1.0/calendar/events.json").mock(
            return_value=Response(200, json=_ALL_DAY_EVENTS)
        )
        result = await client.call_tool(
            "confluence_get_calendar_events", {"start_date": start, "end_date": end}
        )
        assert sorted(e["title"] for e in _parse(result)["events"]) == sorted(titles)


class TestTimeOffAcrossLeaveCalendars:
    async def test_one_request_per_leave_child(self, tool_client):
        """events.json answers only for the first subCalendarId, so each leave
        calendar needs its own request — else the second team's leave is lost."""
        client, router = tool_client
        payload = {
            "payload": [
                {
                    "subCalendar": {"id": "cal-1", "name": "Team Leaves"},
                    "childSubCalendars": [
                        {"subCalendar": {"id": "child-a", "name": "Team A leaves"}},
                        {"subCalendar": {"id": "child-b", "name": "Team B leaves"}},
                    ],
                }
            ]
        }
        by_child = {
            "child-a": {"display": "Alice Smith", "id": "ev-a"},
            "child-b": {"display": "Bob Jones", "id": "ev-b"},
        }
        router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
            return_value=Response(200, json=payload)
        )

        def answer(request):
            ids = request.url.params.get_list("subCalendarId")
            assert len(ids) == 1
            who = by_child[ids[0]]
            event = {
                "id": who["id"],
                "title": "Vacation",
                "eventType": "leaves",
                "start": "2024-03-04T00:00:00",
                "end": "2024-03-05T00:00:00",
                "subCalendarId": ids[0],
                "invitees": [{"displayName": who["display"]}],
            }
            return Response(200, json={"events": [event]})

        events = router.get("/rest/calendar-services/1.0/calendar/events.json").mock(
            side_effect=answer
        )
        result = await client.call_tool(
            "confluence_get_time_off", {"start_date": "2024-03-01", "end_date": "2024-03-10"}
        )
        assert events.call_count == 2
        names = sorted(e["person_name"] for e in _parse(result)["events"])
        assert names == ["Alice Smith", "Bob Jones"]


class TestConfluenceListCalendarsSpace:
    async def test_space_key_and_child_names(self, tool_client):
        client, router = tool_client
        subcals, _ = _mock_space_calendars(router, events=False)
        result = await client.call_tool("confluence_list_calendars", {"space_key": "OPS"})
        parsed = _parse(result)
        assert subcals.calls.last.request.url.params["viewingSpaceKey"] == "OPS"
        assert parsed["items"][0]["children"] == [
            {"id": "c-maint", "name": "Maintenance windows"},
            {"id": "c-pay", "name": "Payroll"},
        ]

    async def test_without_space_key_no_context(self, tool_client):
        client, router = tool_client
        subcals, _ = _mock_space_calendars(router, events=False)
        await client.call_tool("confluence_list_calendars", {})
        assert "viewingSpaceKey" not in subcals.calls.last.request.url.params

    async def test_null_names_do_not_break_filters(self, tool_client):
        client, router = tool_client
        payload = {
            "payload": [
                {"subCalendar": {"id": "a", "name": None, "typeKey": None}},
                {"subCalendar": {"id": "b", "name": "Releases", "spaceKey": "REL"}},
            ]
        }
        router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
            return_value=Response(200, json=payload)
        )
        result = await client.call_tool(
            "confluence_list_calendars", {"filter_type": "rel", "search": "rel"}
        )
        assert [i["id"] for i in _parse(result)["items"]] == ["b"]


class TestLeaveKeywords:
    async def test_configured_keyword_finds_german_calendar(self):
        config = ConfluenceConfig(
            url=TEST_CONFLUENCE_URL, token="t", leave_keywords=("abwesenheit",)
        )
        client = ConfluenceExtendedClient(config)
        payload = {"payload": [{"subCalendar": {"id": "a", "name": "Abwesenheiten"}}]}
        async with respx.mock(base_url=TEST_CONFLUENCE_URL) as router:
            router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
                return_value=Response(200, json=payload)
            )
            assert len(await client.get_all_leave_calendars()) == 1
        await client.close()


# ═══════════════════════════════════════════════════════
# Versions
# ═══════════════════════════════════════════════════════


class TestGetProjectVersions:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.get("/rest/api/2/project/PROJ/versions").mock(
            return_value=Response(
                200,
                json=[
                    {"id": "100", "name": "v1.0.0", "released": True},
                    {"id": "101", "name": "v2.0.0", "released": False},
                ],
            )
        )
        result = await client.call_tool("jira_get_project_versions", {"project_key": "PROJ"})
        parsed = _parse(result)
        assert parsed["count"] == 2
        assert parsed["items"][0]["name"] == "v1.0.0"


class TestCreateVersion:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.post("/rest/api/2/version").mock(
            return_value=Response(
                201,
                json={"id": "200", "name": "v3.0.0", "project": "PROJ", "released": True},
            )
        )
        result = await client.call_tool(
            "jira_create_version",
            {
                "project_key": "PROJ",
                "name": "v3.0.0",
                "release_date": "2026-03-04",
                "released": True,
            },
        )
        parsed = _parse(result)
        assert parsed["id"] == "200"
        assert parsed["name"] == "v3.0.0"


class TestUpdateVersion:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.put("/rest/api/2/version/200").mock(
            return_value=Response(
                200,
                json={"id": "200", "name": "v3.0.0", "released": True},
            )
        )
        result = await client.call_tool(
            "jira_update_version",
            {"version_id": "200", "released": True},
        )
        parsed = _parse(result)
        assert parsed["released"] is True


# ═══════════════════════════════════════════════════════
# Write guard reads the calling tool's own config
# ═══════════════════════════════════════════════════════


def _guard_ctx(*, jira_read_only: bool, confluence_read_only: bool) -> Any:
    """Minimal stand-in for a FastMCP Context — _check_write only reads the lifespan dict."""
    lifespan = {
        "jira_config": JiraConfig(url=TEST_JIRA_URL, token=TEST_TOKEN, read_only=jira_read_only),
        "confluence_config": ConfluenceConfig(
            url=TEST_CONFLUENCE_URL, token=TEST_TOKEN, read_only=confluence_read_only
        ),
    }
    return SimpleNamespace(lifespan_context=lifespan)


class TestWriteGuardPerService:
    """Jira and Confluence read-only flags are independent — each guard reads its own."""

    def test_confluence_read_only_blocks_only_confluence(self):
        ctx = _guard_ctx(jira_read_only=False, confluence_read_only=True)
        with pytest.raises(WriteDisabledError):
            _check_write(ctx, "confluence")
        _check_write(ctx, "jira")  # Jira is writable — must not raise

    def test_jira_read_only_blocks_only_jira(self):
        ctx = _guard_ctx(jira_read_only=True, confluence_read_only=False)
        with pytest.raises(WriteDisabledError):
            _check_write(ctx, "jira")
        _check_write(ctx, "confluence")  # Confluence is writable — must not raise


class TestNotConfiguredMessage:
    """Cloud basic auth is a supported way to configure either product — say so."""

    @staticmethod
    def _ctx() -> Any:
        lifespan = {"jira_client": None, "confluence_client": None}
        return SimpleNamespace(lifespan_context=lifespan)

    def test_jira_message_names_both_auth_modes(self):
        with pytest.raises(ValueError, match="not configured") as exc:
            _get_jira(self._ctx())
        assert "JIRA_USERNAME" in str(exc.value)
        assert "JIRA_API_TOKEN" in str(exc.value)
        assert "JIRA_PAT" in str(exc.value)

    def test_confluence_message_names_both_auth_modes(self):
        with pytest.raises(ValueError, match="not configured") as exc:
            _get_confluence(self._ctx())
        assert "CONFLUENCE_USERNAME" in str(exc.value)
        assert "CONFLUENCE_API_TOKEN" in str(exc.value)
        assert "CONFLUENCE_PAT" in str(exc.value)


# ═══════════════════════════════════════════════════════
# Team Calendars add-on missing
# ═══════════════════════════════════════════════════════


class TestTeamCalendarsMissing:
    """All three Confluence tools go through /rest/calendar-services/1.0/ (Team Calendars)."""

    @pytest.mark.parametrize(
        ("tool", "args"),
        [
            ("confluence_list_calendars", {}),
            (
                "confluence_get_time_off",
                {"start_date": "2025-01-01", "end_date": "2025-01-31"},
            ),
            (
                "confluence_sprint_capacity",
                {
                    "team_members": ["Alice"],
                    "sprint_start": "2025-01-01",
                    "sprint_end": "2025-01-14",
                },
            ),
        ],
    )
    async def test_404_explains_the_addon(self, tool_client, tool, args):
        client, router = tool_client
        router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
            return_value=Response(404, text="not found")
        )
        parsed = _err_body(await client.call_tool(tool, args, raise_on_error=False))
        assert parsed["status_code"] == 404
        assert "Team Calendars" in parsed["error"]
        assert "Team Calendars add-on" in parsed["hint"]
        # The generic Jira 404 hint must not leak into a Confluence failure.
        assert "jira_list_projects" not in parsed["hint"]
