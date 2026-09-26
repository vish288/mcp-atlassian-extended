"""The error contract: expected failures are JSON, bugs are MCP tool errors."""

from __future__ import annotations

import json

import pytest
from fastmcp.exceptions import ToolError
from httpx import Response

from mcp_atlassian_extended.clients.jira import JiraExtendedClient


async def _boom(self):
    msg = "lifespan dict lost a key"
    raise RuntimeError(msg)


async def test_bug_is_a_tool_error_not_a_result(tool_client, monkeypatch, caplog):
    client, _ = tool_client
    monkeypatch.setattr(JiraExtendedClient, "list_projects", _boom)

    result = await client.call_tool("jira_list_projects", {}, raise_on_error=False)

    assert result.is_error is True
    assert "RuntimeError: lifespan dict lost a key" in result.content[0].text
    assert "jira_list_projects failed" in caplog.text
    assert "Traceback" in caplog.text


async def test_bug_raises_by_default(tool_client, monkeypatch):
    client, _ = tool_client
    monkeypatch.setattr(JiraExtendedClient, "list_projects", _boom)
    with pytest.raises(ToolError, match="RuntimeError"):
        await client.call_tool("jira_list_projects", {})


async def test_api_error_is_still_structured_json(tool_client):
    client, router = tool_client
    router.get("/rest/api/2/project").mock(return_value=Response(404, text="gone"))

    result = await client.call_tool("jira_list_projects", {})

    assert result.is_error is False
    parsed = json.loads(result.content[0].text)
    assert parsed["status_code"] == 404
    assert "hint" in parsed


async def test_local_validation_is_still_structured_json(tool_client, tmp_path, monkeypatch):
    """ValueError / FileNotFoundError are expected — they must not become ToolErrors."""
    client, _ = tool_client
    monkeypatch.chdir(tmp_path)

    result = await client.call_tool(
        "jira_download_attachment",
        {"content_url": "https://jira.example.com/x", "save_path": "../escape"},
    )

    assert result.is_error is False
    assert "traversal" in json.loads(result.content[0].text)["hint"]
