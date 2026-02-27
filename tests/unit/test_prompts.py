"""Tests for MCP prompt registration and content."""

from __future__ import annotations

from pathlib import Path

import pytest

from mcp_atlassian_extended.servers.prompts import (
    _PROMPTS_DIR,
    _load_prompt,
    close_ticket,
    create_ticket,
    manage_attachments,
    plan_sprint,
    team_availability,
)

EXPECTED_PROMPTS = {
    "create_ticket": {
        "fn": create_ticket,
        "file": "create-ticket.md",
        "args": {"project_key": "PROJ", "issue_type": "Story"},
    },
    "plan_sprint": {
        "fn": plan_sprint,
        "file": "plan-sprint.md",
        "args": {"board_id": "10", "sprint_id": "50"},
    },
    "close_ticket": {
        "fn": close_ticket,
        "file": "close-ticket.md",
        "args": {"issue_key": "PROJ-100"},
    },
    "team_availability": {
        "fn": team_availability,
        "file": "team-availability.md",
        "args": {
            "team_members": "Alice, Bob, Carol",
            "start_date": "2026-03-01",
            "end_date": "2026-03-14",
        },
    },
    "manage_attachments": {
        "fn": manage_attachments,
        "file": "manage-attachments.md",
        "args": {"issue_key": "PROJ-200"},
    },
}

PROMPT_FILES = [info["file"] for info in EXPECTED_PROMPTS.values()]


class TestPromptFiles:
    """Verify prompt .md files exist and are valid."""

    def test_prompts_dir_exists(self) -> None:
        assert Path(_PROMPTS_DIR).is_dir(), f"Prompts directory missing: {_PROMPTS_DIR}"

    def test_all_files_exist(self) -> None:
        for filename in PROMPT_FILES:
            path = Path(_PROMPTS_DIR) / filename
            assert path.is_file(), f"Missing prompt file: {path}"

    def test_load_returns_content(self) -> None:
        for filename in PROMPT_FILES:
            content = _load_prompt(filename)
            assert len(content) > 100, f"{filename} too short ({len(content)} chars)"

    def test_content_starts_with_heading(self) -> None:
        for filename in PROMPT_FILES:
            content = _load_prompt(filename)
            assert content.lstrip().startswith("#"), (
                f"{filename} should start with markdown heading"
            )

    def test_no_python_escape_artifacts(self) -> None:
        """Ensure .md files don't contain Python string artifacts."""
        for filename in PROMPT_FILES:
            content = _load_prompt(filename)
            assert '"""' not in content, f"{filename} contains triple-quote artifact"


class TestLoadPromptSecurity:
    """Verify _load_prompt() rejects path traversal attempts."""

    def test_rejects_directory_traversal(self) -> None:
        with pytest.raises(ValueError, match="Invalid filename"):
            _load_prompt("../../../etc/passwd")

    def test_rejects_forward_slash(self) -> None:
        with pytest.raises(ValueError, match="Invalid filename"):
            _load_prompt("subdir/file.md")

    def test_rejects_backslash(self) -> None:
        with pytest.raises(ValueError, match="Invalid filename"):
            _load_prompt("subdir\\file.md")

    def test_rejects_dotdot_only(self) -> None:
        with pytest.raises(ValueError, match="Invalid filename"):
            _load_prompt("..")


class TestPromptRegistration:
    """Verify prompts are registered and return valid messages."""

    def test_prompt_count(self) -> None:
        assert len(EXPECTED_PROMPTS) == 5

    def test_each_prompt_returns_messages(self) -> None:
        for name, info in EXPECTED_PROMPTS.items():
            result = info["fn"](**info["args"])
            assert isinstance(result, list), f"{name} should return a list"
            assert len(result) == 2, f"{name} should return 2 messages"

    def test_first_message_is_user_role(self) -> None:
        for name, info in EXPECTED_PROMPTS.items():
            result = info["fn"](**info["args"])
            assert result[0].role == "user", f"{name} first message should be user role"

    def test_second_message_is_assistant_role(self) -> None:
        for name, info in EXPECTED_PROMPTS.items():
            result = info["fn"](**info["args"])
            assert result[1].role == "assistant", f"{name} second message should be assistant role"

    def test_args_are_interpolated(self) -> None:
        result = create_ticket(project_key="DEMO", issue_type="Bug")
        assert "DEMO" in result[0].content.text
        assert "Bug" in result[0].content.text

    def test_close_ticket_interpolation(self) -> None:
        result = close_ticket(issue_key="TEST-99")
        assert "TEST-99" in result[0].content.text
        assert "TEST-99" in result[1].content.text

    def test_team_availability_dates(self) -> None:
        result = team_availability(
            team_members="Alice", start_date="2026-01-01", end_date="2026-01-31"
        )
        assert "2026-01-01" in result[0].content.text
        assert "2026-01-31" in result[0].content.text

    def test_prompt_functions_have_metadata(self) -> None:
        for name, info in EXPECTED_PROMPTS.items():
            fn = info["fn"]
            assert hasattr(fn, "__fastmcp__"), f"{name} function missing __fastmcp__ metadata"

    def test_curly_braces_in_args_do_not_crash(self) -> None:
        """Values containing curly braces must not raise KeyError."""
        result = create_ticket(project_key="PROJ", issue_type='{"nested": "json"}')
        assert '{"nested": "json"}' in result[0].content.text


class TestURLParsing:
    """Verify prompts accept full Jira URLs and extract IDs."""

    def test_close_ticket_from_browse_url(self) -> None:
        result = close_ticket(issue_key="https://jira.example.com/browse/PROJ-123")
        assert "PROJ-123" in result[0].content.text
        assert "PROJ-123" in result[1].content.text

    def test_manage_attachments_from_browse_url(self) -> None:
        result = manage_attachments(issue_key="https://jira.example.com/browse/TEST-456")
        assert "TEST-456" in result[0].content.text

    def test_create_ticket_from_project_url(self) -> None:
        result = create_ticket(
            project_key="https://jira.example.com/jira/software/projects/DEMO/boards/1",
            issue_type="Story",
        )
        assert "DEMO" in result[0].content.text

    def test_plan_sprint_from_board_url(self) -> None:
        result = plan_sprint(
            board_id="https://jira.example.com/jira/software/projects/PROJ/boards/42",
            sprint_id="100",
        )
        assert "42" in result[0].content.text

    def test_plain_keys_still_work(self) -> None:
        result = close_ticket(issue_key="PROJ-99")
        assert "PROJ-99" in result[0].content.text


class TestPromptRendering:
    """Verify prompts render via FastMCP."""

    @pytest.mark.asyncio
    async def test_list_prompts(self) -> None:
        from mcp_atlassian_extended.servers import mcp

        prompts = await mcp.list_prompts()
        prompt_names = {p.name for p in prompts}
        for name in EXPECTED_PROMPTS:
            assert name in prompt_names, f"Prompt {name} not listed"

    @pytest.mark.asyncio
    async def test_render_create_ticket(self) -> None:
        from mcp_atlassian_extended.servers import mcp

        result = await mcp.render_prompt(
            "create_ticket",
            arguments={"project_key": "PROJ", "issue_type": "Story"},
        )
        assert len(result.messages) == 2
        assert "PROJ" in result.messages[0].content.text
