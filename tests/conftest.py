"""Shared test fixtures for mcp-atlassian-extended.

Tool tests go through the real FastMCP server: ``mcp._lifespan`` is swapped for
one that yields real Jira/Confluence clients pointed at fake hosts, HTTP is
mocked with respx, and calls go through ``fastmcp.Client``. One respx router
serves both hosts — a path-only pattern matches on any host, so tests register
``router.get("/rest/api/2/...")`` and ``router.get("/rest/calendar-services/...")``
on the same router.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import pytest
import respx
from fastmcp import Client, FastMCP

from mcp_atlassian_extended.clients.confluence import ConfluenceExtendedClient
from mcp_atlassian_extended.clients.jira import JiraExtendedClient
from mcp_atlassian_extended.config import ConfluenceConfig, JiraConfig

TEST_JIRA_URL = "https://jira.example.com"
TEST_CONFLUENCE_URL = "https://confluence.example.com"
TEST_TOKEN = "test-token"


def _make_mcp(*, read_only: bool = False) -> tuple[FastMCP, Any]:
    """Return the server with its lifespan swapped for one yielding test clients."""
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


async def _client(*, read_only: bool):
    mcp, original_lifespan = _make_mcp(read_only=read_only)
    try:
        with respx.mock() as router:
            async with Client(mcp) as client:
                yield client, router
    finally:
        mcp._lifespan = original_lifespan


@pytest.fixture
async def tool_client():
    """(Client, respx router) against a writable server."""
    async for pair in _client(read_only=False):
        yield pair


@pytest.fixture
async def readonly_client():
    """(Client, respx router) against a server with ATLASSIAN_READ_ONLY=true."""
    async for pair in _client(read_only=True):
        yield pair
