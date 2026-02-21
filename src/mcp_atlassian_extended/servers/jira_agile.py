"""Jira Agile tools — boards, sprints."""

from __future__ import annotations

import json
from typing import Annotated, Any

from fastmcp import Context
from pydantic import Field

from ..clients.jira import JiraExtendedClient
from ..exceptions import WriteDisabledError
from . import mcp


def _get_jira(ctx: Context) -> JiraExtendedClient:
    client = ctx.request_context.lifespan_context["jira_client"]
    if client is None:
        msg = "Jira is not configured. Set JIRA_URL and JIRA_PAT environment variables."
        raise ValueError(msg)
    return client


def _check_write(ctx: Context) -> None:
    if ctx.request_context.lifespan_context["jira_config"].read_only:
        raise WriteDisabledError


def _ok(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def _err(error: Exception) -> str:
    return json.dumps({"error": str(error)}, indent=2, ensure_ascii=False)


@mcp.tool(tags={"jira", "agile", "read"})
async def jira_get_board(
    ctx: Context,
    board_id: Annotated[int, Field(description="Board ID")],
) -> str:
    """Get details of a Jira agile board."""
    try:
        data = await _get_jira(ctx).get_board(board_id)
        return _ok(data)
    except Exception as e:
        return _err(e)


@mcp.tool(tags={"jira", "agile", "read"})
async def jira_board_config(
    ctx: Context,
    board_id: Annotated[int, Field(description="Board ID")],
) -> str:
    """Get board column/status configuration."""
    try:
        data = await _get_jira(ctx).get_board_config(board_id)
        return _ok(data)
    except Exception as e:
        return _err(e)


@mcp.tool(tags={"jira", "agile", "read"})
async def jira_get_sprint(
    ctx: Context,
    sprint_id: Annotated[int, Field(description="Sprint ID")],
) -> str:
    """Get details of a specific sprint."""
    try:
        data = await _get_jira(ctx).get_sprint(sprint_id)
        return _ok(data)
    except Exception as e:
        return _err(e)


@mcp.tool(tags={"jira", "agile", "write"})
async def jira_move_to_sprint(
    ctx: Context,
    sprint_id: Annotated[int, Field(description="Target sprint ID")],
    issue_keys: Annotated[
        list[str], Field(description="Issue keys to move (e.g. ['PROJ-1', 'PROJ-2'])")
    ],
) -> str:
    """Move issues into a sprint."""
    try:
        _check_write(ctx)
        await _get_jira(ctx).move_to_sprint(sprint_id, issue_keys)
        return _ok({"status": "moved", "sprint_id": sprint_id, "issues": issue_keys})
    except Exception as e:
        return _err(e)
