"""Shared response handling for both clients."""

from __future__ import annotations

import httpx
import pytest

from mcp_atlassian_extended.clients._http import _parse_json, _raise_for_atlassian
from mcp_atlassian_extended.exceptions import (
    AtlassianApiError,
    AtlassianAuthError,
    TeamCalendarsUnavailableError,
)


@pytest.mark.parametrize(
    ("status", "not_found", "exc"),
    [
        (401, None, AtlassianAuthError),
        (403, None, AtlassianAuthError),
        (404, None, AtlassianApiError),
        (404, TeamCalendarsUnavailableError, TeamCalendarsUnavailableError),
        (500, TeamCalendarsUnavailableError, AtlassianApiError),
    ],
)
def test_raise_for_atlassian(status, not_found, exc):
    with pytest.raises(exc) as info:
        _raise_for_atlassian(httpx.Response(status, text="body"), not_found=not_found)
    assert info.value.status_code == status
    assert info.value.body == "body"


def test_raise_for_atlassian_passes_success():
    _raise_for_atlassian(httpx.Response(204))


@pytest.mark.parametrize(
    ("response", "expected"),
    [
        (httpx.Response(204), None),
        (httpx.Response(200, json={"a": 1}), {"a": 1}),
    ],
)
def test_parse_json(response, expected):
    assert _parse_json(response) == expected


@pytest.mark.parametrize(
    ("response", "match"),
    [
        (httpx.Response(200, text="<html>", headers={"content-type": "text/html"}), "HTML"),
        (httpx.Response(200, text="{not json"), "JSON parse error"),
    ],
)
def test_parse_json_rejects_non_json(response, match):
    with pytest.raises(AtlassianApiError, match=match):
        _parse_json(response)
