"""Extended MCP tools for Jira and Confluence."""

import asyncio
import hmac
import logging
import os

import click
from dotenv import load_dotenv
from fastmcp.server.auth import TokenVerifier
from mcp.server.auth.provider import AccessToken

from .config import ConfluenceConfig, JiraConfig

# Hosts for which an HTTP transport needs no bearer token: the loopback
# interface is only reachable from the same machine.
_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


class _BearerTokenVerifier(TokenVerifier):
    """Accept exactly one shared bearer token, compared in constant time.

    StaticTokenVerifier resolves tokens with a dict ``.get``, which is not
    constant-time. For a single env-sourced secret, ``hmac.compare_digest``
    avoids leaking how long a matching prefix the presented token has through
    response timing. Compare encoded bytes: ``compare_digest`` raises TypeError
    on a str containing non-ASCII, so a non-ASCII bearer would otherwise 500
    instead of being rejected.
    """

    def __init__(self, token: str) -> None:
        super().__init__()
        self._token = token.encode()

    async def verify_token(self, token: str) -> AccessToken | None:
        if hmac.compare_digest(token.encode(), self._token):
            return AccessToken(token=token, client_id="mcp-atlassian-extended", scopes=[])
        return None


def _warn_argv_token(flag: str, env: str) -> None:
    click.echo(
        f"Warning: {flag} is deprecated. It puts the token in the process argument "
        f"list, where `ps` and shell history can read it. Set {env} instead.",
        err=True,
    )


@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable-http"]),
    default="stdio",
    help="MCP transport type (sse is deprecated; use streamable-http)",
)
@click.option("--port", default=8000, help="Port for HTTP transports")
@click.option("--host", default="127.0.0.1", help="Host for HTTP transports")
@click.option("--jira-url", envvar="JIRA_URL", help="Jira instance URL")
@click.option("--jira-token", hidden=True, help="Deprecated: set JIRA_PAT instead")
@click.option("--jira-username", envvar="JIRA_USERNAME", help="Jira username/email (Cloud)")
@click.option("--jira-api-token", hidden=True, help="Deprecated: set JIRA_API_TOKEN instead")
@click.option("--confluence-url", envvar="CONFLUENCE_URL", help="Confluence instance URL")
@click.option("--confluence-token", hidden=True, help="Deprecated: set CONFLUENCE_PAT instead")
@click.option(
    "--confluence-username", envvar="CONFLUENCE_USERNAME", help="Confluence username/email (Cloud)"
)
@click.option(
    "--confluence-api-token", hidden=True, help="Deprecated: set CONFLUENCE_API_TOKEN instead"
)
@click.option("--read-only", is_flag=True, help="Disable write operations")
@click.pass_context
def main(
    ctx: click.Context,
    transport: str,
    port: int,
    host: str,
    jira_url: str | None,
    jira_token: str | None,
    jira_username: str | None,
    jira_api_token: str | None,
    confluence_url: str | None,
    confluence_token: str | None,
    confluence_username: str | None,
    confluence_api_token: str | None,
    read_only: bool,
) -> None:
    """Run the Atlassian Extended MCP server."""
    load_dotenv()

    # Start from the environment (picks up timeout/ssl/token aliases and .env),
    # then let explicit CLI flags win — no writing back through os.environ. A bad
    # *_TIMEOUT is one clear line and exit 2 (D7), not a startup traceback.
    try:
        jira_config = JiraConfig.from_env()
        confluence_config = ConfluenceConfig.from_env()
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        ctx.exit(2)
    if jira_url:
        jira_config.url = jira_url.rstrip("/")
    if jira_token:
        _warn_argv_token("--jira-token", "JIRA_PAT")
        jira_config.token = jira_token
    if jira_username:
        jira_config.username = jira_username
    if jira_api_token:
        _warn_argv_token("--jira-api-token", "JIRA_API_TOKEN")
        jira_config.api_token = jira_api_token
    if confluence_url:
        confluence_config.url = confluence_url.rstrip("/")
    if confluence_token:
        _warn_argv_token("--confluence-token", "CONFLUENCE_PAT")
        confluence_config.token = confluence_token
    if confluence_username:
        confluence_config.username = confluence_username
    if confluence_api_token:
        _warn_argv_token("--confluence-api-token", "CONFLUENCE_API_TOKEN")
        confluence_config.api_token = confluence_api_token
    if read_only:
        jira_config.read_only = True
        confluence_config.read_only = True

    # Fail fast when NOTHING is configured (D7): the server used to start
    # "healthy" and report "not configured" on every tool call, so a broken
    # launch looked fine to the client. One product configured and the other not
    # is a legitimate single-product deployment and still starts.
    if not (jira_config.is_configured or confluence_config.is_configured):
        msg = (
            "No Atlassian product is configured. Set JIRA_URL plus either "
            "JIRA_USERNAME+JIRA_API_TOKEN (Cloud) or JIRA_PAT (Data Center), "
            "and/or the matching CONFLUENCE_* variables."
        )
        click.echo(f"Error: {msg}", err=True)
        ctx.exit(2)

    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s | %(message)s",
    )

    from .servers import configure, mcp

    configure(jira_config, confluence_config)

    if transport == "sse":
        click.echo(
            "Warning: --transport sse uses the HTTP+SSE transport, deprecated in MCP 2026-07-28. "
            "Use --transport streamable-http.",
            err=True,
        )

    bearer_token = os.getenv("ATLASSIAN_HTTP_BEARER_TOKEN", "").strip()

    run_kwargs: dict = {"transport": transport}
    if transport != "stdio":
        run_kwargs["host"] = host
        run_kwargs["port"] = port
        # DNS-rebinding protection: validate Host/Origin before a request reaches
        # the MCP endpoint. "auto" guards loopback-bound servers, allowing the
        # configured host plus localhost/127.0.0.1/[::1] and rejecting any other
        # Host (421) or cross-site Origin (403). Without this a rebinding page
        # could drive the local server with the operator's Atlassian credentials.
        run_kwargs["host_origin_protection"] = "auto"

        # Host/Origin protection is not authentication: an HTTP transport serves
        # every tool, with the operator's Atlassian credentials, to anyone who
        # reaches the port. Require a bearer token before binding anywhere but
        # loopback.
        if bearer_token:
            if len(bearer_token) < 16:
                msg = (
                    "ATLASSIAN_HTTP_BEARER_TOKEN must be at least 16 characters; "
                    "generate one with: openssl rand -hex 32"
                )
                raise click.UsageError(msg)
            mcp.auth = _BearerTokenVerifier(bearer_token)
        elif host not in _LOOPBACK_HOSTS:
            msg = (
                f"--host {host} would expose the Atlassian credentials to the network. "
                "Set ATLASSIAN_HTTP_BEARER_TOKEN (clients send it as "
                "'Authorization: Bearer <token>') or bind to 127.0.0.1."
            )
            raise click.UsageError(msg)

    asyncio.run(mcp.run_async(show_banner=False, **run_kwargs))


if __name__ == "__main__":
    main()
