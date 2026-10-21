"""Tests for CLI entry point."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from mcp_atlassian_extended import main


@pytest.fixture(autouse=True)
def _configured(monkeypatch: pytest.MonkeyPatch) -> None:
    """A product must be configured or the CLI exits 2 before reaching the body (D7).

    ``JIRA_TOKEN`` is the ``TOKEN`` alias and is not in ``_ALL_TOKEN_ENVS``, so the
    flag-plumbing tests (which delete PAT/API_TOKEN) still start Jira configured.
    Tests that want the unconfigured path clear the environment themselves.
    """
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    monkeypatch.setenv("JIRA_TOKEN", "baseline-tok")


# (flag, env var, configure() positional arg index, config attribute)
TOKEN_FLAGS = [
    ("--jira-token", "JIRA_PAT", 0, "token"),
    ("--jira-api-token", "JIRA_API_TOKEN", 0, "api_token"),
    ("--confluence-token", "CONFLUENCE_PAT", 1, "token"),
    ("--confluence-api-token", "CONFLUENCE_API_TOKEN", 1, "api_token"),
]

_ALL_TOKEN_ENVS = ["JIRA_PAT", "JIRA_API_TOKEN", "CONFLUENCE_PAT", "CONFLUENCE_API_TOKEN"]


@pytest.mark.parametrize("flag", [f[0] for f in TOKEN_FLAGS])
def test_token_flag_hidden_from_help(flag):
    """Deprecated token flags are hidden from --help; a control flag stays visible."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert flag not in result.output
    assert "--jira-username" in result.output


@pytest.mark.parametrize("flag,env_name,config_index,attr", TOKEN_FLAGS)
def test_token_flag_still_works_and_warns(monkeypatch, flag, env_name, config_index, attr):
    """Passing a token on argv still configures it but prints one stderr warning."""
    for env in _ALL_TOKEN_ENVS:
        monkeypatch.delenv(env, raising=False)
    runner = CliRunner()
    with (
        patch("mcp_atlassian_extended.asyncio.run") as mock_run,
        patch("mcp_atlassian_extended.servers.mcp.run_async", new_callable=MagicMock),
        patch("mcp_atlassian_extended.servers.configure") as mock_configure,
    ):
        result = runner.invoke(main, [flag, "argv-tok"])
    assert result.exit_code == 0
    mock_run.assert_called_once()
    assert getattr(mock_configure.call_args.args[config_index], attr) == "argv-tok"
    assert f"{flag} is deprecated" in result.stderr
    assert env_name in result.stderr
    assert "deprecated" not in result.stdout


@pytest.mark.parametrize("flag,env_name,config_index,attr", TOKEN_FLAGS)
def test_env_token_does_not_warn(monkeypatch, flag, env_name, config_index, attr):
    """A token supplied via env var prints no deprecation warning."""
    for env in _ALL_TOKEN_ENVS:
        monkeypatch.delenv(env, raising=False)
    monkeypatch.setenv(env_name, "env-tok")
    runner = CliRunner()
    with (
        patch("mcp_atlassian_extended.asyncio.run"),
        patch("mcp_atlassian_extended.servers.mcp.run_async", new_callable=MagicMock),
        patch("mcp_atlassian_extended.servers.configure"),
    ):
        result = runner.invoke(main, [])
    assert result.exit_code == 0
    assert "deprecated" not in result.stderr


def test_sse_transport_warns_deprecated():
    """--transport sse prints a deprecation warning but still runs."""
    runner = CliRunner()
    with (
        patch("mcp_atlassian_extended.asyncio.run") as mock_run,
        patch("mcp_atlassian_extended.servers.mcp.run_async", new_callable=MagicMock),
        patch("mcp_atlassian_extended.servers.configure"),
    ):
        result = runner.invoke(main, ["--transport", "sse"])
    assert result.exit_code == 0
    assert "Warning:" in result.stderr
    assert "HTTP+SSE transport" in result.stderr
    assert "deprecated in MCP 2026-07-28" in result.stderr
    assert "streamable-http" in result.stderr
    mock_run.assert_called_once()


def test_nothing_configured_exits_2_with_one_line():
    """D7: with no product configured the CLI exits 2 before starting, one stderr line."""
    runner = CliRunner()
    with patch.dict(os.environ, {}, clear=True):
        result = runner.invoke(main, [])
    assert result.exit_code == 2
    lines = [ln for ln in result.output.splitlines() if ln.strip()]
    assert len(lines) == 1
    assert lines[0].startswith("Error:")
    assert "No Atlassian product is configured" in lines[0]
    assert result.exception is None or isinstance(result.exception, SystemExit)


def test_single_product_configured_still_starts():
    """One product configured (Jira only) is a valid single-product deployment."""
    runner = CliRunner()
    env = {"JIRA_URL": "https://jira.example.com", "JIRA_TOKEN": "tok"}
    with (
        patch.dict(os.environ, env, clear=True),
        patch("mcp_atlassian_extended.asyncio.run") as mock_run,
        patch("mcp_atlassian_extended.servers.mcp.run_async", new_callable=MagicMock),
        patch("mcp_atlassian_extended.servers.configure"),
    ):
        result = runner.invoke(main, [])
    assert result.exit_code == 0
    mock_run.assert_called_once()


def test_invalid_timeout_exits_2():
    """A non-integer *_TIMEOUT is one clear line and exit 2, not a startup traceback."""
    runner = CliRunner()
    env = {"JIRA_URL": "https://jira.example.com", "JIRA_TOKEN": "tok", "JIRA_TIMEOUT": "30s"}
    with patch.dict(os.environ, env, clear=True):
        result = runner.invoke(main, [])
    assert result.exit_code == 2
    lines = [ln for ln in result.output.splitlines() if ln.strip()]
    assert len(lines) == 1
    assert lines[0].startswith("Error:")
    assert "JIRA_TIMEOUT" in lines[0]
