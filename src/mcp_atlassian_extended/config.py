"""Configuration for Atlassian Extended MCP server."""

from __future__ import annotations

import base64
import functools
import logging
import os
from dataclasses import dataclass
from typing import Any, ClassVar
from urllib.parse import urlparse

_log = logging.getLogger(__name__)

# Shared across the mcp-* servers so one deployer-set env var locks any of them
# read-only. The per-server alias (ATLASSIAN_READ_ONLY) stays; either being truthy
# wins and nothing can turn the lock back off at runtime.
_SHARED_READ_ONLY = "MCP_READ_ONLY"
_FALSEY = frozenset({"", "0", "false", "no", "off"})
_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _is_locking(value: str | None) -> bool:
    """Whether a source's value locks read-only.

    Fail closed: a source locks unless it is unset or an explicit falsey value. An
    unrecognised non-empty value (e.g. ``maybe``) locks — a typo must never silently
    leave writes enabled.
    """
    return value is not None and value.strip().lower() not in _FALSEY


def read_only_sources(alias: str) -> list[str]:
    """Env var names (shared first, then the per-server alias) whose value locks read-only."""
    return [name for name in (_SHARED_READ_ONLY, alias) if _is_locking(os.getenv(name))]


@functools.cache
def _resolve(shared: str | None, alias_name: str, alias: str | None) -> bool:
    """Resolve read-only from the raw source values and warn once per process.

    Pure in its arguments, so ``@lru_cache`` makes the warnings fire once per process
    for a given environment — both products resolve the same two sources, so the lock
    is resolved once rather than per product. Any locking source locks the server; a
    falsy value is never an override. One WARNING per ignored falsy source and per
    unrecognised value taken as locking, each naming the source and value.
    """
    pairs = ((_SHARED_READ_ONLY, shared), (alias_name, alias))
    locked = any(_is_locking(raw) for _, raw in pairs)
    for name, raw in pairs:
        if raw is None:
            continue
        normalised = raw.strip().lower()
        if normalised in _FALSEY:
            if locked:
                _log.warning(
                    "read-only is locked on; ignoring %s=%s (a falsy value cannot unlock it)",
                    name,
                    raw,
                )
        elif normalised not in _TRUTHY:
            _log.warning(
                "read-only: locking on unrecognised %s=%s (anything but a falsy value locks)",
                name,
                raw,
            )
    return locked


def _read_only(alias: str) -> bool:
    """Resolve read-only as ``locking(MCP_READ_ONLY) or locking(<alias>)``."""
    # ponytail: process-lifetime cache on env values; fine because resolution is pure
    # and the environment is fixed for a process. Tests monkeypatch distinct values.
    return _resolve(os.getenv(_SHARED_READ_ONLY), alias, os.getenv(alias))


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
        "read_only": _read_only("ATLASSIAN_READ_ONLY"),
        # Unprefixed like ATLASSIAN_READ_ONLY: one upload/download root per server.
        "upload_dir": os.getenv("ATLASSIAN_UPLOAD_DIR", ""),
        "download_dir": os.getenv("ATLASSIAN_DOWNLOAD_DIR", ""),
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
    upload_dir: str = ""
    download_dir: str = ""
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
