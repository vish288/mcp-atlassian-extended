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
    """Format error as JSON with actionable hints."""
    from ..exceptions import AtlassianApiError, AtlassianAuthError, WriteDisabledError

    detail: dict[str, Any] = {"error": str(error)}

    if isinstance(error, AtlassianAuthError):
        detail["status_code"] = error.status_code
        detail["body"] = error.body
        detail["hint"] = (
            "Check authentication. For Jira Data Center use JIRA_PAT; "
            "for Jira Cloud use JIRA_USERNAME + JIRA_API_TOKEN."
        )
    elif isinstance(error, WriteDisabledError):
        detail["hint"] = (
            "Server is in read-only mode. Set ATLASSIAN_READ_ONLY=false to enable writes."
        )
    elif isinstance(error, AtlassianApiError):
        detail["status_code"] = error.status_code
        detail["body"] = error.body
        if error.status_code == 404:
            detail["hint"] = (
                "Resource not found. Verify the issue key format (PROJ-123) "
                "or resource ID. Use jira_list_projects to check accessible projects."
            )
        elif error.status_code == 400:
            detail["hint"] = "Bad request — check required fields and value formats."
        elif error.status_code == 409:
            detail["hint"] = "Conflict — resource may already exist or be locked."
        elif error.status_code == 422:
            detail["hint"] = "Validation failed — check required fields and formats."
        elif error.status_code == 429:
            detail["hint"] = "Rate limited. Wait before retrying."
    elif isinstance(error, ValueError):
        msg = str(error).lower()
        if "not configured" in msg:
            detail["hint"] = (
                "Client not configured. Set required environment variables "
                "(JIRA_URL, JIRA_PAT, etc.)."
            )
        elif "traversal" in msg:
            detail["hint"] = "Path traversal is not allowed for security reasons."
        elif "too large" in msg:
            detail["hint"] = "File exceeds the 100MB size limit."
    elif isinstance(error, FileNotFoundError):
        detail["hint"] = "File not found. Check the file path exists and is accessible."

    return json.dumps(detail, indent=2, ensure_ascii=False)
