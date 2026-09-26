"""Jira Extended tools — attachments, users, metadata, backlog."""

from __future__ import annotations

from typing import Annotated

from fastmcp import Context
from pydantic import Field

from . import mcp
from ._helpers import _get_jira, _ok, _paginated, tool_result

# ── Attachments ───────────────────────────────────────────────────


@mcp.tool(
    tags={"jira", "attachments", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": True},
)
@tool_result
async def jira_get_attachments(
    ctx: Context,
    issue_key: Annotated[str, Field(description="Jira issue key (e.g. PROJ-123)", min_length=1)],
) -> str:
    """List attachments on a Jira issue."""
    data = await _get_jira(ctx).get_attachments(issue_key)
    return _paginated(data)


@mcp.tool(
    tags={"jira", "attachments", "write"},
    annotations={"readOnlyHint": False, "openWorldHint": True},
)
@tool_result(write="jira")
async def jira_upload_attachment(
    ctx: Context,
    issue_key: Annotated[str, Field(description="Jira issue key", min_length=1)],
    file_path: Annotated[str, Field(description="Local file path to upload", min_length=1)],
    filename: Annotated[str | None, Field(description="Override filename")] = None,
) -> str:
    """Upload a file as an attachment to a Jira issue."""
    data = await _get_jira(ctx).upload_attachment(issue_key, file_path, filename)
    return _ok(data)


@mcp.tool(
    tags={"jira", "attachments", "write"},
    annotations={"readOnlyHint": False, "openWorldHint": True},
)
@tool_result(write="jira")
async def jira_download_attachment(
    ctx: Context,
    content_url: Annotated[str, Field(description="Attachment content URL", min_length=1)],
    save_path: Annotated[str, Field(description="Local path to save the file", min_length=1)],
) -> str:
    """Download a Jira attachment to a local file. Writes to current working directory only."""
    from pathlib import Path

    save = Path(save_path)
    if save.is_absolute():
        msg = "Absolute paths are not allowed. Use a relative path from the working directory."
        raise ValueError(msg)
    if ".." in save.parts:
        msg = f"Path traversal detected in save_path: {save_path}"
        raise ValueError(msg)
    resolved = (Path.cwd() / save).resolve()
    if not resolved.is_relative_to(Path.cwd().resolve()):
        msg = f"Path traversal detected in save_path: {save_path}"
        raise ValueError(msg)

    content = await _get_jira(ctx).download_attachment(content_url)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_bytes(content)
    return _ok({"status": "downloaded", "path": str(resolved), "size": len(content)})


@mcp.tool(
    tags={"jira", "attachments", "write"},
    annotations={"destructiveHint": True, "readOnlyHint": False, "openWorldHint": True},
)
@tool_result(write="jira")
async def jira_delete_attachment(
    ctx: Context,
    attachment_id: Annotated[str, Field(description="Attachment ID to delete", min_length=1)],
) -> str:
    """Delete a Jira attachment."""
    await _get_jira(ctx).delete_attachment(attachment_id)
    return _ok({"status": "deleted", "attachment_id": attachment_id})


# ── Users ─────────────────────────────────────────────────────────


@mcp.tool(
    tags={"jira", "users", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": True},
)
@tool_result
async def jira_search_users(
    ctx: Context,
    query: Annotated[str, Field(description="Search by name, email, or username", min_length=1)],
    max_results: Annotated[int, Field(description="Maximum results", ge=1, le=100)] = 10,
    start_at: Annotated[
        int, Field(description="Index of the first result (use next_start_at to page)", ge=0)
    ] = 0,
) -> str:
    """Search for Jira users."""
    data = await _get_jira(ctx).search_users(query, max_results, start_at)
    return _paginated(data, start_at=start_at, max_results=max_results)


# ── Metadata ──────────────────────────────────────────────────────


@mcp.tool(
    tags={"jira", "metadata", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": True},
)
@tool_result
async def jira_list_projects(ctx: Context) -> str:
    """List all accessible Jira projects."""
    data = await _get_jira(ctx).list_projects()
    return _paginated(data)


@mcp.tool(
    tags={"jira", "metadata", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": True},
)
@tool_result
async def jira_list_fields(
    ctx: Context,
    search: Annotated[str | None, Field(description="Filter fields by name")] = None,
    custom_only: Annotated[bool, Field(description="Only return custom fields")] = False,
) -> str:
    """List Jira fields, optionally filtered."""
    data = await _get_jira(ctx).list_fields()
    if custom_only:
        data = [f for f in data if f.get("custom", False)]
    if search:
        search_lower = search.lower()
        data = [f for f in data if search_lower in f.get("name", "").lower()]
    return _paginated(data)


@mcp.tool(
    tags={"jira", "metadata", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": True},
)
@tool_result
async def jira_backlog(
    ctx: Context,
    board_id: Annotated[int, Field(description="Board ID", ge=1)],
    max_results: Annotated[int, Field(description="Maximum results", ge=1, le=100)] = 50,
    start_at: Annotated[
        int, Field(description="Index of the first result (use next_start_at to page)", ge=0)
    ] = 0,
) -> str:
    """Get backlog issues for a board."""
    data = await _get_jira(ctx).get_backlog(board_id, max_results, start_at)
    return _paginated(
        data.get("issues", []),
        start_at=data.get("startAt", start_at),
        total=data.get("total"),
        max_results=max_results,
    )


# ── Versions ─────────────────────────────────────────────────────


@mcp.tool(
    tags={"jira", "versions", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": True},
)
@tool_result
async def jira_get_project_versions(
    ctx: Context,
    project_key: Annotated[str, Field(description="Project key (e.g. PROJ)", min_length=1)],
) -> str:
    """List all versions for a Jira project (REST API v2, supports Server/DC and Cloud)."""
    data = await _get_jira(ctx).get_project_versions(project_key)
    return _paginated(data)


@mcp.tool(
    tags={"jira", "versions", "write"},
    annotations={"readOnlyHint": False, "openWorldHint": True},
)
@tool_result(write="jira")
async def jira_create_version(
    ctx: Context,
    project_key: Annotated[str, Field(description="Project key (e.g. PROJ)", min_length=1)],
    name: Annotated[str, Field(description="Version name", min_length=1)],
    description: Annotated[str | None, Field(description="Version description")] = None,
    release_date: Annotated[str | None, Field(description="Release date (YYYY-MM-DD)")] = None,
    start_date: Annotated[str | None, Field(description="Start date (YYYY-MM-DD)")] = None,
    released: Annotated[bool, Field(description="Mark as released")] = False,
    archived: Annotated[bool, Field(description="Mark as archived")] = False,
) -> str:
    """Create a new version in a Jira project (REST API v2, supports Server/DC and Cloud)."""
    data = await _get_jira(ctx).create_version(
        project_key,
        name,
        description=description,
        release_date=release_date,
        start_date=start_date,
        released=released,
        archived=archived,
    )
    return _ok(data)


@mcp.tool(
    tags={"jira", "versions", "write"},
    annotations={"readOnlyHint": False, "idempotentHint": True, "openWorldHint": True},
)
@tool_result(write="jira")
async def jira_update_version(
    ctx: Context,
    version_id: Annotated[str, Field(description="Version ID", min_length=1)],
    name: Annotated[str | None, Field(description="New version name")] = None,
    description: Annotated[str | None, Field(description="New description")] = None,
    release_date: Annotated[str | None, Field(description="Release date (YYYY-MM-DD)")] = None,
    start_date: Annotated[str | None, Field(description="Start date (YYYY-MM-DD)")] = None,
    released: Annotated[bool | None, Field(description="Mark as released")] = None,
    archived: Annotated[bool | None, Field(description="Mark as archived")] = None,
) -> str:
    """Update an existing Jira version (REST API v2, supports Server/DC and Cloud)."""
    data = await _get_jira(ctx).update_version(
        version_id,
        name=name,
        description=description,
        release_date=release_date,
        start_date=start_date,
        released=released,
        archived=archived,
    )
    return _ok(data)
