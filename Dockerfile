# Minimal non-root image for mcp-atlassian-extended.
# Build:  docker build -t mcp-atlassian-extended .
# Run (stdio is for local clients; for a network bind set a bearer token):
#   docker run --rm -i \
#     -e JIRA_URL=https://your-company.atlassian.net \
#     -e JIRA_USERNAME=you@company.com -e JIRA_API_TOKEN=... \
#     -e MCP_READ_ONLY=true \
#     mcp-atlassian-extended
FROM python:3.13-slim

# uv for a fast, no-cache install of the built package.
COPY --from=ghcr.io/astral-sh/uv:0.9.2 /uv /uvx /bin/

WORKDIR /app
COPY . .
RUN uv pip install --system --no-cache . \
    && useradd --create-home --uid 10001 app

USER app
ENTRYPOINT ["mcp-atlassian-extended"]
