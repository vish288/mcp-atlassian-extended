"""Tests for Atlassian Extended configuration."""

from __future__ import annotations

import base64
import os
from unittest.mock import patch

from mcp_atlassian_extended.config import ConfluenceConfig, JiraConfig

URL = "https://jira.example.com"


def test_jira_config_from_env():
    env = {"JIRA_URL": "https://jira.example.com", "JIRA_PAT": "pat-123"}
    with patch.dict(os.environ, env, clear=False):
        config = JiraConfig.from_env()
    assert config.url == "https://jira.example.com"
    assert config.token == "pat-123"
    assert config.is_configured is True


def test_jira_config_not_configured():
    with patch.dict(os.environ, {}, clear=True):
        config = JiraConfig.from_env()
    assert config.is_configured is False


def test_confluence_config_from_env():
    env = {"CONFLUENCE_URL": "https://confluence.example.com/wiki", "CONFLUENCE_PAT": "pat-456"}
    with patch.dict(os.environ, env, clear=False):
        config = ConfluenceConfig.from_env()
    assert config.url == "https://confluence.example.com/wiki"
    assert config.token == "pat-456"
    assert config.is_configured is True


def test_read_only_flag():
    env = {"JIRA_URL": "https://jira.example.com", "JIRA_PAT": "x", "ATLASSIAN_READ_ONLY": "true"}
    with patch.dict(os.environ, env, clear=False):
        config = JiraConfig.from_env()
    assert config.read_only is True


def test_url_strips_trailing_slash():
    env = {"JIRA_URL": "https://jira.example.com/", "JIRA_PAT": "x"}
    with patch.dict(os.environ, env, clear=False):
        config = JiraConfig.from_env()
    assert config.url == "https://jira.example.com"


def _decode_basic(header: dict[str, str]) -> str:
    scheme, _, value = header["Authorization"].partition(" ")
    assert scheme == "Basic"
    return base64.b64decode(value).decode()


class TestAuthHeaderPrecedence:
    """Cloud basic auth wins; Bearer only when the username/API-token pair is incomplete."""

    def test_basic_only(self):
        config = JiraConfig(url=URL, username="a@b.com", api_token="api-tok")
        assert _decode_basic(config.auth_header) == "a@b.com:api-tok"

    def test_bearer_only(self):
        config = JiraConfig(url=URL, token="pat-123")
        assert config.auth_header == {"Authorization": "Bearer pat-123"}

    def test_basic_wins_over_stray_token(self):
        """A stray JIRA_TOKEN must not shadow configured Cloud credentials."""
        config = JiraConfig(url=URL, token="stray-pat", username="a@b.com", api_token="api-tok")
        assert _decode_basic(config.auth_header) == "a@b.com:api-tok"

    def test_bearer_used_when_basic_incomplete(self):
        """Username without an API token is not usable — fall back to Bearer."""
        assert JiraConfig(url=URL, token="pat-123", username="a@b.com").auth_header == {
            "Authorization": "Bearer pat-123"
        }
        assert JiraConfig(url=URL, token="pat-123", api_token="api-tok").auth_header == {
            "Authorization": "Bearer pat-123"
        }

    def test_no_credentials(self):
        assert JiraConfig(url=URL).auth_header == {}

    def test_confluence_basic_wins_over_stray_token(self):
        config = ConfluenceConfig(
            url=URL, token="stray-pat", username="a@b.com", api_token="api-tok"
        )
        assert _decode_basic(config.auth_header) == "a@b.com:api-tok"

    def test_confluence_bearer_only(self):
        config = ConfluenceConfig(url=URL, token="pat-456")
        assert config.auth_header == {"Authorization": "Bearer pat-456"}


class TestIsCloud:
    """Cloud is decided by the URL host, not the auth mode — DC also uses basic auth."""

    def test_atlassian_net_host_is_cloud(self):
        assert JiraConfig(url="https://acme.atlassian.net", token="pat").is_cloud is True

    def test_api_atlassian_com_host_is_cloud(self):
        assert JiraConfig(url="https://api.atlassian.com", token="pat").is_cloud is True

    def test_dc_host_with_basic_auth_is_not_cloud(self):
        """The regression: DC on basic auth must not be treated as Cloud."""
        config = JiraConfig(url="https://jira.example.com", username="svc", api_token="tok")
        assert config.is_cloud is False

    def test_cloud_host_with_basic_auth_is_cloud(self):
        config = JiraConfig(url="https://acme.atlassian.net", username="me", api_token="tok")
        assert config.is_cloud is True

    def test_no_host_falls_back_to_auth_signal(self):
        assert JiraConfig(url="", username="me", api_token="tok").is_cloud is True
        assert JiraConfig(url="", token="pat").is_cloud is False


def test_stray_jira_token_env_does_not_shadow_cloud_basic():
    """End-to-end via from_env: JIRA_TOKEN present alongside Cloud credentials."""
    env = {
        "JIRA_URL": URL,
        "JIRA_TOKEN": "stray-pat",
        "JIRA_USERNAME": "a@b.com",
        "JIRA_API_TOKEN": "api-tok",
    }
    with patch.dict(os.environ, env, clear=True):
        config = JiraConfig.from_env()
    assert config.token == "stray-pat"
    assert _decode_basic(config.auth_header) == "a@b.com:api-tok"
