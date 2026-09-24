"""Tests for date resolution — clock frozen at Wednesday 2026-03-04."""

from __future__ import annotations

from datetime import datetime

import pytest

from mcp_atlassian_extended.servers import confluence_extended
from mcp_atlassian_extended.servers.confluence_extended import _resolve_date


class _Frozen(datetime):
    @classmethod
    def now(cls, tz=None):
        return cls(2026, 3, 4, 12, 0, tzinfo=tz)


@pytest.fixture(autouse=True)
def _freeze(monkeypatch):
    monkeypatch.setattr(confluence_extended, "datetime", _Frozen)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("today", "2026-03-04"),
        ("tomorrow", "2026-03-05"),
        ("+7d", "2026-03-11"),
        ("-3d", "2026-03-01"),
        ("next week", "2026-03-09"),
        ("2026-06-15", "2026-06-15"),
    ],
)
def test_resolve(value, expected):
    assert _resolve_date(value) == expected
