"""Configuration for Atlassian Extended MCP server."""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from typing import Any, ClassVar
from urllib.parse import urlparse


def _auth_header(token: str, username: str, api_token: str) -> dict[str, str]:
    """Build the Authorization header.

    Precedence: Cloud basic auth wins. If both *username* and *api_token* are set,
    Basic is used and any personal access token is ignored — otherwise a stray
    ``JIRA_TOKEN``/``CONFLUENCE_TOKEN`` in the environment would silently shadow
    the Cloud credentials. Bearer is used only when basic auth is incomplete.
    """
    if username and api_token:
        creds = base64.b64encode(f"{username}:{api_token}".encode()).decode()
        return {"Authorization": f"Basic {creds}"}
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def _config_for(prefix: str) -> dict[str, Any]:
    """Read ``<prefix>_*`` environment variables into constructor kwargs.

    ``ATLASSIAN_READ_ONLY`` is deliberately unprefixed: one switch covers both
    products.
    """

    def env(name: str, default: str = "") -> str:
        return os.getenv(f"{prefix}_{name}", default)

    return {
        "url": env("URL").rstrip("/"),
        "token": env("PAT") or env("PERSONAL_TOKEN") or env("TOKEN"),
        "username": env("USERNAME"),
        "api_token": env("API_TOKEN"),
        "read_only": os.getenv("ATLASSIAN_READ_ONLY", "false").lower() in ("true", "1", "yes"),
        "timeout": int(env("TIMEOUT", "30")),
        "ssl_verify": env("SSL_VERIFY", "true").lower() not in ("false", "0", "no"),
    }


@dataclass
class AtlassianConfig:
    """Connection settings for one Atlassian product.

    Supports two authentication modes, read from ``<PREFIX>_*`` variables:
    - Basic auth: ``<PREFIX>_USERNAME`` + ``<PREFIX>_API_TOKEN`` (Cloud) — takes precedence
    - Bearer token: ``<PREFIX>_PAT`` or ``<PREFIX>_PERSONAL_TOKEN`` (Data Center / self-hosted)
    """

    _prefix: ClassVar[str] = ""

    url: str = ""
    token: str = ""
    username: str = ""
    api_token: str = ""
    read_only: bool = False
    timeout: int = 30
    ssl_verify: bool = True

    @classmethod
    def from_env(cls):
        return cls(**_config_for(cls._prefix))

    @property
    def is_configured(self) -> bool:
        has_bearer = bool(self.url and self.token)
        has_basic = bool(self.url and self.username and self.api_token)
        return has_bearer or has_basic

    @property
    def is_cloud(self) -> bool:
        """True when configured for Atlassian Cloud.

        Decided by the URL host: Cloud lives on ``*.atlassian.net`` (or
        ``api.atlassian.com``). The auth mode is NOT a reliable signal — Data
        Center/Server also accepts basic auth (username + password or API token),
        so keying off basic auth would misroute a DC instance as Cloud. Only when
        the URL has no host (misconfigured) do we fall back to the auth signal.
        """
        host = (urlparse(self.url).hostname or "").lower()
        if host:
            return host == "api.atlassian.com" or host.endswith(".atlassian.net")
        return bool(self.username and self.api_token)

    @property
    def auth_header(self) -> dict[str, str]:
        """Return the Authorization header — Basic (Cloud) wins over Bearer."""
        return _auth_header(self.token, self.username, self.api_token)


class JiraConfig(AtlassianConfig):
    """Jira connection configuration: ``JIRA_URL`` plus ``JIRA_*`` credentials."""

    _prefix = "JIRA"


class ConfluenceConfig(AtlassianConfig):
    """Confluence connection configuration: ``CONFLUENCE_URL`` plus ``CONFLUENCE_*`` credentials."""

    _prefix = "CONFLUENCE"
