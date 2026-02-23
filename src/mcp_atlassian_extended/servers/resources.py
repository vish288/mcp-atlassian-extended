"""MCP resources for Atlassian — curated rules and guides for Jira/Confluence workflows."""

from __future__ import annotations

from pathlib import Path

from . import mcp

_RESOURCES_DIR = Path(__file__).resolve().parent.parent / "resources"


def _load(filename: str) -> str:
    """Load a resource markdown file."""
    return (_RESOURCES_DIR / filename).read_text(encoding="utf-8")


# ════════════════════════════════════════════════════════════════════
# Rules
# ════════════════════════════════════════════════════════════════════


@mcp.resource(
    "resource://rules/jira-hierarchy",
    name="Jira Issue Hierarchy",
    description="Epic → Story → Task → Subtask structure, splitting rules, and type selection",
    mime_type="text/markdown",
    tags={"rule", "jira"},
)
def jira_hierarchy_rules() -> str:
    """Jira issue hierarchy and type definitions."""
    return _load("jira-hierarchy.md")


@mcp.resource(
    "resource://rules/jira-ticket-writing",
    name="Jira Ticket Writing Standards",
    description="Summary format, Story/Bug/Task/Spike description templates, comment policy",
    mime_type="text/markdown",
    tags={"rule", "jira"},
)
def jira_ticket_writing_rules() -> str:
    """Jira ticket writing standards and templates."""
    return _load("jira-ticket-writing.md")


@mcp.resource(
    "resource://rules/acceptance-criteria",
    name="Acceptance Criteria Standards",
    description="Given/When/Then format, rule-oriented criteria, writing rules",
    mime_type="text/markdown",
    tags={"rule", "jira"},
)
def acceptance_criteria_rules() -> str:
    """Acceptance criteria standards and formats."""
    return _load("acceptance-criteria.md")


@mcp.resource(
    "resource://rules/sprint-hygiene",
    name="Sprint Hygiene Rules",
    description="Definition of Ready, WIP limits, carry-over policy, refinement standards",
    mime_type="text/markdown",
    tags={"rule", "jira", "agile"},
)
def sprint_hygiene_rules() -> str:
    """Sprint hygiene rules and practices."""
    return _load("sprint-hygiene.md")


@mcp.resource(
    "resource://rules/jira-workflow",
    name="Jira Workflow & Automation",
    description="Status transitions, automation rule patterns, workflow governance",
    mime_type="text/markdown",
    tags={"rule", "jira"},
)
def jira_workflow_rules() -> str:
    """Jira workflow transitions and automation patterns."""
    return _load("jira-workflow.md")


@mcp.resource(
    "resource://rules/issue-linking",
    name="Issue Linking Best Practices",
    description="Link types, correct usage, cross-team patterns, cleanup",
    mime_type="text/markdown",
    tags={"rule", "jira"},
)
def issue_linking_rules() -> str:
    """Issue linking best practices and cross-team patterns."""
    return _load("issue-linking.md")


# ════════════════════════════════════════════════════════════════════
# Guides
# ════════════════════════════════════════════════════════════════════


@mcp.resource(
    "resource://guides/story-points",
    name="Story Point Estimation",
    description="Fibonacci scale, Planning Poker, relative sizing, velocity",
    mime_type="text/markdown",
    tags={"guide", "jira", "agile"},
)
def story_points_guide() -> str:
    """Story point estimation guide."""
    return _load("story-points.md")


@mcp.resource(
    "resource://guides/definition-of-done",
    name="Definition of Done Checklists",
    description="Story/Bug/Task DoD templates, enforcement rules, governance",
    mime_type="text/markdown",
    tags={"guide", "jira", "agile"},
)
def definition_of_done_guide() -> str:
    """Definition of Done checklists and governance."""
    return _load("definition-of-done.md")


@mcp.resource(
    "resource://guides/jira-labels",
    name="Jira Label Taxonomy",
    description="Standard labels, naming rules, governance, JQL usage",
    mime_type="text/markdown",
    tags={"guide", "jira"},
)
def jira_labels_guide() -> str:
    """Jira label taxonomy and governance."""
    return _load("jira-labels.md")


@mcp.resource(
    "resource://guides/jql-library",
    name="JQL Query Library",
    description="15 query patterns for sprint management, blockers, stale tickets, reporting",
    mime_type="text/markdown",
    tags={"guide", "jira"},
)
def jql_library_guide() -> str:
    """JQL query library with reusable patterns."""
    return _load("jql-library.md")


@mcp.resource(
    "resource://guides/custom-fields",
    name="Jira Custom Field Governance",
    description="Creation process, naming conventions, field contexts, audit",
    mime_type="text/markdown",
    tags={"guide", "jira"},
)
def custom_fields_guide() -> str:
    """Jira custom field governance guide."""
    return _load("custom-fields.md")


@mcp.resource(
    "resource://guides/confluence-spaces",
    name="Confluence Space Organization",
    description="Space taxonomy, page hierarchy, naming conventions, maintenance",
    mime_type="text/markdown",
    tags={"guide", "confluence"},
)
def confluence_spaces_guide() -> str:
    """Confluence space organization guide."""
    return _load("confluence-spaces.md")


@mcp.resource(
    "resource://guides/agile-ceremonies",
    name="Agile Ceremony Standards",
    description="Sprint planning, standup, review, retrospective formats and rules",
    mime_type="text/markdown",
    tags={"guide", "jira", "agile"},
)
def agile_ceremonies_guide() -> str:
    """Agile ceremony standards and formats."""
    return _load("agile-ceremonies.md")


@mcp.resource(
    "resource://guides/git-jira-integration",
    name="Git-Jira Integration Patterns",
    description="Branch naming for auto-linking, smart commits, automation rules, macros",
    mime_type="text/markdown",
    tags={"guide", "jira", "git"},
)
def git_jira_integration_guide() -> str:
    """Git-Jira integration patterns."""
    return _load("git-jira-integration.md")


# ════════════════════════════════════════════════════════════════════
# Templates
# ════════════════════════════════════════════════════════════════════


@mcp.resource(
    "resource://templates/confluence-pages",
    name="Confluence Page Templates",
    description="ADR, RFC, Runbook, Retrospective, DACI, and Meeting Notes templates",
    mime_type="text/markdown",
    tags={"template", "confluence"},
)
def confluence_page_templates() -> str:
    """Confluence page templates in wiki markup."""
    return _load("confluence-pages.md")
