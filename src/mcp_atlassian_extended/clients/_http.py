"""Response handling shared by the Jira and Confluence clients."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

import httpx

from ..exceptions import AtlassianApiError, AtlassianAuthError


def _raise_for_atlassian(
    resp: httpx.Response, *, not_found: Callable[[str], Exception] | None = None
) -> None:
    """Map an Atlassian error response to the matching exception.

    *not_found* gives a 404 a more specific meaning for one namespace (Confluence's
    Team Calendars add-on); it is called with the response body.
    """
    if resp.status_code in (401, 403):
        raise AtlassianAuthError(resp.status_code, resp.text)
    if resp.status_code == 404 and not_found is not None:
        raise not_found(resp.text[:500])
    if not resp.is_success:
        raise AtlassianApiError(resp.status_code, resp.reason_phrase or "", resp.text)


def _parse_json(resp: httpx.Response) -> Any:
    """Decode a successful response body; ``None`` when it is empty."""
    if not resp.content:
        return None
    if "text/html" in resp.headers.get("content-type", ""):
        raise AtlassianApiError(
            resp.status_code, "Unexpected HTML response — check auth", resp.text[:500]
        )
    try:
        return resp.json()
    except json.JSONDecodeError as e:
        raise AtlassianApiError(resp.status_code, f"JSON parse error: {e}", resp.text[:500]) from e
