"""Jira Issue tools — create, update, link issues with custom field support."""

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


# ── Issue CRUD ─────────────────────────────────────────────────────


@mcp.tool(tags={"jira", "issues", "write"})
async def jira_create_issue(
    ctx: Context,
    project_key: Annotated[str, Field(description="Project key (e.g. PROJ)")],
    summary: Annotated[str, Field(description="Issue title/summary")],
    issue_type: Annotated[str, Field(description="Issue type name")] = "Story",
    description: Annotated[str | None, Field(description="Issue description")] = None,
    labels: Annotated[list[str] | None, Field(description="Labels to set")] = None,
    priority: Annotated[str | None, Field(description="Priority name")] = None,
    custom_fields: Annotated[
        dict[str, Any] | None,
        Field(
            description="Custom fields dict — keys are customfield_NNNNN IDs. "
            "Use jira_list_fields to discover IDs for your instance."
        ),
    ] = None,
) -> str:
    """Create a Jira issue with standard and custom fields.

    custom_fields example: {"customfield_10004": 5, "customfield_17220": {"value": "SDM"}}
    """
    try:
        _check_write(ctx)
        data = await _get_jira(ctx).create_issue(
            project_key,
            summary,
            issue_type,
            description=description,
            labels=labels,
            priority=priority,
            custom_fields=custom_fields,
        )
        return _ok(data)
    except Exception as e:
        return _err(e)


@mcp.tool(tags={"jira", "issues", "write"})
async def jira_update_issue(
    ctx: Context,
    issue_key: Annotated[str, Field(description="Jira issue key (e.g. PROJ-123)")],
    fields: Annotated[
        dict[str, Any] | None,
        Field(description="Standard fields to update (summary, description, labels, etc.)"),
    ] = None,
    custom_fields: Annotated[
        dict[str, Any] | None,
        Field(description="Custom fields dict — keys are customfield_NNNNN IDs"),
    ] = None,
) -> str:
    """Update a Jira issue's standard and custom fields."""
    try:
        _check_write(ctx)
        await _get_jira(ctx).update_issue(issue_key, fields=fields, custom_fields=custom_fields)
        return _ok({"status": "updated", "issue_key": issue_key})
    except Exception as e:
        return _err(e)


@mcp.tool(tags={"jira", "issues", "write"})
async def jira_create_epic(
    ctx: Context,
    project_key: Annotated[str, Field(description="Project key (e.g. PROJ)")],
    epic_name: Annotated[str, Field(description="Epic name/title")],
    description: Annotated[str | None, Field(description="Epic description")] = None,
    labels: Annotated[list[str] | None, Field(description="Labels to set")] = None,
    custom_fields: Annotated[
        dict[str, Any] | None,
        Field(
            description="Additional custom fields. Pass your instance's Epic Name field "
            '(e.g. {"customfield_10009": "My Epic"}) to set it explicitly.'
        ),
    ] = None,
) -> str:
    """Create a Jira epic. Sets issue type to Epic automatically."""
    try:
        _check_write(ctx)
        data = await _get_jira(ctx).create_issue(
            project_key,
            epic_name,
            "Epic",
            description=description,
            labels=labels,
            custom_fields=custom_fields,
        )
        return _ok(data)
    except Exception as e:
        return _err(e)


# ── Issue Links ────────────────────────────────────────────────────


@mcp.tool(tags={"jira", "links", "write"})
async def jira_create_link(
    ctx: Context,
    link_type: Annotated[
        str, Field(description="Link type name (Relates, Blocks, Duplicate, etc.)")
    ],
    inward_issue: Annotated[str, Field(description="Inward issue key (receives the action)")],
    outward_issue: Annotated[str, Field(description="Outward issue key (performs the action)")],
    comment: Annotated[str | None, Field(description="Optional comment on the link")] = None,
) -> str:
    """Create a link between two Jira issues."""
    try:
        _check_write(ctx)
        await _get_jira(ctx).create_issue_link(
            link_type, inward_issue, outward_issue, comment=comment
        )
        return _ok(
            {
                "status": "linked",
                "type": link_type,
                "outward": outward_issue,
                "inward": inward_issue,
            }
        )
    except Exception as e:
        return _err(e)


@mcp.tool(tags={"jira", "links", "write"})
async def jira_delete_link(
    ctx: Context,
    link_id: Annotated[str, Field(description="Issue link ID to delete")],
) -> str:
    """Delete a Jira issue link by its ID."""
    try:
        _check_write(ctx)
        await _get_jira(ctx).delete_issue_link(link_id)
        return _ok({"status": "deleted", "link_id": link_id})
    except Exception as e:
        return _err(e)
