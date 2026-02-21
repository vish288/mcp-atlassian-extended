"""Extended MCP tools for Jira and Confluence."""

import asyncio
import os

import click
from dotenv import load_dotenv


@click.command()
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse", "streamable-http"]),
    default="stdio",
    help="MCP transport type",
)
@click.option("--port", default=8000, help="Port for HTTP transports")
@click.option("--host", default="127.0.0.1", help="Host for HTTP transports")
@click.option("--jira-url", envvar="JIRA_URL", help="Jira instance URL")
@click.option("--jira-token", envvar="JIRA_PAT", help="Jira personal access token")
@click.option("--confluence-url", envvar="CONFLUENCE_URL", help="Confluence instance URL")
@click.option(
    "--confluence-token", envvar="CONFLUENCE_PAT", help="Confluence personal access token"
)
@click.option("--read-only", is_flag=True, help="Disable write operations")
def main(
    transport: str,
    port: int,
    host: str,
    jira_url: str | None,
    jira_token: str | None,
    confluence_url: str | None,
    confluence_token: str | None,
    read_only: bool,
) -> None:
    """Run the Atlassian Extended MCP server."""
    load_dotenv()

    if jira_url:
        os.environ["JIRA_URL"] = jira_url
    if jira_token:
        os.environ["JIRA_PAT"] = jira_token
    if confluence_url:
        os.environ["CONFLUENCE_URL"] = confluence_url
    if confluence_token:
        os.environ["CONFLUENCE_PAT"] = confluence_token
    if read_only:
        os.environ["ATLASSIAN_READ_ONLY"] = "true"

    from .servers import mcp

    run_kwargs: dict = {"transport": transport}
    if transport != "stdio":
        run_kwargs["host"] = host
        run_kwargs["port"] = port

    asyncio.run(mcp.run_async(**run_kwargs))


if __name__ == "__main__":
    main()
