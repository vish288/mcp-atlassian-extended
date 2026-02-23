"""Jira Agile tools — boards, sprints."""

from __future__ import annotations

from typing import Annotated

from fastmcp import Context
from pydantic import Field

from . import mcp
from ._helpers import _check_write, _err, _get_jira, _ok


@mcp.tool(
    tags={"jira", "agile", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
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


@mcp.tool(
    tags={"jira", "agile", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
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


@mcp.tool(
    tags={"jira", "agile", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
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


@mcp.tool(tags={"jira", "agile", "write"}, annotations={"readOnlyHint": False})
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
