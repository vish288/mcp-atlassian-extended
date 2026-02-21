"""Atlassian Extended MCP server — combines Jira and Confluence tools."""

from __future__ import annotations

import importlib
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastmcp import FastMCP

from ..clients.confluence import ConfluenceExtendedClient
from ..clients.jira import JiraExtendedClient
from ..config import ConfluenceConfig, JiraConfig


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    jira_config = JiraConfig.from_env()
    confluence_config = ConfluenceConfig.from_env()

    jira_client = JiraExtendedClient(jira_config) if jira_config.is_configured else None
    confluence_client = (
        ConfluenceExtendedClient(confluence_config) if confluence_config.is_configured else None
    )

    try:
        yield {
            "jira_client": jira_client,
            "jira_config": jira_config,
            "confluence_client": confluence_client,
            "confluence_config": confluence_config,
        }
    finally:
        if jira_client:
            await jira_client.close()
        if confluence_client:
            await confluence_client.close()


mcp = FastMCP(
    name="Atlassian Extended MCP Server",
    instructions=(
        "Extended tools for Jira and Confluence that complement mcp-atlassian. "
        "Provides attachments, agile boards/sprints, users, metadata, and calendar tools."
    ),
    lifespan=lifespan,
)


def _register_tools() -> None:
    """Import tool modules so their @mcp.tool decorators execute."""
    importlib.import_module(".jira_extended", __package__)
    importlib.import_module(".jira_agile", __package__)
    importlib.import_module(".confluence_extended", __package__)


_register_tools()
