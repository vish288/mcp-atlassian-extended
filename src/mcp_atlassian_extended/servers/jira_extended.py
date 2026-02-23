"""Jira Extended tools — attachments, users, metadata, backlog."""

from __future__ import annotations

from typing import Annotated

from fastmcp import Context
from pydantic import Field

from . import mcp
from ._helpers import _check_write, _err, _get_jira, _ok

# ── Attachments ───────────────────────────────────────────────────


@mcp.tool(
    tags={"jira", "attachments", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def jira_get_attachments(
    ctx: Context,
    issue_key: Annotated[str, Field(description="Jira issue key (e.g. PROJ-123)")],
) -> str:
    """List attachments on a Jira issue."""
    try:
        data = await _get_jira(ctx).get_attachments(issue_key)
        return _ok(data)
    except Exception as e:
        return _err(e)


@mcp.tool(tags={"jira", "attachments", "write"}, annotations={"readOnlyHint": False})
async def jira_upload_attachment(
    ctx: Context,
    issue_key: Annotated[str, Field(description="Jira issue key")],
    file_path: Annotated[str, Field(description="Local file path to upload")],
    filename: Annotated[str | None, Field(description="Override filename")] = None,
) -> str:
    """Upload a file as an attachment to a Jira issue."""
    try:
        _check_write(ctx)
        data = await _get_jira(ctx).upload_attachment(issue_key, file_path, filename)
        return _ok(data)
    except Exception as e:
        return _err(e)


@mcp.tool(tags={"jira", "attachments", "write"}, annotations={"readOnlyHint": False})
async def jira_download_attachment(
    ctx: Context,
    content_url: Annotated[str, Field(description="Attachment content URL")],
    save_path: Annotated[str, Field(description="Local path to save the file")],
) -> str:
    """Download a Jira attachment to a local file. Writes to local disk."""
    try:
        _check_write(ctx)
        from pathlib import Path

        content = await _get_jira(ctx).download_attachment(content_url)
        Path(save_path).write_bytes(content)
        return _ok({"status": "downloaded", "path": save_path, "size": len(content)})
    except Exception as e:
        return _err(e)


@mcp.tool(
    tags={"jira", "attachments", "write"},
    annotations={"destructiveHint": True, "readOnlyHint": False},
)
async def jira_delete_attachment(
    ctx: Context,
    attachment_id: Annotated[str, Field(description="Attachment ID to delete")],
) -> str:
    """Delete a Jira attachment."""
    try:
        _check_write(ctx)
        await _get_jira(ctx).delete_attachment(attachment_id)
        return _ok({"status": "deleted", "attachment_id": attachment_id})
    except Exception as e:
        return _err(e)


# ── Users ─────────────────────────────────────────────────────────


@mcp.tool(
    tags={"jira", "users", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def jira_search_users(
    ctx: Context,
    query: Annotated[str, Field(description="Search by name, email, or username")],
    max_results: Annotated[int, Field(description="Maximum results")] = 10,
) -> str:
    """Search for Jira users."""
    try:
        data = await _get_jira(ctx).search_users(query, max_results)
        return _ok(data)
    except Exception as e:
        return _err(e)


# ── Metadata ──────────────────────────────────────────────────────


@mcp.tool(
    tags={"jira", "metadata", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def jira_list_projects(ctx: Context) -> str:
    """List all accessible Jira projects."""
    try:
        data = await _get_jira(ctx).list_projects()
        return _ok(data)
    except Exception as e:
        return _err(e)


@mcp.tool(
    tags={"jira", "metadata", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def jira_list_fields(
    ctx: Context,
    search: Annotated[str | None, Field(description="Filter fields by name")] = None,
    custom_only: Annotated[bool, Field(description="Only return custom fields")] = False,
) -> str:
    """List Jira fields, optionally filtered."""
    try:
        data = await _get_jira(ctx).list_fields()
        if custom_only:
            data = [f for f in data if f.get("custom", False)]
        if search:
            search_lower = search.lower()
            data = [f for f in data if search_lower in f.get("name", "").lower()]
        return _ok(data)
    except Exception as e:
        return _err(e)


@mcp.tool(
    tags={"jira", "metadata", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def jira_backlog(
    ctx: Context,
    board_id: Annotated[int, Field(description="Board ID")],
    max_results: Annotated[int, Field(description="Maximum results")] = 50,
) -> str:
    """Get backlog issues for a board."""
    try:
        data = await _get_jira(ctx).get_backlog(board_id, max_results)
        return _ok(data)
    except Exception as e:
        return _err(e)
