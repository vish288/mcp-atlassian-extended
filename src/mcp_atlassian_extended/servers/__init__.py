"""Atlassian Extended MCP server — combines Jira and Confluence tools."""

from __future__ import annotations

import importlib
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from importlib.metadata import version
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from mcp.types import Icon

from ..clients.confluence import ConfluenceExtendedClient
from ..clients.jira import JiraExtendedClient
from ..config import ConfluenceConfig, JiraConfig, read_only_sources

_log = logging.getLogger(__name__)

_LOCK_SUFFIX = (
    " This deployment is locked read-only: write tools are not listed and cannot be"
    " enabled from the client."
)


async def _write_names(server: FastMCP, product: str) -> set[str]:
    """Names of write tools and write-workflow prompts for *product* in the raw registry.

    Uses ``_list_tools``/``_list_prompts`` (the raw registry, before any visibility
    transform) filtered by the ``write`` tag plus the product tag. Tag matching in
    ``disable`` is any-of, so the two products must be hidden by name, never by
    passing both product tags.
    """
    tools = {t.name for t in await server._list_tools() if {"write", product} <= t.tags}
    prompts = {p.name for p in await server._list_prompts() if {"write", product} <= p.tags}
    return tools | prompts


def _lock_read_only(server: FastMCP, *, names: set[str], sources: list[str]) -> None:
    """Hide the named write tools and prompts from a read-only server, for good.

    fastmcp 4.0.10: ``disable`` appends a ``Visibility(False)`` transform, so the
    named components drop out of ``tools/list`` / ``prompts/list`` and ``tools/call``
    on them returns a "Unknown tool" error. There is no client-reachable path to
    re-enable them — ``enable``/``enable_components`` are server code only and this
    server never calls them. ``_check_write`` stays as defence in depth.

    Idempotent via the instructions suffix: a re-entered lifespan (tests reuse the
    module-level ``mcp``) sees the suffix already present and does not stack transforms.
    """
    if not names or _LOCK_SUFFIX in (server.instructions or ""):
        return
    server.disable(names=names)
    server.instructions = (server.instructions or "") + _LOCK_SUFFIX
    named = f" ({', '.join(sources)})" if sources else ""
    _log.info("read-only: LOCKED%s — write tools and prompts hidden", named)


# MCP_TOOLSETS: coarse tool groups (workbench-backlog#160). A group is a named set of the
# raw domain tags the tools already carry; selecting one or more (MCP_TOOLSETS, a comma
# list, or --toolsets) switches tools/list to an allowlist of just those tools. `core`
# (users + metadata) is unioned into every selection — assignee lookup and custom-field
# discovery are prerequisites for both `issues` and `agile`; naming it explicitly is
# accepted but adds nothing. `release` names the Jira versions surface, the same job name
# as the sibling servers use; `calendars` is the whole Confluence surface today. Unset or
# `all` lists every tool; MCP_READ_ONLY still applies after the allowlist and only ever
# removes tools.
TOOLSET_GROUPS: dict[str, frozenset[str]] = {
    "issues": frozenset({"issues", "links", "attachments"}),
    "agile": frozenset({"agile"}),
    "release": frozenset({"versions"}),
    "calendars": frozenset({"calendars", "time_off"}),
}
CORE_TAGS: frozenset[str] = frozenset({"users", "metadata"})


class UnknownToolsetError(ValueError):
    """MCP_TOOLSETS named a group this server does not define."""


def parse_toolsets(raw: str | None) -> set[str] | None:
    """Resolve MCP_TOOLSETS / --toolsets to the set of raw tags to allowlist.

    None, empty/whitespace, or a list containing ``all`` returns ``None`` — no filtering,
    every tool listed (today's default). Names are lowercase, comma-separated, trimmed;
    ``core`` is accepted (its tags are always included anyway). An unknown name raises
    ``UnknownToolsetError`` naming the offenders and every valid group.
    """
    if not raw or not raw.strip():
        return None
    names = [n.strip().lower() for n in raw.split(",") if n.strip()]
    if not names or "all" in names:
        return None
    valid = {*TOOLSET_GROUPS, "core"}
    unknown = [n for n in names if n not in valid]
    if unknown:
        valid_list = ", ".join([*sorted(TOOLSET_GROUPS), "core", "all"])
        msg = f"Unknown MCP_TOOLSETS group(s): {', '.join(unknown)}. Valid groups: {valid_list}"
        raise UnknownToolsetError(msg)
    tags: set[str] = set(CORE_TAGS)
    for name in names:
        tags |= TOOLSET_GROUPS.get(name, frozenset())
    return tags


def _apply_toolsets(server: FastMCP, raw: str | None) -> None:
    """Allowlist tools for the selected toolsets, keeping every resource and prompt.

    fastmcp 4.1.6: ``enable(tags=..., only=True)`` switches to allowlist mode over *all*
    component types, so resources and prompts would vanish; the chained
    ``enable(components=...)`` re-lists every resource/template/prompt. This runs before the
    read-only ``disable`` so the lock stays the last word — an allowlisted group still
    carries its write tools until the lock removes them. A no-op when no toolset is
    selected, so the default server is untouched.
    """
    tags = parse_toolsets(raw)
    if tags is None:
        return
    server.enable(tags=tags, only=True).enable(components={"resource", "template", "prompt"})


# Configs the lifespan uses. The CLI (``__init__.main``) injects pre-built,
# CLI-overridden configs here so the values reach the lifespan directly instead
# of round-tripping through ``os.environ``. Left unset, the lifespan reads the
# environment itself — the path tests and ``uvx`` take.
_injected_configs: tuple[JiraConfig, ConfluenceConfig] | None = None


def configure(jira: JiraConfig, confluence: ConfluenceConfig) -> None:
    """Hand the lifespan pre-built configs instead of re-reading the environment."""
    global _injected_configs
    _injected_configs = (jira, confluence)


@asynccontextmanager
async def lifespan(server: FastMCP) -> AsyncIterator[dict[str, Any]]:
    if _injected_configs is not None:
        jira_config, confluence_config = _injected_configs
    else:
        jira_config = JiraConfig.from_env()
        confluence_config = ConfluenceConfig.from_env()

    pkg_version = version("mcp-atlassian-extended")
    _log.info("mcp-atlassian-extended %s starting", pkg_version)
    _log.info(
        "Jira: %s (configured: %s, read-only: %s)",
        jira_config.url or "(none)",
        jira_config.is_configured,
        jira_config.read_only,
    )
    _log.info(
        "Confluence: %s (configured: %s, read-only: %s)",
        confluence_config.url or "(none)",
        confluence_config.is_configured,
        confluence_config.read_only,
    )
    _log.info(
        "Attachments: upload root %s, download root %s",
        jira_config.upload_dir or str(Path.cwd()),
        jira_config.download_dir or str(Path.cwd() / "atlassian-downloads"),
    )

    _apply_toolsets(server, os.getenv("MCP_TOOLSETS"))

    names: set[str] = set()
    if jira_config.read_only:
        names |= await _write_names(server, "jira")
    if confluence_config.read_only:
        names |= await _write_names(server, "confluence")
    if names:
        # Env sources name themselves; a lock set only by the CLI flag (no env source)
        # must name --read-only so the LOCKED log says where the lock came from.
        sources = read_only_sources("ATLASSIAN_READ_ONLY") or ["--read-only"]
        _lock_read_only(server, names=names, sources=sources)

    jira_client = JiraExtendedClient(jira_config) if jira_config.is_configured else None
    confluence_client = (
        ConfluenceExtendedClient(confluence_config) if confluence_config.is_configured else None
    )

    try:
        yield {
            "jira_client": jira_client,
            "jira_config": jira_config,
            "confluence_client": confluence_client,
            "confluence_config": confluence_config,
        }
    finally:
        if jira_client:
            await jira_client.close()
        if confluence_client:
            await confluence_client.close()


mcp = FastMCP(
    name="Atlassian Extended MCP Server",
    version=version("mcp-atlassian-extended"),
    website_url="https://vish288.github.io/mcp-install?server=mcp-atlassian-extended",
    icons=[
        Icon(
            src="https://raw.githubusercontent.com/vish288/mcp-atlassian-extended/main/assets/icon.svg",
            mime_type="image/svg+xml",
            sizes=["any"],
        )
    ],
    instructions=(
        "Extended tools for Jira and Confluence that complement mcp-atlassian. "
        "Provides issue creation/update with custom fields, issue links, "
        "attachments, agile boards/sprints, users, metadata, "
        "project versions (API v2), and calendar tools."
    ),
    lifespan=lifespan,
    # 2026-07-28 cache hints on list results: a modern client stops re-listing the
    # tools/prompts/resources each turn (#155). cacheScope is private because
    # resources/read can vary by the per-user token; the TTL is 5 minutes. Inert for
    # legacy clients. (cacheScope is fixed at construction, before the per-process
    # read-only decision, so it stays private rather than public-when-locked.)
    cache_ttl=300,
    cache_scope="private",
)


def _register_tools() -> None:
    """Import tool modules so their @mcp.tool decorators execute."""
    importlib.import_module(".jira_extended", __package__)
    importlib.import_module(".jira_agile", __package__)
    importlib.import_module(".jira_issues", __package__)
    importlib.import_module(".confluence_extended", __package__)
    importlib.import_module(".resources", __package__)
    importlib.import_module(".prompts", __package__)


_register_tools()
