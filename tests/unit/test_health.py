"""/health liveness route (workbench-backlog#167).

A container or remote (HTTP transport) deployment needs an unauthenticated liveness URL.
FastMCP's auth guards ``/mcp``, not custom routes, so ``GET /health`` answers with the
server name and package version and nothing else — no config, no secrets.

The route is registered on the combined server the CLI entry point runs (``servers.mcp``,
which carries both the Jira and Confluence tools), so these tests hit that app's
``http_app()`` rather than a per-product sub-server.
"""

from __future__ import annotations

from importlib.metadata import version

import httpx

from mcp_atlassian_extended.servers import mcp


async def test_health_returns_ok_name_and_version():
    transport = httpx.ASGITransport(app=mcp.http_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://health.test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "status": "ok",
        "name": mcp.name,
        "version": version("mcp-atlassian-extended"),
    }


async def test_health_exposes_no_secrets():
    transport = httpx.ASGITransport(app=mcp.http_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://health.test") as client:
        response = await client.get("/health")
    assert set(response.json()) == {"status", "name", "version"}


async def test_health_is_served_by_the_combined_entry_point_app():
    """The route lives on the one FastMCP instance the CLI serves: its registry carries
    both Jira and Confluence tools, so this is the combined app, not a product server."""
    names = {tool.name for tool in await mcp._list_tools()}
    assert any(name.startswith("jira_") for name in names)
    assert any(name.startswith("confluence_") for name in names)
    paths = {getattr(route, "path", None) for route in mcp.http_app().routes}
    assert "/health" in paths
