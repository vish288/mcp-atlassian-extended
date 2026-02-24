"""MCP prompts — multi-tool workflow templates for Jira/Confluence operations."""

from __future__ import annotations

from pathlib import Path

from fastmcp.prompts.prompt import Message

from . import mcp

_PROMPTS_DIR = Path(__file__).resolve().parent.parent / "resources" / "prompts"


def _load_prompt(filename: str) -> str:
    """Load a prompt markdown file from the prompts directory."""
    if "/" in filename or "\\" in filename or ".." in filename:
        msg = f"Invalid prompt filename: {filename}"
        raise ValueError(msg)
    path = _PROMPTS_DIR / filename
    if not path.resolve().is_relative_to(_PROMPTS_DIR.resolve()):
        msg = f"Invalid prompt filename: {filename}"
        raise ValueError(msg)
    return path.read_text(encoding="utf-8")


@mcp.prompt(tags={"jira", "create"})
def create_ticket(project_key: str, issue_type: str) -> list[Message]:
    """Create a Jira ticket — gather fields, set custom fields (points, DoD,
    privacy, security), create issue, and add links."""
    text = _load_prompt("create-ticket.md").format(project_key=project_key, issue_type=issue_type)
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
    and move issues into the sprint."""
    text = _load_prompt("plan-sprint.md").format(board_id=board_id, sprint_id=sprint_id)
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
    statuses, and add closing comment."""
    text = _load_prompt("close-ticket.md").format(issue_key=issue_key)
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
    text = _load_prompt("team-availability.md").format(
        team_members=team_members, start_date=start_date, end_date=end_date
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
    upload/download, and clean up."""
    text = _load_prompt("manage-attachments.md").format(issue_key=issue_key)
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
