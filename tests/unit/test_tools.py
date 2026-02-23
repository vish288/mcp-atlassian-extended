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
        assert len(parsed) == 1
        assert parsed[0]["filename"] == "doc.pdf"

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
        assert len(parsed) == 2
        assert parsed[0]["displayName"] == "Alice"


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
        assert len(parsed) == 2
        assert parsed[0]["key"] == "PROJ"


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
