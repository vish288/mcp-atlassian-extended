"""Tests for CLI entry point."""

from __future__ import annotations

from unittest.mock import patch

from click.testing import CliRunner

from mcp_atlassian_extended import main


def test_sse_transport_warns_deprecated():
    """--transport sse prints a deprecation warning but still runs."""
    runner = CliRunner()
    with patch("mcp_atlassian_extended.asyncio.run") as mock_run:
        result = runner.invoke(main, ["--transport", "sse"])
    assert result.exit_code == 0
    assert "Warning:" in result.stderr
    assert "HTTP+SSE transport" in result.stderr
    assert "deprecated in MCP 2026-07-28" in result.stderr
    assert "streamable-http" in result.stderr
    mock_run.assert_called_once()
