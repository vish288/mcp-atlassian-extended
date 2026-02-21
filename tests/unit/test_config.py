"""Tests for Atlassian Extended configuration."""

from __future__ import annotations

import os
from unittest.mock import patch

from mcp_atlassian_extended.config import ConfluenceConfig, JiraConfig


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
