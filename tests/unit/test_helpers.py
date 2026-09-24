"""``_err`` / ``_paginated``: the exact JSON shape tools hand back."""

from __future__ import annotations

import json

import pytest

from mcp_atlassian_extended.exceptions import (
    AtlassianApiError,
    AtlassianAuthError,
    AtlassianError,
    TeamCalendarsUnavailableError,
    WriteDisabledError,
)
from mcp_atlassian_extended.servers._helpers import _err, _paginated

API = {"error", "status_code", "body", "hint"}


@pytest.mark.parametrize(
    ("exc", "keys", "hint"),
    [
        (AtlassianAuthError(401, "b"), API, "JIRA_API_TOKEN"),
        (AtlassianAuthError(403, "b"), API, "CONFLUENCE_PAT"),
        (TeamCalendarsUnavailableError("b"), API, "Team Calendars add-on"),
        (WriteDisabledError(), {"error", "hint"}, "read-only"),
        (AtlassianApiError(404, "m", "b"), API, "not found"),
        (AtlassianApiError(400, "m"), API, "Bad request"),
        (AtlassianApiError(409, "m"), API, "Conflict"),
        (AtlassianApiError(422, "m"), API, "Validation failed"),
        (AtlassianApiError(429, "m"), API, "Rate limited"),
        (AtlassianApiError(500, "m"), {"error", "status_code", "body"}, None),
        (ValueError("Jira is not configured"), {"error", "hint"}, "Client not configured"),
        (ValueError("Path traversal detected"), {"error", "hint"}, "traversal"),
        (ValueError("File too large"), {"error", "hint"}, "100MB"),
        (ValueError("anything else"), {"error"}, None),
        (FileNotFoundError("gone"), {"error", "hint"}, "File not found"),
        (AtlassianError("base"), {"error"}, None),
        (RuntimeError("bug"), {"error"}, None),
    ],
    ids=lambda v: type(v).__name__ if isinstance(v, Exception) else None,
)
def test_err_key_set(exc, keys, hint):
    parsed = json.loads(_err(exc))
    assert set(parsed) == keys
    assert parsed["error"] == str(exc)
    if hint:
        assert hint in parsed["hint"]


def test_paginated_without_total_or_page_size_cannot_claim_more():
    parsed = json.loads(_paginated([1, 2], start_at=0))
    assert parsed["has_more"] is False
    assert parsed["next_start_at"] is None
