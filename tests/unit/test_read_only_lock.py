"""Locked read-only: one deployer-set switch (``MCP_READ_ONLY``) hides write tools.

Covers the shared config semantics (OR across sources, fail-closed on unrecognised
values, falsy-beside-truthy warning), the lifespan hide (write tools and
write-workflow prompts absent from a locked server), the decorator-level guard that
stays as defence in depth, and a src-scan pinning that nothing re-enables visibility
at runtime.

Importing the server package registers every tool and prompt, so the registry-derived
assertions below are not order-dependent.
"""

from __future__ import annotations

import asyncio
import contextlib
import re
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from click.testing import CliRunner
from fastmcp import Client

from mcp_atlassian_extended import servers
from mcp_atlassian_extended.config import ConfluenceConfig, JiraConfig, _read_only
from mcp_atlassian_extended.servers import mcp

_SRC = Path(__file__).resolve().parents[2] / "src" / "mcp_atlassian_extended"


# ── config semantics ────────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Config/assembly here must not inherit a ``MCP_READ_ONLY`` exported for the gate."""
    monkeypatch.delenv("MCP_READ_ONLY", raising=False)
    monkeypatch.delenv("ATLASSIAN_READ_ONLY", raising=False)


def test_mcp_read_only_env_locks(monkeypatch):
    monkeypatch.setenv("MCP_READ_ONLY", "true")
    assert _read_only("ATLASSIAN_READ_ONLY") is True


def test_alias_env_locks(monkeypatch):
    monkeypatch.setenv("ATLASSIAN_READ_ONLY", "true")
    assert _read_only("ATLASSIAN_READ_ONLY") is True


def test_value_is_stripped(monkeypatch):
    monkeypatch.setenv("MCP_READ_ONLY", "  true  ")
    assert _read_only("ATLASSIAN_READ_ONLY") is True


def test_alias_false_cannot_unlock(monkeypatch, caplog):
    monkeypatch.setenv("MCP_READ_ONLY", "true")
    monkeypatch.setenv("ATLASSIAN_READ_ONLY", "false")
    with caplog.at_level("WARNING"):
        assert _read_only("ATLASSIAN_READ_ONLY") is True
    assert any("ignoring ATLASSIAN_READ_ONLY=false" in r.message for r in caplog.records)


def test_mcp_false_cannot_unlock_alias(monkeypatch, caplog):
    monkeypatch.setenv("MCP_READ_ONLY", "false")
    monkeypatch.setenv("ATLASSIAN_READ_ONLY", "true")
    with caplog.at_level("WARNING"):
        assert _read_only("ATLASSIAN_READ_ONLY") is True
    assert any("ignoring MCP_READ_ONLY=false" in r.message for r in caplog.records)


def test_falsy_alone_is_the_default(monkeypatch, caplog):
    monkeypatch.setenv("MCP_READ_ONLY", "false")
    with caplog.at_level("WARNING"):
        assert _read_only("ATLASSIAN_READ_ONLY") is False
    assert caplog.records == []


def test_unrecognised_value_fails_closed(monkeypatch, caplog):
    monkeypatch.setenv("MCP_READ_ONLY", "maybe")
    with caplog.at_level("WARNING"):
        assert _read_only("ATLASSIAN_READ_ONLY") is True
    assert any("locking on unrecognised MCP_READ_ONLY=maybe" in r.message for r in caplog.records)


def test_no_read_only_flag_rejected():
    """``--read-only`` is a plain flag, so ``--no-read-only`` is rejected (exit 2)."""
    from mcp_atlassian_extended import main

    result = CliRunner().invoke(main, ["--no-read-only"])
    assert result.exit_code == 2


# ── lifespan hide ────────────────────────────────────────────────────


async def test_locked_boot_hides_write_tools_and_prompts(monkeypatch):
    """Boot the real lifespan read-only via a real Client; write tools and
    write-workflow prompts are absent and the instructions announce the lock."""
    monkeypatch.setenv("MCP_READ_ONLY", "true")
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    monkeypatch.setenv("JIRA_PAT", "t")

    transforms_before = len(mcp._transforms)
    instructions_before = mcp.instructions
    servers._injected_configs = None
    try:
        async with Client(mcp) as client:
            tool_names = {t.name for t in await client.list_tools()}
            prompt_names = {p.name for p in await client.list_prompts()}
            instructions = mcp.instructions
        write_tools = {t.name for t in await mcp._list_tools() if "write" in t.tags}
        assert write_tools, "expected some write tools in the registry"
        assert write_tools.isdisjoint(tool_names)
        # Write-workflow prompts (incl. plan_sprint, whose last step moves issues)
        # are hidden; the read-only prompts stay listed.
        hidden_prompts = {"create_ticket", "close_ticket", "manage_attachments", "plan_sprint"}
        assert hidden_prompts.isdisjoint(prompt_names)
        assert {"team_availability"} <= prompt_names
        assert "locked read-only" in (instructions or "")
    finally:
        del mcp._transforms[transforms_before:]
        mcp.instructions = instructions_before
        servers._injected_configs = None


async def _hidden_tool_names(client) -> set[str]:
    """Tool names in the raw registry but absent from a locked client's listing."""
    listed = {t.name for t in await client.list_tools()}
    return {t.name for t in await mcp._list_tools()} - listed


async def test_hidden_set_equals_write_tag_set(readonly_client):
    """The tools removed from a locked listing are exactly the ``write``-tagged tools."""
    client, _router = readonly_client
    hidden = await _hidden_tool_names(client)
    write_tools = {t.name for t in await mcp._list_tools() if "write" in t.tags}
    assert hidden == write_tools


async def test_hidden_set_equals_read_only_hint_false_set(readonly_client):
    """Hidden tools are exactly those annotated ``readOnlyHint is False``."""
    client, _router = readonly_client
    hidden = await _hidden_tool_names(client)
    write_hint = {
        t.name
        for t in await mcp._list_tools()
        if t.annotations is not None and t.annotations.read_only_hint is False
    }
    assert hidden == write_hint


async def test_hidden_set_equals_write_decorator_set(readonly_client):
    """Hidden tools are exactly those whose ``@tool_result(write=…)`` guard refuses."""
    client, _router = readonly_client
    hidden = await _hidden_tool_names(client)
    guarded: set[str] = set()
    for tool in await mcp._list_tools():
        # Read tools reach their body and raise without clients; write tools refuse
        # at the guard before the body, returning an error result.
        result = None
        with contextlib.suppress(Exception):
            result = await tool.fn(_stub_ctx(read_only=True))
        if result is not None and result.is_error and "disabled" in result.content[0].text.lower():
            guarded.add(tool.name)
    assert hidden == guarded


async def test_call_hidden_write_tool_is_unknown_tool(readonly_client):
    """A client that cached the full list and calls a hidden write tool gets 'Unknown tool'."""
    client, _router = readonly_client
    result = await client.call_tool(
        "jira_create_issue",
        {"project_key": "PROJ", "summary": "S"},
        raise_on_error=False,
    )
    assert result.is_error is True
    assert "unknown tool" in result.content[0].text.lower()


async def test_confluence_only_read_only_hides_nothing():
    """All write tools and write prompts are Jira's; a Confluence-only lock hides nothing."""
    assert await servers._write_names(mcp, "confluence") == set()


async def _boot_and_capture_lock_log(caplog, *, configs=None):
    """Boot the real lifespan once, returning the LOCKED log line (snapshots/restores mcp)."""
    transforms_before = len(mcp._transforms)
    instructions_before = mcp.instructions
    servers._injected_configs = configs
    try:
        with caplog.at_level("INFO"):
            async with servers.lifespan(mcp):
                pass
        return next((r.message for r in caplog.records if "LOCKED" in r.message), None)
    finally:
        del mcp._transforms[transforms_before:]
        mcp.instructions = instructions_before
        servers._injected_configs = None


async def test_locked_log_names_env_source(monkeypatch, caplog):
    """A lock from the env names the env var that set it."""
    monkeypatch.setenv("MCP_READ_ONLY", "true")
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    monkeypatch.setenv("JIRA_PAT", "t")
    message = await _boot_and_capture_lock_log(caplog)
    assert message is not None
    assert "MCP_READ_ONLY" in message


async def test_locked_log_names_read_only_flag(caplog):
    """A lock set only by ``--read-only`` (no env source) names ``--read-only``."""
    configs = (
        JiraConfig(url="https://j.example.com", token="t", read_only=True),
        ConfluenceConfig(url="https://c.example.com", token="t", read_only=True),
    )
    message = await _boot_and_capture_lock_log(caplog, configs=configs)
    assert message is not None
    assert "--read-only" in message


# ── decorator-level guard (defence in depth) ─────────────────────────


def _stub_ctx(*, read_only: bool) -> Any:
    return SimpleNamespace(
        lifespan_context={
            "jira_config": JiraConfig(read_only=read_only),
            "confluence_config": ConfluenceConfig(read_only=read_only),
        }
    )


def _write_tool_names() -> list[str]:
    """Write-tagged tool names, resolved at collection time so each is its own case."""
    tools = asyncio.run(mcp._list_tools())
    return sorted(t.name for t in tools if "write" in t.tags)


@pytest.mark.parametrize("tool_name", _write_tool_names())
async def test_guard_still_refuses_when_not_hidden(tool_name):
    """Even reached directly (tool not hidden), each write tool refuses in read-only.

    Parametrized so a failure names the offending tool rather than the whole loop.
    """
    tool = next(t for t in await mcp._list_tools() if t.name == tool_name)
    result = await tool.fn(_stub_ctx(read_only=True))
    assert result.is_error is True
    text = result.content[0].text.lower()
    assert "disabled" in text or "read-only" in text
    assert "ask the deployer" in text


# ── src-scan: no runtime toggle or unlock ────────────────────────────


@pytest.mark.parametrize(
    "pattern",
    [
        r"\.enable\(",
        r"enable_components\(",
        r"disable_components\(",
        r"reset_visibility\(",
        r"add_transform\(",
        r"\._transforms",
        r"read_only\s*=\s*False",
    ],
)
def test_src_has_no_runtime_toggle_or_unlock(pattern):
    rx = re.compile(pattern)
    for path in _SRC.rglob("*.py"):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            assert not rx.search(line), f"{path}:{i} matches {pattern!r}: {line.strip()}"
