"""Atlassian Extended MCP server — combines Jira and Confluence tools."""

from __future__ import annotations

import importlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import version
from typing import Any

from fastmcp import FastMCP

from ..clients.confluence import ConfluenceExtendedClient
from ..clients.jira import JiraExtendedClient
from ..config import ConfluenceConfig, JiraConfig

_log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    jira_config = JiraConfig.from_env()
    confluence_config = ConfluenceConfig.from_env()

    pkg_version = version("mcp-atlassian-extended")
    _log.info("mcp-atlassian-extended %s starting", pkg_version)
    _log.info(
        "Jira: %s (configured: %s, read-only: %s)",
        jira_config.url or "(none)",
        jira_config.is_configured,
        jira_config.read_only,
    )
    _log.info(
        "Confluence: %s (configured: %s, read-only: %s)",
        confluence_config.url or "(none)",
        confluence_config.is_configured,
        confluence_config.read_only,
    )

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
        "Provides issue creation/update with custom fields, issue links, "
        "attachments, agile boards/sprints, users, metadata, and calendar tools."
    ),
    lifespan=lifespan,
)


def _register_tools() -> None:
    """Import tool modules so their @mcp.tool decorators execute."""
    importlib.import_module(".jira_extended", __package__)
    importlib.import_module(".jira_agile", __package__)
    importlib.import_module(".jira_issues", __package__)
    importlib.import_module(".confluence_extended", __package__)
    importlib.import_module(".resources", __package__)
    importlib.import_module(".prompts", __package__)


_register_tools()
