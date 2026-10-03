"""Extended MCP tools for Jira and Confluence."""

import asyncio
import logging

import click
from dotenv import load_dotenv

from .config import ConfluenceConfig, JiraConfig


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
@click.option("--jira-token", envvar="JIRA_PAT", help="Jira personal access token (Data Center)")
@click.option("--jira-username", envvar="JIRA_USERNAME", help="Jira username/email (Cloud)")
@click.option("--jira-api-token", envvar="JIRA_API_TOKEN", help="Jira API token (Cloud)")
@click.option("--confluence-url", envvar="CONFLUENCE_URL", help="Confluence instance URL")
@click.option(
    "--confluence-token", envvar="CONFLUENCE_PAT", help="Confluence personal access token"
)
@click.option(
    "--confluence-username", envvar="CONFLUENCE_USERNAME", help="Confluence username/email (Cloud)"
)
@click.option(
    "--confluence-api-token", envvar="CONFLUENCE_API_TOKEN", help="Confluence API token (Cloud)"
)
@click.option("--read-only", is_flag=True, help="Disable write operations")
def main(
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
    # then let explicit CLI flags win — no writing back through os.environ.
    jira_config = JiraConfig.from_env()
    confluence_config = ConfluenceConfig.from_env()
    if jira_url:
        jira_config.url = jira_url.rstrip("/")
    if jira_token:
        jira_config.token = jira_token
    if jira_username:
        jira_config.username = jira_username
    if jira_api_token:
        jira_config.api_token = jira_api_token
    if confluence_url:
        confluence_config.url = confluence_url.rstrip("/")
    if confluence_token:
        confluence_config.token = confluence_token
    if confluence_username:
        confluence_config.username = confluence_username
    if confluence_api_token:
        confluence_config.api_token = confluence_api_token
    if read_only:
        jira_config.read_only = True
        confluence_config.read_only = True

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

    run_kwargs: dict = {"transport": transport}
    if transport != "stdio":
        run_kwargs["host"] = host
        run_kwargs["port"] = port

    asyncio.run(mcp.run_async(show_banner=False, **run_kwargs))


if __name__ == "__main__":
    main()
