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


class _FrozenMonday(datetime):
    @classmethod
    def now(cls, tz=None):
        # 2026-03-02 is a Monday.
        return cls(2026, 3, 2, 12, 0, tzinfo=tz)


def test_next_week_from_monday_is_the_following_monday(monkeypatch):
    """On a Monday, 'next week' is +7 days, not the same day: ``(7 - weekday) % 7``
    is 0 on Monday, and the ``or 7`` is what turns it into a full week."""
    monkeypatch.setattr(confluence_extended, "datetime", _FrozenMonday)
    assert _resolve_date("next week") == "2026-03-09"
