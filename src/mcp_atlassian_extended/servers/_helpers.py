"""Shared helpers for all server modules."""

from __future__ import annotations

import functools
import json
import re
from pathlib import Path
from typing import Any, Literal

from fastmcp import Context

from ..clients.confluence import ConfluenceExtendedClient
from ..clients.jira import JiraExtendedClient
from ..exceptions import WriteDisabledError


@functools.cache
def _load_file(base_dir: str, filename: str) -> str:
    """Load a file from the given directory with path traversal protection.

    Results are cached — static files do not change at runtime.
    """
    if "/" in filename or "\\" in filename or ".." in filename:
        msg = f"Invalid filename: {filename}"
        raise ValueError(msg)
    base = Path(base_dir)
    path = base / filename
    if not path.resolve().is_relative_to(base.resolve()):
        msg = f"Invalid filename: {filename}"
        raise ValueError(msg)
    return path.read_text(encoding="utf-8")


def _get_jira(ctx: Context) -> JiraExtendedClient:
    client = ctx.request_context.lifespan_context["jira_client"]
    if client is None:
        msg = (
            "Jira is not configured. Set JIRA_URL plus either "
            "JIRA_USERNAME + JIRA_API_TOKEN (Cloud) or JIRA_PAT (Data Center)."
        )
        raise ValueError(msg)
    return client


def _get_confluence(ctx: Context) -> ConfluenceExtendedClient:
    client = ctx.request_context.lifespan_context["confluence_client"]
    if client is None:
        msg = (
            "Confluence is not configured. Set CONFLUENCE_URL plus either "
            "CONFLUENCE_USERNAME + CONFLUENCE_API_TOKEN (Cloud) or "
            "CONFLUENCE_PAT (Data Center)."
        )
        raise ValueError(msg)
    return client


def _check_write(ctx: Context, service: Literal["jira", "confluence"]) -> None:
    """Block writes when the config for *service* is read-only.

    *service* must name the product the calling tool writes to — Jira tools pass
    ``"jira"``, Confluence tools pass ``"confluence"``. The two configs are
    independent, so consulting the wrong one silently ignores the setting.
    """
    if ctx.request_context.lifespan_context[f"{service}_config"].read_only:
        raise WriteDisabledError


def _ok(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


def _paginated(
    items: list,
    *,
    start_at: int | None = None,
    total: int | None = None,
    max_results: int | None = None,
) -> str:
    """Wrap a list response, reporting real paging state when the API has one.

    ``count`` is the size of *this* page, never a grand total. Callers hitting a
    genuinely paged endpoint pass ``start_at`` (and ``total``/``max_results``
    when the API returns them), which adds ``has_more`` and ``next_start_at`` so
    a truncated result can actually be continued. Endpoints that return their
    full collection in one response (``/rest/api/2/field``,
    ``/rest/api/2/project``) pass nothing and get a bare count -- which is the
    honest answer for them.
    """
    payload: dict[str, Any] = {"items": items, "count": len(items)}

    if start_at is not None:
        next_start_at = start_at + len(items)
        if total is not None:
            has_more = next_start_at < total
        elif max_results is not None:
            # No total from the API: a full page implies there may be more.
            has_more = len(items) == max_results
        else:
            has_more = False
        payload["start_at"] = start_at
        if total is not None:
            payload["total"] = total
        payload["has_more"] = has_more
        payload["next_start_at"] = next_start_at if has_more else None

    return json.dumps(payload, indent=2, ensure_ascii=False)


def _err(error: Exception) -> str:
    """Format error as JSON with actionable hints."""
    from ..exceptions import (
        AtlassianApiError,
        AtlassianAuthError,
        TeamCalendarsUnavailableError,
        WriteDisabledError,
    )

    detail: dict[str, Any] = {"error": str(error)}

    if isinstance(error, AtlassianAuthError):
        detail["status_code"] = error.status_code
        detail["body"] = error.body
        detail["hint"] = (
            "Check the credentials for the product this tool targets. "
            "Cloud: JIRA_USERNAME + JIRA_API_TOKEN, or CONFLUENCE_USERNAME + "
            "CONFLUENCE_API_TOKEN — a complete Cloud pair takes precedence over a PAT. "
            "Data Center: JIRA_PAT or CONFLUENCE_PAT."
        )
    elif isinstance(error, TeamCalendarsUnavailableError):
        detail["status_code"] = error.status_code
        detail["body"] = error.body
        detail["hint"] = (
            "Every Confluence calendar tool requires the Team Calendars add-on, "
            "which serves /rest/calendar-services/1.0/. Install or enable it on the "
            "Confluence instance, and check CONFLUENCE_URL — Cloud URLs usually need "
            "the /wiki suffix."
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
                "Client not configured. Set the URL and credentials for that product "
                "(JIRA_URL / CONFLUENCE_URL plus a Cloud username + API token, or a PAT)."
            )
        elif "traversal" in msg:
            detail["hint"] = "Path traversal is not allowed for security reasons."
        elif "too large" in msg:
            detail["hint"] = "File exceeds the 100MB size limit."
    elif isinstance(error, FileNotFoundError):
        detail["hint"] = "File not found. Check the file path exists and is accessible."

    return json.dumps(detail, indent=2, ensure_ascii=False)


# ════════════════════════════════════════════════════════════════════
# Jira URL parsing
# ════════════════════════════════════════════════════════════════════

# Matches: https://<host>/browse/PROJ-123  (Data Center & Cloud)
_ISSUE_URL_RE = re.compile(r"https?://[^/]+/browse/([A-Z][A-Z0-9_]+-\d+)")
# Matches: https://<host>/jira/software/projects/PROJ/...
_PROJECT_URL_RE = re.compile(r"https?://[^/]+/(?:jira/software/)?projects/([A-Z][A-Z0-9_]+)")
# Matches: .../boards/<board_id>
_BOARD_URL_RE = re.compile(r"/boards/(\d+)")


def _parse_jira_issue_url(value: str) -> str:
    """Extract issue key from a Jira browse URL.

    If *value* is not a URL, returns it unchanged (assumes it's already a key).
    """
    if not value.startswith(("http://", "https://")):
        return value
    m = _ISSUE_URL_RE.match(value)
    if m:
        return m.group(1)
    return value


def _parse_jira_project_url(value: str) -> str:
    """Extract project key from a Jira project URL.

    If *value* is not a URL, returns it unchanged.
    """
    if not value.startswith(("http://", "https://")):
        return value
    m = _PROJECT_URL_RE.match(value)
    if m:
        return m.group(1)
    return value


def _parse_jira_board_url(value: str) -> str:
    """Extract board ID from a Jira board URL.

    If *value* is not a URL, returns it unchanged.
    """
    if not value.startswith(("http://", "https://")):
        return value
    m = _BOARD_URL_RE.search(value)
    if m:
        return m.group(1)
    return value
