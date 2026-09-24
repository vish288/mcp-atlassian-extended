"""Boot the real server: real ``lifespan``, live tool/resource/prompt inventory."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from fastmcp import Client

from mcp_atlassian_extended.servers import mcp

_SERVERS_DIR = Path(__file__).resolve().parents[2] / "src" / "mcp_atlassian_extended" / "servers"
_TOOL_DECORATOR = re.compile(r"^@mcp\.tool\b", re.MULTILINE)


def _decorated_tool_count() -> int:
    return sum(len(_TOOL_DECORATOR.findall(p.read_text())) for p in _SERVERS_DIR.glob("*.py"))


@pytest.fixture
def _configured(monkeypatch):
    for key, value in {
        "JIRA_URL": "https://jira.example.com",
        "JIRA_PAT": "t",
        "CONFLUENCE_URL": "https://confluence.example.com",
        "CONFLUENCE_PAT": "t",
    }.items():
        monkeypatch.setenv(key, value)
    monkeypatch.delenv("ATLASSIAN_READ_ONLY", raising=False)


@pytest.fixture
def _unconfigured(monkeypatch):
    monkeypatch.setenv("JIRA_URL", "")
    monkeypatch.setenv("CONFLUENCE_URL", "")


@pytest.mark.usefixtures("_configured")
async def test_real_lifespan_registers_everything():
    expected = _decorated_tool_count()
    assert expected > 0
    async with Client(mcp) as client:
        assert len(await client.list_tools()) == expected
        resources = await client.list_resources()
        assert resources
        for resource in resources:
            content = await client.read_resource(resource.uri)
            assert content[0].text.lstrip().startswith("#"), resource.uri
        assert await client.list_prompts()


@pytest.mark.usefixtures("_unconfigured")
async def test_boots_with_nothing_configured_and_tools_say_so():
    async with Client(mcp) as client:
        result = await client.call_tool("jira_list_projects", {})
        parsed = json.loads(result.content[0].text)
        assert "not configured" in parsed["error"]
        assert "JIRA_URL" in parsed["hint"]
