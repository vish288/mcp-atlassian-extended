"""Tests for Jira Extended client."""

from __future__ import annotations

import httpx
import pytest
import respx

from mcp_atlassian_extended.clients.jira import JiraExtendedClient
from mcp_atlassian_extended.config import JiraConfig
from mcp_atlassian_extended.exceptions import AtlassianAuthError

BASE = "https://jira.example.com"


def _make_client() -> JiraExtendedClient:
    return JiraExtendedClient(JiraConfig(url=BASE, token="test-token"))


class TestJiraClient:
    @pytest.mark.asyncio
    async def test_get_attachments(self):
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/api/2/issue/PROJ-123").mock(
                return_value=httpx.Response(
                    200, json={"fields": {"attachment": [{"id": "1", "filename": "test.txt"}]}}
                )
            )
            client = _make_client()
            result = await client.get_attachments("PROJ-123")
            assert len(result) == 1
            assert result[0]["filename"] == "test.txt"

    @pytest.mark.asyncio
    async def test_search_users(self):
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/api/2/user/search").mock(
                return_value=httpx.Response(
                    200, json=[{"displayName": "John Doe", "accountId": "abc123"}]
                )
            )
            client = _make_client()
            result = await client.search_users("john")
            assert len(result) == 1
            assert result[0]["displayName"] == "John Doe"

    @pytest.mark.asyncio
    async def test_list_projects(self):
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/api/2/project").mock(
                return_value=httpx.Response(200, json=[{"key": "PROJ", "name": "Project"}])
            )
            client = _make_client()
            result = await client.list_projects()
            assert result[0]["key"] == "PROJ"

    @pytest.mark.asyncio
    async def test_get_board(self):
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/agile/1.0/board/42").mock(
                return_value=httpx.Response(200, json={"id": 42, "name": "Sprint Board"})
            )
            client = _make_client()
            result = await client.get_board(42)
            assert result["id"] == 42

    @pytest.mark.asyncio
    async def test_auth_error(self):
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/api/2/project").mock(
                return_value=httpx.Response(401, text="Unauthorized")
            )
            client = _make_client()
            with pytest.raises(AtlassianAuthError):
                await client.list_projects()

    @pytest.mark.asyncio
    async def test_delete_attachment(self):
        async with respx.mock(base_url=BASE) as router:
            router.delete("/rest/api/2/attachment/123").mock(return_value=httpx.Response(204))
            client = _make_client()
            result = await client.delete_attachment("123")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_sprint(self):
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/agile/1.0/sprint/10").mock(
                return_value=httpx.Response(
                    200, json={"id": 10, "name": "Sprint 5", "state": "active"}
                )
            )
            client = _make_client()
            result = await client.get_sprint(10)
            assert result["state"] == "active"

    @pytest.mark.asyncio
    async def test_move_to_sprint(self):
        async with respx.mock(base_url=BASE) as router:
            router.post("/rest/agile/1.0/sprint/10/issue").mock(return_value=httpx.Response(204))
            client = _make_client()
            result = await client.move_to_sprint(10, ["PROJ-1", "PROJ-2"])
            assert result is None


class TestFilePathValidation:
    """Tests for _validate_file_path static method."""

    def test_rejects_path_traversal(self):
        with pytest.raises(ValueError, match="Path traversal"):
            JiraExtendedClient._validate_file_path("../../../etc/passwd")

    def test_rejects_nonexistent_file(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="File not found"):
            JiraExtendedClient._validate_file_path(str(tmp_path / "nonexistent.txt"))

    def test_rejects_directory(self, tmp_path):
        with pytest.raises(FileNotFoundError, match="File not found"):
            JiraExtendedClient._validate_file_path(str(tmp_path))

    def test_accepts_valid_file(self, tmp_path):
        valid = tmp_path / "valid.txt"
        valid.write_text("content")
        result = JiraExtendedClient._validate_file_path(str(valid))
        assert result == valid.resolve()


class TestDownloadUrlValidation:
    """Tests for _validate_download_url domain check."""

    def test_rejects_mismatched_domain(self):
        client = _make_client()
        with pytest.raises(ValueError, match="doesn't match"):
            client._validate_download_url("https://evil.com/rest/api/2/attachment/content/123")

    def test_accepts_matching_domain(self):
        client = _make_client()
        url = f"{BASE}/rest/api/2/attachment/content/123"
        result = client._validate_download_url(url)
        assert result == url

    def test_accepts_relative_url(self):
        client = _make_client()
        result = client._validate_download_url("/rest/api/2/attachment/content/123")
        assert result == "/rest/api/2/attachment/content/123"
