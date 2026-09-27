"""MCP resources for Atlassian — curated rules and guides for Jira/Confluence workflows.

Every resource is a markdown file under ``resources/``; the table below is the
single place that names them. Adding one means adding the ``.md`` and one row.
"""

from __future__ import annotations

import functools
from pathlib import Path
from typing import NamedTuple

from . import mcp
from ._helpers import _load_file

_RESOURCES_DIR = str(Path(__file__).resolve().parent.parent / "resources")


def _load(filename: str) -> str:
    """Load a resource markdown file."""
    return _load_file(_RESOURCES_DIR, filename)


class Resource(NamedTuple):
    uri: str
    name: str
    description: str
    tags: set[str]
    file: str


RESOURCES = [
    # ── Rules ──
    Resource(
        "resource://rules/jira-hierarchy",
        "Jira Issue Hierarchy",
        "Epic → Story → Task → Subtask structure, splitting rules, and type selection",
        {"rule", "jira"},
        "jira-hierarchy.md",
    ),
    Resource(
        "resource://rules/jira-ticket-writing",
        "Jira Ticket Writing Standards",
        "Summary format, Story/Bug/Task/Spike description templates, comment policy",
        {"rule", "jira"},
        "jira-ticket-writing.md",
    ),
    Resource(
        "resource://rules/acceptance-criteria",
        "Acceptance Criteria Standards",
        "Given/When/Then format, rule-oriented criteria, writing rules",
        {"rule", "jira"},
        "acceptance-criteria.md",
    ),
    Resource(
        "resource://rules/sprint-hygiene",
        "Sprint Hygiene Rules",
        "Definition of Ready, WIP limits, carry-over policy, refinement standards",
        {"rule", "jira", "agile"},
        "sprint-hygiene.md",
    ),
    Resource(
        "resource://rules/jira-workflow",
        "Jira Workflow & Automation",
        "Status transitions, automation rule patterns, workflow governance",
        {"rule", "jira"},
        "jira-workflow.md",
    ),
    Resource(
        "resource://rules/issue-linking",
        "Issue Linking Best Practices",
        "Link types, correct usage, cross-team patterns, cleanup",
        {"rule", "jira"},
        "issue-linking.md",
    ),
    # ── Guides ──
    Resource(
        "resource://guides/story-points",
        "Story Point Estimation",
        "Fibonacci scale, Planning Poker, relative sizing, velocity",
        {"guide", "jira", "agile"},
        "story-points.md",
    ),
    Resource(
        "resource://guides/definition-of-done",
        "Definition of Done Checklists",
        "Story/Bug/Task DoD templates, enforcement rules, governance",
        {"guide", "jira", "agile"},
        "definition-of-done.md",
    ),
    Resource(
        "resource://guides/jira-labels",
        "Jira Label Taxonomy",
        "Standard labels, naming rules, governance, JQL usage",
        {"guide", "jira"},
        "jira-labels.md",
    ),
    Resource(
        "resource://guides/jql-library",
        "JQL Query Library",
        "15 query patterns for sprint management, blockers, stale tickets, reporting",
        {"guide", "jira"},
        "jql-library.md",
    ),
    Resource(
        "resource://guides/custom-fields",
        "Jira Custom Field Governance",
        "Creation process, naming conventions, field contexts, audit",
        {"guide", "jira"},
        "custom-fields.md",
    ),
    Resource(
        "resource://guides/confluence-spaces",
        "Confluence Space Organization",
        "Space taxonomy, page hierarchy, naming conventions, maintenance",
        {"guide", "confluence"},
        "confluence-spaces.md",
    ),
    Resource(
        "resource://guides/agile-ceremonies",
        "Agile Ceremony Standards",
        "Sprint planning, standup, review, retrospective formats and rules",
        {"guide", "jira", "agile"},
        "agile-ceremonies.md",
    ),
    Resource(
        "resource://guides/git-jira-integration",
        "Git-Jira Integration Patterns",
        "Branch naming for auto-linking, smart commits, automation rules, macros",
        {"guide", "jira", "git"},
        "git-jira-integration.md",
    ),
    # ── Templates ──
    Resource(
        "resource://templates/confluence-pages",
        "Confluence Page Templates",
        "ADR, RFC, Runbook, Retrospective, DACI, and Meeting Notes templates",
        {"template", "confluence"},
        "confluence-pages.md",
    ),
]

for _r in RESOURCES:
    mcp.resource(
        _r.uri, name=_r.name, description=_r.description, mime_type="text/markdown", tags=_r.tags
    )(functools.partial(_load, _r.file))


def _validate_resources() -> None:
    """Verify every resource file exists at import time."""
    _dir = Path(_RESOURCES_DIR)
    missing = [r.file for r in RESOURCES if not (_dir / r.file).is_file()]
    if missing:
        msg = f"Missing resource files (packaging error): {missing}"
        raise RuntimeError(msg)


_validate_resources()
