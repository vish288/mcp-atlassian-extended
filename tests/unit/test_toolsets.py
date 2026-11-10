"""MCP_TOOLSETS: coarse tool groups (workbench-backlog#160).

``MCP_TOOLSETS`` (or ``--toolsets``) selects named groups of the raw domain tags the tools
already carry, switching ``tools/list`` to an allowlist of just those tools so a client with
a tool budget sees fewer. The ``core`` tags (users + metadata) are unioned into every
selection. Resources and prompts stay listed regardless, and ``MCP_READ_ONLY`` still applies
after the selection and only ever removes tools. Unset or ``all`` lists every tool; an
unknown group name exits 2 with the valid list.

Each case boots a real ``Client(mcp)`` so the env → lifespan → ``_apply_toolsets`` wiring is
exercised, and restores the module-level server's visibility transforms afterwards.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from click.testing import CliRunner
from fastmcp import Client

from mcp_atlassian_extended import main
from mcp_atlassian_extended.servers import (
    CORE_TAGS,
    TOOLSET_GROUPS,
    UnknownToolsetError,
    mcp,
    parse_toolsets,
)

# Non-domain tags every tool carries; the remainder is its one domain tag.
_FRAME_TAGS = {"jira", "confluence", "read", "write"}

# Per group: (tools listed, tools listed under read-only). Measured against the server;
# every count includes the always-on `core` tools (users + metadata).
_EXPECTED = {
    "issues": (11, 4),
    "agile": (8, 7),
    "release": (6, 4),
    "calendars": (7, 7),
}
_CORE = (3, 3)
_ALL_TOOLS = 23
_ALL_TOOLS_RO = 13
_RESOURCES = 15
_PROMPTS = 5


async def _boot(
    monkeypatch, toolsets: str | None, *, read_only: bool = False
) -> tuple[set[str], int, int]:
    """Boot ``mcp`` through a real client with the given MCP_TOOLSETS / MCP_READ_ONLY env and
    return (tool names, resource count, prompt count), restoring visibility afterwards."""
    monkeypatch.setenv("JIRA_URL", "https://jira.example.com")
    monkeypatch.setenv("JIRA_PAT", "t")
    monkeypatch.setenv("CONFLUENCE_URL", "https://confluence.example.com")
    monkeypatch.setenv("CONFLUENCE_PAT", "t")
    monkeypatch.delenv("ATLASSIAN_READ_ONLY", raising=False)
    monkeypatch.delenv("MCP_READ_ONLY", raising=False)
    monkeypatch.delenv("MCP_TOOLSETS", raising=False)
    if toolsets is not None:
        monkeypatch.setenv("MCP_TOOLSETS", toolsets)
    if read_only:
        monkeypatch.setenv("MCP_READ_ONLY", "true")
    tx = len(mcp._transforms)
    instructions = mcp.instructions
    try:
        async with Client(mcp) as client:
            tools = {t.name for t in await client.list_tools()}
            res = len(await client.list_resources())
            prm = len(await client.list_prompts())
        return tools, res, prm
    finally:
        del mcp._transforms[tx:]
        mcp.instructions = instructions


# ── the group map ──────────────────────────────────────────────────────


async def test_every_domain_tag_belongs_to_exactly_one_group():
    """Each tool's one domain tag is covered by exactly one group or ``core``, and no group
    names a tag no tool carries — so the map and the decorators cannot drift apart."""
    all_tools = await mcp._list_tools()
    domain_tags = {t for tool in all_tools for t in (set(tool.tags) - _FRAME_TAGS)}
    for tool in all_tools:
        assert len(set(tool.tags) - _FRAME_TAGS) == 1, tool.name
    group_tags = [tag for tags in TOOLSET_GROUPS.values() for tag in tags]
    assert len(group_tags) == len(set(group_tags)), "a tag appears in two groups"
    assert not (set(group_tags) & CORE_TAGS), "core overlaps a selectable group"
    assert set(group_tags) | CORE_TAGS == domain_tags


# ── selection ────────────────────────────────────────────────────────────


@pytest.mark.parametrize("group", sorted(_EXPECTED))
async def test_group_lists_expected_tools(monkeypatch, group):
    tools, res, prm = await _boot(monkeypatch, group)
    assert len(tools) == _EXPECTED[group][0]
    assert (res, prm) == (_RESOURCES, _PROMPTS)


async def test_core_alone_lists_core_tools(monkeypatch):
    tools, _, _ = await _boot(monkeypatch, "core")
    assert len(tools) == _CORE[0]
    assert tools == {"jira_search_users", "jira_list_projects", "jira_list_fields"}


@pytest.mark.parametrize("raw", [None, "", "  ", "all", "issues,all"])
async def test_unset_or_all_lists_everything(monkeypatch, raw):
    tools, res, prm = await _boot(monkeypatch, raw)
    assert len(tools) == _ALL_TOOLS
    assert (res, prm) == (_RESOURCES, _PROMPTS)


async def test_core_is_unioned_into_every_selection(monkeypatch):
    core_tools, _, _ = await _boot(monkeypatch, "core")
    issues_tools, _, _ = await _boot(monkeypatch, "issues")
    assert core_tools < issues_tools


async def test_multiple_groups_union(monkeypatch):
    tools, _, _ = await _boot(monkeypatch, "issues,agile")
    assert len(tools) == _EXPECTED["issues"][0] + 5


# ── read-only still wins after the allowlist ──────────────────────────────


@pytest.mark.parametrize("group", sorted(_EXPECTED))
async def test_group_plus_read_only_drops_writes(monkeypatch, group):
    all_tools = await mcp._list_tools()
    write_names = {t.name for t in all_tools if "write" in t.tags}
    tools, _, _ = await _boot(monkeypatch, group, read_only=True)
    assert len(tools) == _EXPECTED[group][1]
    assert not (tools & write_names)


async def test_all_read_only_count(monkeypatch):
    tools, _, prm = await _boot(monkeypatch, None, read_only=True)
    assert len(tools) == _ALL_TOOLS_RO
    # The read-only lock still runs after the (absent) allowlist and hides write-workflow
    # prompts; the one read prompt stays listed.
    assert prm == 1


# ── parsing / validation ──────────────────────────────────────────────────


@pytest.mark.parametrize("raw", [None, "", "   ", "all", "ALL", " agile , all "])
def test_parse_none_means_no_filter(raw):
    assert parse_toolsets(raw) is None


def test_parse_trims_lowercases_and_unions_core():
    assert parse_toolsets(" Agile ") == set(TOOLSET_GROUPS["agile"]) | set(CORE_TAGS)


def test_parse_core_alone_is_just_core():
    assert parse_toolsets("core") == set(CORE_TAGS)


def test_parse_unknown_raises_with_valid_list():
    with pytest.raises(UnknownToolsetError) as exc:
        parse_toolsets("issues,bogus")
    message = str(exc.value)
    assert "bogus" in message
    for name in [*TOOLSET_GROUPS, "core", "all"]:
        assert name in message


def test_cli_unknown_toolset_exits_2():
    # main() writes MCP_TOOLSETS into os.environ; patch.dict restores it so the bad value
    # does not leak into later tests (CliRunner's env= would not).
    env = {"JIRA_URL": "https://jira.example.com", "JIRA_TOKEN": "t"}
    with patch.dict("os.environ", env, clear=False):
        result = CliRunner().invoke(main, ["--toolsets", "bogus"])
    assert result.exit_code == 2
    assert "bogus" in result.output
    assert "issues" in result.output
