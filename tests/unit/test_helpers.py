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
from mcp_atlassian_extended.servers._helpers import _err, _load_file, _paginated

API = {"error", "status_code", "body", "hint"}


class TestLoadFileSecurity:
    """``_load_file`` is the single traversal guard behind both resource and
    prompt loading (``resources._load`` / ``prompts._load_prompt`` delegate here),
    so the path-injection cases live once, next to the helper."""

    @pytest.mark.parametrize(
        "bad", ["../../../etc/passwd", "subdir/file.md", "subdir\\file.md", ".."]
    )
    def test_rejects_traversal(self, tmp_path, bad):
        with pytest.raises(ValueError, match="Invalid filename"):
            _load_file(str(tmp_path), bad)


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
        (
            ValueError("file_path resolves outside the upload directory /r: /x"),
            {"error", "hint"},
            "ATLASSIAN_UPLOAD_DIR",
        ),
        (
            ValueError("save_path ... downloads are written under the download directory /r"),
            {"error", "hint"},
            "ATLASSIAN_DOWNLOAD_DIR",
        ),
        (ValueError("File too large"), {"error", "hint"}, "100MB"),
        (ValueError("anything else"), {"error"}, None),
        (FileNotFoundError("gone"), {"error", "hint"}, "File not found"),
        (AtlassianError("base"), {"error"}, None),
        (RuntimeError("bug"), {"error"}, None),
    ],
    ids=lambda v: type(v).__name__ if isinstance(v, Exception) else None,
)
def test_err_key_set(exc, keys, hint):
    parsed = _err(exc)
    assert set(parsed) == keys
    assert parsed["error"] == str(exc)
    if hint:
        assert hint in parsed["hint"]


def test_paginated_without_total_or_page_size_cannot_claim_more():
    parsed = json.loads(_paginated([1, 2], start_at=0))
    assert parsed["has_more"] is False
    assert parsed["next_start_at"] is None


def test_paginated_full_page_without_total_claims_more():
    """No total from the API: a full page (len == max_results) must report more,
    so the tail is not silently dropped. Under-reporting here is the bug the
    `==` guard fixes — do not let it regress to `<`."""
    parsed = json.loads(_paginated([1, 2], start_at=4, max_results=2))
    assert parsed["has_more"] is True
    assert parsed["next_start_at"] == 6


def test_paginated_partial_page_without_total_stops():
    parsed = json.loads(_paginated([1], start_at=4, max_results=2))
    assert parsed["has_more"] is False
    assert parsed["next_start_at"] is None


def test_paginated_with_total_pages_until_total():
    parsed = json.loads(_paginated([1, 2], start_at=0, total=5, max_results=2))
    assert parsed["total"] == 5
    assert parsed["has_more"] is True
    assert parsed["next_start_at"] == 2
    last = json.loads(_paginated([1], start_at=4, total=5, max_results=2))
    assert last["has_more"] is False
    assert last["next_start_at"] is None
