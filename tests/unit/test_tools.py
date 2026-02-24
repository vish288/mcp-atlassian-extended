"""Tool-level tests — call @mcp.tool functions via FastMCP Client with mocked API."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import pytest
import respx
from fastmcp import Client, FastMCP
from httpx import Response

from mcp_atlassian_extended.clients.confluence import ConfluenceExtendedClient
from mcp_atlassian_extended.clients.jira import JiraExtendedClient
from mcp_atlassian_extended.config import ConfluenceConfig, JiraConfig

TEST_JIRA_URL = "https://jira.example.com"
TEST_CONFLUENCE_URL = "https://confluence.example.com"
TEST_TOKEN = "test-token"


def _make_mcp(*, read_only: bool = False) -> tuple[FastMCP, Any]:
    """Build a FastMCP server with mocked lifespan."""
    jira_config = JiraConfig(url=TEST_JIRA_URL, token=TEST_TOKEN, read_only=read_only)
    confluence_config = ConfluenceConfig(
        url=TEST_CONFLUENCE_URL, token=TEST_TOKEN, read_only=read_only
    )
    jira_client = JiraExtendedClient(jira_config)
    confluence_client = ConfluenceExtendedClient(confluence_config)

    @asynccontextmanager
    async def mock_lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
        try:
            yield {
                "jira_client": jira_client,
                "jira_config": jira_config,
                "confluence_client": confluence_client,
                "confluence_config": confluence_config,
            }
        finally:
            await jira_client.close()
            await confluence_client.close()

    from mcp_atlassian_extended.servers import mcp

    original_lifespan = mcp._lifespan
    mcp._lifespan = mock_lifespan
    return mcp, original_lifespan


@pytest.fixture
async def tool_client():
    """FastMCP test client with mocked lifespan and respx-mocked HTTP."""
    mcp, original_lifespan = _make_mcp()
    with respx.mock(base_url=TEST_JIRA_URL) as router:
        async with Client(mcp) as client:
            yield client, router
    mcp._lifespan = original_lifespan


@pytest.fixture
async def readonly_client():
    """FastMCP test client in read-only mode."""
    mcp, original_lifespan = _make_mcp(read_only=True)
    with respx.mock(base_url=TEST_JIRA_URL) as router:
        async with Client(mcp) as client:
            yield client, router
    mcp._lifespan = original_lifespan


@pytest.fixture
async def confluence_client():
    """FastMCP test client with Confluence router."""
    mcp, original_lifespan = _make_mcp()
    with respx.mock(base_url=TEST_CONFLUENCE_URL) as router:
        async with Client(mcp) as client:
            yield client, router
    mcp._lifespan = original_lifespan


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
        result = await client.call_tool("jira_get_attachments", {"issue_key": "INVALID-999"})
        parsed = _parse(result)
        assert "error" in parsed


class TestUploadAttachment:
    async def test_read_only_blocked(self, readonly_client):
        client, router = readonly_client
        result = await client.call_tool(
            "jira_upload_attachment",
            {"issue_key": "PROJ-123", "file_path": "./test-upload.txt"},
        )
        parsed = _parse(result)
        assert "error" in parsed
        assert "read-only" in parsed["error"].lower() or "disabled" in parsed["error"].lower()


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

    async def test_read_only_blocked(self, readonly_client):
        client, router = readonly_client
        result = await client.call_tool(
            "jira_create_issue",
            {
                "project_key": "PROJ",
                "summary": "Test issue",
            },
        )
        parsed = _parse(result)
        assert "error" in parsed


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


class TestCreateEpic:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.post("/rest/api/2/issue").mock(
            return_value=Response(
                201,
                json={"id": "10002", "key": "PROJ-125", "self": "https://..."},
            )
        )
        result = await client.call_tool(
            "jira_create_epic",
            {"project_key": "PROJ", "epic_name": "Q1 Auth Overhaul"},
        )
        parsed = _parse(result)
        assert parsed["key"] == "PROJ-125"


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


class TestDeleteLink:
    async def test_read_only_blocked(self, readonly_client):
        client, router = readonly_client
        result = await client.call_tool("jira_delete_link", {"link_id": "12345"})
        parsed = _parse(result)
        assert "error" in parsed


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

    async def test_read_only_blocked(self, readonly_client):
        client, router = readonly_client
        result = await client.call_tool(
            "jira_move_to_sprint",
            {"sprint_id": 7, "issue_keys": ["PROJ-1"]},
        )
        parsed = _parse(result)
        assert "error" in parsed


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


class TestErrorHints:
    async def test_auth_error_hint(self, tool_client):
        client, router = tool_client
        router.get("/rest/api/2/issue/PROJ-123").mock(
            return_value=Response(401, text="Unauthorized")
        )
        result = await client.call_tool("jira_get_attachments", {"issue_key": "PROJ-123"})
        parsed = _parse(result)
        assert "error" in parsed
        assert "hint" in parsed
        assert "authentication" in parsed["hint"].lower() or "JIRA_PAT" in parsed["hint"]

    async def test_not_found_hint(self, tool_client):
        client, router = tool_client
        router.get("/rest/api/2/issue/GONE-404").mock(
            return_value=Response(404, json={"errorMessages": ["Issue Does Not Exist"]})
        )
        result = await client.call_tool("jira_get_attachments", {"issue_key": "GONE-404"})
        parsed = _parse(result)
        assert "error" in parsed
        assert "hint" in parsed
        assert "not found" in parsed["hint"].lower() or "PROJ-123" in parsed["hint"]

    async def test_rate_limit_hint(self, tool_client):
        client, router = tool_client
        router.get("/rest/api/2/issue/PROJ-123").mock(
            return_value=Response(429, text="Too Many Requests")
        )
        result = await client.call_tool("jira_get_attachments", {"issue_key": "PROJ-123"})
        parsed = _parse(result)
        assert "error" in parsed
        assert "hint" in parsed
        assert "rate" in parsed["hint"].lower() or "wait" in parsed["hint"].lower()

    async def test_conflict_hint(self, tool_client):
        client, router = tool_client
        router.post("/rest/api/2/issue").mock(return_value=Response(409, text="Conflict"))
        result = await client.call_tool(
            "jira_create_issue",
            {"project_key": "PROJ", "summary": "Dup"},
        )
        parsed = _parse(result)
        assert "error" in parsed
        assert "hint" in parsed
        assert "conflict" in parsed["hint"].lower()

    async def test_write_disabled_hint(self, readonly_client):
        client, router = readonly_client
        result = await client.call_tool(
            "jira_create_issue",
            {"project_key": "PROJ", "summary": "Test"},
        )
        parsed = _parse(result)
        assert "error" in parsed
        assert "hint" in parsed
        assert "read-only" in parsed["hint"].lower()

    async def test_bad_request_hint(self, tool_client):
        client, router = tool_client
        router.put("/rest/api/2/issue/PROJ-123").mock(
            return_value=Response(400, json={"errors": {"summary": "Field required"}})
        )
        result = await client.call_tool(
            "jira_update_issue",
            {"issue_key": "PROJ-123", "fields": {"summary": ""}},
        )
        parsed = _parse(result)
        assert "error" in parsed
        assert "hint" in parsed
        assert "bad request" in parsed["hint"].lower() or "required" in parsed["hint"].lower()

    async def test_path_traversal_hint(self, tool_client, tmp_path, monkeypatch):
        """Download with '..' path triggers ValueError with traversal hint."""
        client, router = tool_client
        monkeypatch.chdir(tmp_path)
        result = await client.call_tool(
            "jira_download_attachment",
            {
                "content_url": f"{TEST_JIRA_URL}/secure/attachment/1/f.txt",
                "save_path": "../../../etc/passwd",
            },
        )
        parsed = _parse(result)
        assert "error" in parsed
        assert "hint" in parsed
        assert "traversal" in parsed["hint"].lower()

    async def test_file_not_found_hint(self, tool_client):
        """Upload with non-existent file triggers FileNotFoundError hint."""
        client, router = tool_client
        result = await client.call_tool(
            "jira_upload_attachment",
            {"issue_key": "PROJ-123", "file_path": "/nonexistent/path/file.txt"},
        )
        parsed = _parse(result)
        assert "error" in parsed
        assert "hint" in parsed
        assert "file" in parsed["hint"].lower() or "not found" in parsed["hint"].lower()

    async def test_confluence_auth_error_hint(self, confluence_client):
        """Confluence 401 triggers auth hint."""
        client, router = confluence_client
        router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
            return_value=Response(401, text="Unauthorized")
        )
        result = await client.call_tool("confluence_list_calendars", {})
        parsed = _parse(result)
        assert "error" in parsed
        assert "hint" in parsed
        assert "authentication" in parsed["hint"].lower() or "PAT" in parsed["hint"]

    async def test_validation_422_hint(self, tool_client):
        client, router = tool_client
        router.post("/rest/api/2/issue").mock(
            return_value=Response(422, json={"errors": {"field": "invalid"}})
        )
        result = await client.call_tool(
            "jira_create_issue",
            {"project_key": "PROJ", "summary": "Bad fields"},
        )
        parsed = _parse(result)
        assert "error" in parsed
        assert "hint" in parsed
        assert "validation" in parsed["hint"].lower() or "format" in parsed["hint"].lower()


# ═══════════════════════════════════════════════════════
# Upload / Download / Delete Attachments
# ═══════════════════════════════════════════════════════


class TestUploadAttachmentHappy:
    async def test_happy_path(self, tool_client, tmp_path):
        client, router = tool_client
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
    async def test_happy_path(self, tool_client, tmp_path, monkeypatch):
        client, router = tool_client
        content_url = f"{TEST_JIRA_URL}/secure/attachment/10000/doc.pdf"
        file_content = b"PDF binary content here"

        router.get("/secure/attachment/10000/doc.pdf").mock(
            return_value=Response(200, content=file_content)
        )

        # Monkeypatch cwd so the relative save_path resolves inside tmp_path
        monkeypatch.chdir(tmp_path)

        result = await client.call_tool(
            "jira_download_attachment",
            {"content_url": content_url, "save_path": "doc.pdf"},
        )
        parsed = _parse(result)
        assert parsed["status"] == "downloaded"
        assert parsed["size"] == len(file_content)
        assert (tmp_path / "doc.pdf").read_bytes() == file_content

    async def test_read_only_blocked(self, readonly_client):
        client, router = readonly_client
        result = await client.call_tool(
            "jira_download_attachment",
            {
                "content_url": f"{TEST_JIRA_URL}/secure/attachment/10000/doc.pdf",
                "save_path": "doc.pdf",
            },
        )
        parsed = _parse(result)
        assert "error" in parsed


class TestDeleteAttachment:
    async def test_happy_path(self, tool_client):
        client, router = tool_client
        router.delete("/rest/api/2/attachment/123").mock(return_value=Response(204))
        result = await client.call_tool("jira_delete_attachment", {"attachment_id": "123"})
        parsed = _parse(result)
        assert parsed["status"] == "deleted"
        assert parsed["attachment_id"] == "123"

    async def test_read_only_blocked(self, readonly_client):
        client, router = readonly_client
        result = await client.call_tool("jira_delete_attachment", {"attachment_id": "123"})
        parsed = _parse(result)
        assert "error" in parsed


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
        assert parsed["issues"][0]["key"] == "PROJ-10"


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
# Read-Only Guards (remaining write tools)
# ═══════════════════════════════════════════════════════


class TestReadOnlyGuards:
    async def test_update_issue_blocked(self, readonly_client):
        client, router = readonly_client
        result = await client.call_tool(
            "jira_update_issue",
            {"issue_key": "PROJ-123", "fields": {"summary": "Nope"}},
        )
        parsed = _parse(result)
        assert "error" in parsed
        assert "hint" in parsed
        assert "read-only" in parsed["hint"].lower()

    async def test_create_link_blocked(self, readonly_client):
        client, router = readonly_client
        result = await client.call_tool(
            "jira_create_link",
            {
                "link_type": "Relates",
                "inward_issue": "PROJ-1",
                "outward_issue": "PROJ-2",
            },
        )
        parsed = _parse(result)
        assert "error" in parsed

    async def test_create_epic_blocked(self, readonly_client):
        client, router = readonly_client
        result = await client.call_tool(
            "jira_create_epic",
            {"project_key": "PROJ", "epic_name": "Blocked Epic"},
        )
        parsed = _parse(result)
        assert "error" in parsed


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
    async def test_happy_path(self, confluence_client):
        client, router = confluence_client
        router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
            return_value=Response(200, json=_SAMPLE_CALENDARS)
        )
        result = await client.call_tool("confluence_list_calendars", {})
        parsed = _parse(result)
        assert parsed["count"] == 2
        assert parsed["items"][0]["name"] == "Team Leaves"
        assert parsed["items"][0]["child_count"] == 1

    async def test_filter_type(self, confluence_client):
        client, router = confluence_client
        router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
            return_value=Response(200, json=_SAMPLE_CALENDARS)
        )
        result = await client.call_tool("confluence_list_calendars", {"filter_type": "leaves"})
        parsed = _parse(result)
        assert parsed["count"] == 1
        assert parsed["items"][0]["name"] == "Team Leaves"


class TestConfluenceSearchCalendars:
    async def test_happy_path(self, confluence_client):
        client, router = confluence_client
        router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
            return_value=Response(200, json=_SAMPLE_CALENDARS)
        )
        result = await client.call_tool("confluence_search_calendars", {"query": "release"})
        parsed = _parse(result)
        assert parsed["count"] == 1
        assert parsed["items"][0]["name"] == "Release Calendar"

    async def test_search_by_space(self, confluence_client):
        client, router = confluence_client
        router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
            return_value=Response(200, json=_SAMPLE_CALENDARS)
        )
        result = await client.call_tool("confluence_search_calendars", {"query": "ENG"})
        parsed = _parse(result)
        assert parsed["count"] == 1
        assert parsed["items"][0]["space_key"] == "ENG"


class TestConfluenceGetTimeOff:
    async def test_happy_path(self, confluence_client):
        client, router = confluence_client
        _mock_confluence_calendars_and_events(router)
        result = await client.call_tool(
            "confluence_get_time_off",
            {"start_date": "2024-03-01", "end_date": "2024-03-10"},
        )
        parsed = _parse(result)
        assert parsed["start"] == "2024-03-01"
        assert parsed["end"] == "2024-03-10"
        assert len(parsed["events"]) == 2

    async def test_group_by_person(self, confluence_client):
        client, router = confluence_client
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


class TestConfluenceWhoIsOut:
    async def test_happy_path(self, confluence_client):
        client, router = confluence_client
        _mock_confluence_calendars_and_events(router)
        result = await client.call_tool("confluence_who_is_out", {"date": "2024-03-03"})
        parsed = _parse(result)
        assert parsed["date"] == "2024-03-03"
        assert parsed["count"] == 2
        assert "Alice Smith" in parsed["people_out"]
        assert "Bob Jones" in parsed["people_out"]


class TestConfluenceGetPersonTimeOff:
    async def test_happy_path(self, confluence_client):
        client, router = confluence_client
        _mock_confluence_calendars_and_events(router)
        result = await client.call_tool(
            "confluence_get_person_time_off",
            {
                "person": "Alice",
                "calendar_name": "Leaves",
                "start_date": "2024-03-01",
                "end_date": "2024-03-10",
            },
        )
        parsed = _parse(result)
        assert parsed["person"] == "Alice"
        assert len(parsed["events"]) == 1
        assert parsed["events"][0]["person_name"] == "Alice Smith"

    async def test_no_match(self, confluence_client):
        client, router = confluence_client
        _mock_confluence_calendars_and_events(router)
        result = await client.call_tool(
            "confluence_get_person_time_off",
            {
                "person": "Charlie",
                "calendar_name": "Leaves",
                "start_date": "2024-03-01",
                "end_date": "2024-03-10",
            },
        )
        parsed = _parse(result)
        assert parsed["events"] == []


class TestConfluenceSprintCapacity:
    async def test_happy_path(self, confluence_client):
        client, router = confluence_client
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
        assert parsed["team"]["members"] == 3
        assert parsed["sprint"]["working_days"] > 0
        assert parsed["team"]["max_capacity_days"] > 0
        assert parsed["team"]["capacity_percentage"] <= 100
        assert len(parsed["member_breakdown"]) == 3
        # Alice has time off in this range, so days_off > 0
        alice = next(m for m in parsed["member_breakdown"] if m["member"] == "Alice Smith")
        assert alice["days_off"] >= 1

    async def test_no_time_off(self, confluence_client):
        client, router = confluence_client
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
