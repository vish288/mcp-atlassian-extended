"""MCP prompts — multi-tool workflow templates for Jira/Confluence operations."""

from __future__ import annotations

from pathlib import Path
from string import Template

from fastmcp.prompts.prompt import Message

from . import mcp
from ._helpers import (
    _load_file,
    _parse_jira_board_url,
    _parse_jira_issue_url,
    _parse_jira_project_url,
)

_PROMPTS_DIR = str(Path(__file__).resolve().parent.parent / "resources" / "prompts")


def _load_prompt(filename: str) -> str:
    """Load a prompt markdown file from the prompts directory."""
    return _load_file(_PROMPTS_DIR, filename)


def _render(filename: str, **kwargs: str) -> str:
    """Load a prompt template and substitute variables safely.

    Uses string.Template ($var) instead of str.format({var}) to avoid
    KeyError when parameter values contain curly braces.
    """
    return Template(_load_prompt(filename)).safe_substitute(kwargs)


@mcp.prompt(tags={"jira", "create"})
def create_ticket(project_key: str, issue_type: str) -> list[Message]:
    """Create a Jira ticket — gather fields, set custom fields (points, DoD,
    privacy, security), create issue, and add links.

    project_key accepts a full Jira project URL.
    """
    project_key = _parse_jira_project_url(project_key)
    text = _render("create-ticket.md", project_key=project_key, issue_type=issue_type)
    return [
        Message(role="user", content=text),
        Message(
            role="assistant",
            content=(
                f"I'll help create a {issue_type} in {project_key}. "
                "Let me check the available fields first."
            ),
        ),
    ]


@mcp.prompt(tags={"jira", "agile"})
def plan_sprint(board_id: str, sprint_id: str) -> list[Message]:
    """Plan a sprint — review backlog, calculate capacity, suggest scope,
    and move issues into the sprint.

    board_id accepts a full Jira board URL.
    """
    board_id = _parse_jira_board_url(board_id)
    text = _render("plan-sprint.md", board_id=board_id, sprint_id=sprint_id)
    return [
        Message(role="user", content=text),
        Message(
            role="assistant",
            content=(
                f"I'll help plan sprint {sprint_id} on board {board_id}. "
                "Let me check the sprint details and team capacity."
            ),
        ),
    ]


@mcp.prompt(tags={"jira", "workflow"})
def close_ticket(issue_key: str) -> list[Message]:
    """Close a Jira ticket — verify DoD, check linked MRs, transition
    statuses, and add closing comment.

    issue_key accepts a full Jira browse URL (e.g. https://jira.example.com/browse/PROJ-123).
    """
    issue_key = _parse_jira_issue_url(issue_key)
    text = _render("close-ticket.md", issue_key=issue_key)
    return [
        Message(role="user", content=text),
        Message(
            role="assistant",
            content=(
                f"I'll help close {issue_key}. "
                "Let me fetch the issue details and check the Definition of Done."
            ),
        ),
    ]


@mcp.prompt(tags={"confluence", "capacity"})
def team_availability(team_members: str, start_date: str, end_date: str) -> list[Message]:
    """Check team availability — get time-off, calculate capacity,
    and flag scheduling conflicts."""
    text = _render(
        "team-availability.md",
        team_members=team_members,
        start_date=start_date,
        end_date=end_date,
    )
    return [
        Message(role="user", content=text),
        Message(
            role="assistant",
            content=(
                f"I'll check team availability from {start_date} to {end_date}. "
                "Let me look up who is out during that period."
            ),
        ),
    ]


@mcp.prompt(tags={"jira", "attachments"})
def manage_attachments(issue_key: str) -> list[Message]:
    """Manage issue attachments — list, identify stale/duplicates,
    upload/download, and clean up.

    issue_key accepts a full Jira browse URL (e.g. https://jira.example.com/browse/PROJ-123).
    """
    issue_key = _parse_jira_issue_url(issue_key)
    text = _render("manage-attachments.md", issue_key=issue_key)
    return [
        Message(role="user", content=text),
        Message(
            role="assistant",
            content=(
                f"I'll help manage attachments for {issue_key}. "
                "Let me list the current attachments first."
            ),
        ),
    ]


# ════════════════════════════════════════════════════════════════════
# Startup validation
# ════════════════════════════════════════════════════════════════════

_PROMPT_FILES = [
    "create-ticket.md",
    "plan-sprint.md",
    "close-ticket.md",
    "team-availability.md",
    "manage-attachments.md",
]


def _validate_prompts() -> None:
    """Verify all expected prompt files exist at import time."""
    _dir = Path(_PROMPTS_DIR)
    missing = [f for f in _PROMPT_FILES if not (_dir / f).is_file()]
    if missing:
        msg = f"Missing prompt files (packaging error): {missing}"
        raise RuntimeError(msg)


_validate_prompts()
