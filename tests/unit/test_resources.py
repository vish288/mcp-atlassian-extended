"""Tests for MCP resource registration and content."""

from __future__ import annotations

from mcp_atlassian_extended.servers.resources import (
    _RESOURCES_DIR,
    _load,
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
        "file": "jira-hierarchy.md",
    },
    "resource://rules/jira-ticket-writing": {
        "fn": jira_ticket_writing_rules,
        "file": "jira-ticket-writing.md",
    },
    "resource://rules/acceptance-criteria": {
        "fn": acceptance_criteria_rules,
        "file": "acceptance-criteria.md",
    },
    "resource://rules/sprint-hygiene": {
        "fn": sprint_hygiene_rules,
        "file": "sprint-hygiene.md",
    },
    "resource://rules/jira-workflow": {
        "fn": jira_workflow_rules,
        "file": "jira-workflow.md",
    },
    "resource://rules/issue-linking": {
        "fn": issue_linking_rules,
        "file": "issue-linking.md",
    },
    "resource://guides/story-points": {
        "fn": story_points_guide,
        "file": "story-points.md",
    },
    "resource://guides/definition-of-done": {
        "fn": definition_of_done_guide,
        "file": "definition-of-done.md",
    },
    "resource://guides/jira-labels": {
        "fn": jira_labels_guide,
        "file": "jira-labels.md",
    },
    "resource://guides/jql-library": {
        "fn": jql_library_guide,
        "file": "jql-library.md",
    },
    "resource://guides/custom-fields": {
        "fn": custom_fields_guide,
        "file": "custom-fields.md",
    },
    "resource://guides/confluence-spaces": {
        "fn": confluence_spaces_guide,
        "file": "confluence-spaces.md",
    },
    "resource://guides/agile-ceremonies": {
        "fn": agile_ceremonies_guide,
        "file": "agile-ceremonies.md",
    },
    "resource://guides/git-jira-integration": {
        "fn": git_jira_integration_guide,
        "file": "git-jira-integration.md",
    },
    "resource://templates/confluence-pages": {
        "fn": confluence_page_templates,
        "file": "confluence-pages.md",
    },
}

RESOURCE_FILES = [info["file"] for info in EXPECTED_RESOURCES.values()]


class TestResourceFiles:
    """Verify resource .md files exist and are valid."""

    def test_resources_dir_exists(self) -> None:
        assert _RESOURCES_DIR.is_dir(), f"Resources directory missing: {_RESOURCES_DIR}"

    def test_all_files_exist(self) -> None:
        for filename in RESOURCE_FILES:
            path = _RESOURCES_DIR / filename
            assert path.is_file(), f"Missing resource file: {path}"

    def test_load_returns_content(self) -> None:
        for filename in RESOURCE_FILES:
            content = _load(filename)
            assert len(content) > 100, f"{filename} too short ({len(content)} chars)"

    def test_content_starts_with_heading(self) -> None:
        for filename in RESOURCE_FILES:
            content = _load(filename)
            assert content.lstrip().startswith("#"), (
                f"{filename} should start with markdown heading"
            )

    def test_no_python_escape_artifacts(self) -> None:
        """Ensure extracted .md files don't contain Python string artifacts."""
        for filename in RESOURCE_FILES:
            content = _load(filename)
            assert '"""' not in content, f"{filename} contains triple-quote artifact"


class TestResourceRegistration:
    """Verify resources are importable and return content."""

    def test_resource_count(self) -> None:
        """All 15 resources are defined."""
        assert len(EXPECTED_RESOURCES) == 15

    def test_each_resource_returns_file_content(self) -> None:
        """Each resource function returns its file content."""
        for uri, info in EXPECTED_RESOURCES.items():
            result = info["fn"]()
            expected = _load(info["file"])
            assert result == expected, f"{uri} content mismatch"

    def test_resource_uris_are_unique(self) -> None:
        """No duplicate URIs."""
        uris = list(EXPECTED_RESOURCES.keys())
        assert len(uris) == len(set(uris))

    def test_resource_functions_have_metadata(self) -> None:
        """Each function has the __fastmcp__ attribute from the decorator."""
        for uri, info in EXPECTED_RESOURCES.items():
            fn = info["fn"]
            assert hasattr(fn, "__fastmcp__"), f"{uri} function missing __fastmcp__ metadata"
