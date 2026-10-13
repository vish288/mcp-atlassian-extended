"""HTTP transport security: Host/Origin validation and the shared bearer gate.

Before these guards the HTTP face ran with no auth and no DNS-rebinding
protection, so a rebinding page or anyone who reached the port could drive the
tools with the operator's Atlassian credentials. The CLI now passes
``host_origin_protection="auto"`` (rejects foreign Host 421 / cross-site Origin
403) and refuses any non-loopback bind unless ``ATLASSIAN_HTTP_BEARER_TOKEN`` is
set, in which case every request must carry that bearer.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import httpx
import pytest
from click.testing import CliRunner

from mcp_atlassian_extended import _BearerTokenVerifier, main
from mcp_atlassian_extended.servers import mcp as server_mcp

_TOKEN32 = "0123456789abcdef0123456789abcdef"

_INIT = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2026-07-28",
        "capabilities": {},
        "clientInfo": {"name": "test", "version": "0"},
    },
}


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def _reset_auth() -> Iterator[None]:
    """main() mutates the module-level server's auth; keep tests isolated."""
    yield
    server_mcp.auth = None


def _invoke(runner: CliRunner, args: list[str]):
    with (
        patch("mcp_atlassian_extended.asyncio.run") as mock_run,
        patch("mcp_atlassian_extended.servers.mcp.run_async", new_callable=MagicMock) as mock_async,
        patch("mcp_atlassian_extended.servers.configure"),
    ):
        result = runner.invoke(main, args)
    return result, mock_run, mock_async


def test_streamable_http_enables_host_origin_protection(runner: CliRunner) -> None:
    result, mock_run, mock_async = _invoke(
        runner, ["--transport", "streamable-http", "--port", "18771"]
    )
    assert result.exit_code == 0, result.output
    mock_run.assert_called_once()
    assert mock_async.call_args.kwargs["host_origin_protection"] == "auto"


def test_stdio_has_no_host_origin_protection(runner: CliRunner) -> None:
    result, _, mock_async = _invoke(runner, [])
    assert result.exit_code == 0, result.output
    assert "host_origin_protection" not in mock_async.call_args.kwargs


class TestHttpBearerToken:
    """A non-loopback HTTP bind needs a shared bearer token."""

    def test_non_loopback_without_token_exits(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ATLASSIAN_HTTP_BEARER_TOKEN", raising=False)
        result, mock_run, _ = _invoke(
            runner, ["--transport", "streamable-http", "--host", "0.0.0.0"]
        )
        assert result.exit_code == 2
        assert "ATLASSIAN_HTTP_BEARER_TOKEN" in result.output
        mock_run.assert_not_called()

    def test_token_sets_static_auth(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("ATLASSIAN_HTTP_BEARER_TOKEN", _TOKEN32)
        result, mock_run, _ = _invoke(
            runner, ["--transport", "streamable-http", "--host", "0.0.0.0"]
        )
        assert result.exit_code == 0, result.output
        assert isinstance(server_mcp.auth, _BearerTokenVerifier)
        mock_run.assert_called_once()

    def test_loopback_without_token_no_auth(
        self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.delenv("ATLASSIAN_HTTP_BEARER_TOKEN", raising=False)
        result, mock_run, _ = _invoke(
            runner, ["--transport", "streamable-http", "--host", "127.0.0.1"]
        )
        assert result.exit_code == 0, result.output
        assert server_mcp.auth is None
        mock_run.assert_called_once()

    def test_short_token_exits(self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ATLASSIAN_HTTP_BEARER_TOKEN", "deadbeef")  # 8 chars
        result, mock_run, _ = _invoke(
            runner, ["--transport", "streamable-http", "--host", "0.0.0.0"]
        )
        assert result.exit_code == 2
        assert "at least 16" in result.output
        mock_run.assert_not_called()

    def test_stdio_ignores_token(self, runner: CliRunner, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ATLASSIAN_HTTP_BEARER_TOKEN", _TOKEN32)
        result, mock_run, _ = _invoke(runner, [])
        assert result.exit_code == 0, result.output
        assert server_mcp.auth is None
        mock_run.assert_called_once()


async def _post(headers: dict[str, object]) -> httpx.Response:
    app = server_mcp.http_app(transport="streamable-http", host_origin_protection="auto")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://127.0.0.1:18771") as client:
        return await client.post("/mcp", json=_INIT, headers=headers)  # type: ignore[arg-type]


async def test_foreign_origin_rejected() -> None:
    resp = await _post(
        {
            "Host": "127.0.0.1:18771",
            "Origin": "http://evil.example",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
    )
    assert resp.status_code == 403


async def test_foreign_host_rejected() -> None:
    resp = await _post(
        {
            "Host": "evil.example",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
    )
    assert resp.status_code == 421


async def test_bearer_middleware_streamable_http(monkeypatch: pytest.MonkeyPatch) -> None:
    """Wire check: with auth set, the streamable-http ASGI app enforces the token."""
    # The real lifespan boots here; strip read-only env so a MCP_READ_ONLY run does
    # not lock the shared module-level server and leak the hide into later tests.
    monkeypatch.delenv("MCP_READ_ONLY", raising=False)
    monkeypatch.delenv("ATLASSIAN_READ_ONLY", raising=False)
    server_mcp.auth = _BearerTokenVerifier(_TOKEN32)
    try:
        app = server_mcp.http_app()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            async with app.router.lifespan_context(app):
                no_header = await client.post("/mcp", json={})
                wrong_token = await client.post(
                    "/mcp", json={}, headers={"Authorization": "Bearer wrong-token-value"}
                )
                # Non-ASCII must be rejected, not crash: compare_digest raises
                # TypeError on a non-ASCII str, which would 500 with a traceback.
                non_ascii = await client.post(
                    "/mcp", json={}, headers={"Authorization": "Bearer café".encode("latin-1")}
                )
                with_header = await client.post(
                    "/mcp", json={}, headers={"Authorization": f"Bearer {_TOKEN32}"}
                )
        assert no_header.status_code == 401
        assert wrong_token.status_code == 401
        assert non_ascii.status_code == 401
        # The middleware let the authenticated request reach the endpoint; any
        # non-401 status proves that.
        assert with_header.status_code != 401
    finally:
        server_mcp.auth = None
