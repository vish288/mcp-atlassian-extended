# Minimal non-root image for mcp-atlassian-extended.
# Build:  docker build -t mcp-atlassian-extended .
# Run (stdio is for local clients; for a network bind set a bearer token):
#   docker run --rm -i \
#     -e JIRA_URL=https://your-company.atlassian.net \
#     -e JIRA_USERNAME=you@company.com -e JIRA_API_TOKEN=... \
#     mcp-atlassian-extended
# The image defaults to locked read-only (MCP_READ_ONLY=true); pass
# -e MCP_READ_ONLY=false to allow writes.
FROM python:3.13-slim

# uv binary, version-pinned; dependencies come from the committed uv.lock.
COPY --from=ghcr.io/astral-sh/uv:0.9.2 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never

WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
RUN uv sync --frozen --no-dev \
    && useradd --create-home --uid 10001 app \
    && chown -R app:app /app

USER app
ENV PATH="/app/.venv/bin:$PATH" \
    MCP_READ_ONLY=true

ENTRYPOINT ["mcp-atlassian-extended"]
