"""Shared helpers for all server modules."""

from __future__ import annotations

import json
from typing import Any

from fastmcp import Context

from ..clients.confluence import ConfluenceExtendedClient
from ..clients.jira import JiraExtendedClient
from ..exceptions import WriteDisabledError


def _get_jira(ctx: Context) -> JiraExtendedClient:
    client = ctx.request_context.lifespan_context["jira_client"]
    if client is None:
        msg = "Jira is not configured. Set JIRA_URL and JIRA_PAT environment variables."
        raise ValueError(msg)
    return client


def _get_confluence(ctx: Context) -> ConfluenceExtendedClient:
    client = ctx.request_context.lifespan_context["confluence_client"]
    if client is None:
        msg = (
            "Confluence is not configured."
            " Set CONFLUENCE_URL and CONFLUENCE_PAT environment variables."
        )
        raise ValueError(msg)
    return client


def _check_write(ctx: Context) -> None:
    if ctx.request_context.lifespan_context["jira_config"].read_only:
        raise WriteDisabledError


def _ok(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def _err(error: Exception) -> str:
    return json.dumps({"error": str(error)}, indent=2, ensure_ascii=False)
