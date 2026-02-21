"""Shared test fixtures for mcp-atlassian-extended."""

from __future__ import annotations

import pytest

from mcp_atlassian_extended.clients.confluence import ConfluenceExtendedClient
from mcp_atlassian_extended.clients.jira import JiraExtendedClient
from mcp_atlassian_extended.config import ConfluenceConfig, JiraConfig


@pytest.fixture
def jira_config() -> JiraConfig:
    return JiraConfig(url="https://jira.example.com", token="test-token")


@pytest.fixture
def confluence_config() -> ConfluenceConfig:
    return ConfluenceConfig(url="https://confluence.example.com", token="test-token")


@pytest.fixture
def jira_client(jira_config: JiraConfig) -> JiraExtendedClient:
    return JiraExtendedClient(jira_config)


@pytest.fixture
def confluence_client(confluence_config: ConfluenceConfig) -> ConfluenceExtendedClient:
    return ConfluenceExtendedClient(confluence_config)
