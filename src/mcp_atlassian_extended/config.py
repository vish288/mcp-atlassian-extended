"""Configuration for Atlassian Extended MCP server."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass


@dataclass
class JiraConfig:
    """Jira connection configuration from environment.

    Supports two authentication modes:
    - Bearer token: Set JIRA_PAT or JIRA_PERSONAL_TOKEN (for Jira Data Center / self-hosted)
    - Basic auth: Set JIRA_USERNAME + JIRA_API_TOKEN (for Jira Cloud)
    """

    url: str = ""
    token: str = ""
    username: str = ""
    api_token: str = ""
    read_only: bool = False
    timeout: int = 30
    ssl_verify: bool = True

    @classmethod
    def from_env(cls) -> JiraConfig:
        url = os.getenv("JIRA_URL", "").rstrip("/")
        token = (
            os.getenv("JIRA_PAT") or os.getenv("JIRA_PERSONAL_TOKEN") or os.getenv("JIRA_TOKEN", "")
        )
        username = os.getenv("JIRA_USERNAME", "")
        api_token = os.getenv("JIRA_API_TOKEN", "")
        read_only = os.getenv("ATLASSIAN_READ_ONLY", "false").lower() in (
            "true",
            "1",
            "yes",
        )
        timeout = int(os.getenv("JIRA_TIMEOUT", "30"))
        ssl_verify = os.getenv("JIRA_SSL_VERIFY", "true").lower() not in (
            "false",
            "0",
            "no",
        )
        return cls(
            url=url,
            token=token,
            username=username,
            api_token=api_token,
            read_only=read_only,
            timeout=timeout,
            ssl_verify=ssl_verify,
        )

    @property
    def is_configured(self) -> bool:
        has_bearer = bool(self.url and self.token)
        has_basic = bool(self.url and self.username and self.api_token)
        return has_bearer or has_basic

    @property
    def auth_header(self) -> dict[str, str]:
        """Return the appropriate Authorization header."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        if self.username and self.api_token:
            creds = base64.b64encode(f"{self.username}:{self.api_token}".encode()).decode()
            return {"Authorization": f"Basic {creds}"}
        return {}


@dataclass
class ConfluenceConfig:
    """Confluence connection configuration from environment.

    Supports two authentication modes:
    - Bearer token: Set CONFLUENCE_PAT or CONFLUENCE_PERSONAL_TOKEN (Data Center)
    - Basic auth: Set CONFLUENCE_USERNAME + CONFLUENCE_API_TOKEN (Cloud)
    """

    url: str = ""
    token: str = ""
    username: str = ""
    api_token: str = ""
    read_only: bool = False
    timeout: int = 30
    ssl_verify: bool = True

    @classmethod
    def from_env(cls) -> ConfluenceConfig:
        url = os.getenv("CONFLUENCE_URL", "").rstrip("/")
        token = (
            os.getenv("CONFLUENCE_PAT")
            or os.getenv("CONFLUENCE_PERSONAL_TOKEN")
            or os.getenv("CONFLUENCE_TOKEN", "")
        )
        username = os.getenv("CONFLUENCE_USERNAME", "")
        api_token = os.getenv("CONFLUENCE_API_TOKEN", "")
        read_only = os.getenv("ATLASSIAN_READ_ONLY", "false").lower() in (
            "true",
            "1",
            "yes",
        )
        timeout = int(os.getenv("CONFLUENCE_TIMEOUT", "30"))
        ssl_verify = os.getenv("CONFLUENCE_SSL_VERIFY", "true").lower() not in (
            "false",
            "0",
            "no",
        )
        return cls(
            url=url,
            token=token,
            username=username,
            api_token=api_token,
            read_only=read_only,
            timeout=timeout,
            ssl_verify=ssl_verify,
        )

    @property
    def is_configured(self) -> bool:
        has_bearer = bool(self.url and self.token)
        has_basic = bool(self.url and self.username and self.api_token)
        return has_bearer or has_basic

    @property
    def auth_header(self) -> dict[str, str]:
        """Return the appropriate Authorization header."""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        if self.username and self.api_token:
            creds = base64.b64encode(f"{self.username}:{self.api_token}".encode()).decode()
            return {"Authorization": f"Basic {creds}"}
        return {}
