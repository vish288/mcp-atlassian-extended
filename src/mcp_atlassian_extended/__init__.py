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

    if jira_url:
        os.environ["JIRA_URL"] = jira_url
    if jira_token:
        os.environ["JIRA_PAT"] = jira_token
    if jira_username:
        os.environ["JIRA_USERNAME"] = jira_username
    if jira_api_token:
        os.environ["JIRA_API_TOKEN"] = jira_api_token
    if confluence_url:
        os.environ["CONFLUENCE_URL"] = confluence_url
    if confluence_token:
        os.environ["CONFLUENCE_PAT"] = confluence_token
    if confluence_username:
        os.environ["CONFLUENCE_USERNAME"] = confluence_username
    if confluence_api_token:
        os.environ["CONFLUENCE_API_TOKEN"] = confluence_api_token
    if read_only:
        os.environ["ATLASSIAN_READ_ONLY"] = "true"

    from .servers import mcp

    run_kwargs: dict = {"transport": transport}
    if transport != "stdio":
        run_kwargs["host"] = host
        run_kwargs["port"] = port

    asyncio.run(mcp.run_async(show_banner=False, **run_kwargs))


if __name__ == "__main__":
    main()
