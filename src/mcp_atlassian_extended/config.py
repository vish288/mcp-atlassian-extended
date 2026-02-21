"""Configuration for Atlassian Extended MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class JiraConfig:
    """Jira connection configuration from environment."""

    url: str = ""
    token: str = ""
    read_only: bool = False
    timeout: int = 30
    ssl_verify: bool = True

    @classmethod
    def from_env(cls) -> JiraConfig:
        url = os.getenv("JIRA_URL", "").rstrip("/")
        token = os.getenv("JIRA_PAT") or os.getenv("JIRA_TOKEN", "")
        read_only = os.getenv("ATLASSIAN_READ_ONLY", "false").lower() in ("true", "1", "yes")
        timeout = int(os.getenv("JIRA_TIMEOUT", "30"))
        ssl_verify = os.getenv("JIRA_SSL_VERIFY", "true").lower() not in ("false", "0", "no")
        return cls(
            url=url, token=token, read_only=read_only, timeout=timeout, ssl_verify=ssl_verify
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.token)


@dataclass
class ConfluenceConfig:
    """Confluence connection configuration from environment."""

    url: str = ""
    token: str = ""
    read_only: bool = False
    timeout: int = 30
    ssl_verify: bool = True

    @classmethod
    def from_env(cls) -> ConfluenceConfig:
        url = os.getenv("CONFLUENCE_URL", "").rstrip("/")
        token = os.getenv("CONFLUENCE_PAT") or os.getenv("CONFLUENCE_TOKEN", "")
        read_only = os.getenv("ATLASSIAN_READ_ONLY", "false").lower() in ("true", "1", "yes")
        timeout = int(os.getenv("CONFLUENCE_TIMEOUT", "30"))
        ssl_verify = os.getenv("CONFLUENCE_SSL_VERIFY", "true").lower() not in ("false", "0", "no")
        return cls(
            url=url, token=token, read_only=read_only, timeout=timeout, ssl_verify=ssl_verify
        )

    @property
    def is_configured(self) -> bool:
        return bool(self.url and self.token)
