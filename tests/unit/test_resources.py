"""Tests for MCP resource registration and content."""

from __future__ import annotations

from mcp_atlassian_extended.servers.resources import (
    _ACCEPTANCE_CRITERIA_CONTENT,
    _AGILE_CEREMONIES_CONTENT,
    _CONFLUENCE_PAGES_CONTENT,
    _CONFLUENCE_SPACES_CONTENT,
    _CUSTOM_FIELDS_CONTENT,
    _DEFINITION_OF_DONE_CONTENT,
    _GIT_JIRA_INTEGRATION_CONTENT,
    _ISSUE_LINKING_CONTENT,
    _JIRA_HIERARCHY_CONTENT,
    _JIRA_LABELS_CONTENT,
    _JIRA_TICKET_WRITING_CONTENT,
    _JIRA_WORKFLOW_CONTENT,
    _JQL_LIBRARY_CONTENT,
    _SPRINT_HYGIENE_CONTENT,
    _STORY_POINTS_CONTENT,
    acceptance_criteria_rules,
    agile_ceremonies_guide,
    confluence_page_templates,
    confluence_spaces_guide,
    custom_fields_guide,
    definition_of_done_guide,
    git_jira_integration_guide,
    issue_linking_rules,
    jira_hierarchy_rules,
    jira_labels_guide,
    jira_ticket_writing_rules,
    jira_workflow_rules,
    jql_library_guide,
    sprint_hygiene_rules,
    story_points_guide,
)

EXPECTED_RESOURCES = {
    "resource://rules/jira-hierarchy": {
        "fn": jira_hierarchy_rules,
        "content": _JIRA_HIERARCHY_CONTENT,
    },
    "resource://rules/jira-ticket-writing": {
        "fn": jira_ticket_writing_rules,
        "content": _JIRA_TICKET_WRITING_CONTENT,
    },
    "resource://rules/acceptance-criteria": {
        "fn": acceptance_criteria_rules,
        "content": _ACCEPTANCE_CRITERIA_CONTENT,
    },
    "resource://rules/sprint-hygiene": {
        "fn": sprint_hygiene_rules,
        "content": _SPRINT_HYGIENE_CONTENT,
    },
    "resource://rules/jira-workflow": {
        "fn": jira_workflow_rules,
        "content": _JIRA_WORKFLOW_CONTENT,
    },
    "resource://rules/issue-linking": {
        "fn": issue_linking_rules,
        "content": _ISSUE_LINKING_CONTENT,
    },
    "resource://guides/story-points": {
        "fn": story_points_guide,
        "content": _STORY_POINTS_CONTENT,
    },
    "resource://guides/definition-of-done": {
        "fn": definition_of_done_guide,
        "content": _DEFINITION_OF_DONE_CONTENT,
    },
    "resource://guides/jira-labels": {
        "fn": jira_labels_guide,
        "content": _JIRA_LABELS_CONTENT,
    },
    "resource://guides/jql-library": {
        "fn": jql_library_guide,
        "content": _JQL_LIBRARY_CONTENT,
    },
    "resource://guides/custom-fields": {
        "fn": custom_fields_guide,
        "content": _CUSTOM_FIELDS_CONTENT,
    },
    "resource://guides/confluence-spaces": {
        "fn": confluence_spaces_guide,
        "content": _CONFLUENCE_SPACES_CONTENT,
    },
    "resource://guides/agile-ceremonies": {
        "fn": agile_ceremonies_guide,
        "content": _AGILE_CEREMONIES_CONTENT,
    },
    "resource://guides/git-jira-integration": {
        "fn": git_jira_integration_guide,
        "content": _GIT_JIRA_INTEGRATION_CONTENT,
    },
    "resource://templates/confluence-pages": {
        "fn": confluence_page_templates,
        "content": _CONFLUENCE_PAGES_CONTENT,
    },
}


class TestResourceRegistration:
    """Verify resources are importable and return content."""

    def test_resource_count(self) -> None:
        """All 15 resources are defined."""
        assert len(EXPECTED_RESOURCES) == 15

    def test_each_resource_returns_content(self) -> None:
        """Each resource function returns its content constant."""
        for uri, info in EXPECTED_RESOURCES.items():
            result = info["fn"]()
            assert result == info["content"], f"{uri} content mismatch"

    def test_content_is_non_empty_markdown(self) -> None:
        """Each content constant is non-empty and starts with a markdown heading."""
        for uri, info in EXPECTED_RESOURCES.items():
            content = info["content"]
            assert len(content) > 100, f"{uri} content too short"
            assert content.lstrip().startswith("#"), f"{uri} should start with markdown heading"

    def test_resource_uris_are_unique(self) -> None:
        """No duplicate URIs."""
        uris = list(EXPECTED_RESOURCES.keys())
        assert len(uris) == len(set(uris))

    def test_resource_functions_have_metadata(self) -> None:
        """Each function has the __fastmcp__ attribute from the decorator."""
        for uri, info in EXPECTED_RESOURCES.items():
            fn = info["fn"]
            assert hasattr(fn, "__fastmcp__"), f"{uri} function missing __fastmcp__ metadata"
