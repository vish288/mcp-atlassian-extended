"""Tests for date resolution utility."""

from __future__ import annotations

from datetime import datetime, timedelta

from mcp_atlassian_extended.servers.confluence_extended import _resolve_date


def test_resolve_today():
    result = _resolve_date("today")
    assert result == datetime.now().strftime("%Y-%m-%d")


def test_resolve_tomorrow():
    result = _resolve_date("tomorrow")
    expected = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    assert result == expected


def test_resolve_plus_days():
    result = _resolve_date("+7d")
    expected = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
    assert result == expected


def test_resolve_minus_days():
    result = _resolve_date("-3d")
    expected = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d")
    assert result == expected


def test_resolve_iso_date():
    result = _resolve_date("2026-06-15")
    assert result == "2026-06-15"


def test_resolve_next_week():
    result = _resolve_date("next week")
    d = datetime.strptime(result, "%Y-%m-%d")
    assert d.weekday() == 0  # Monday
