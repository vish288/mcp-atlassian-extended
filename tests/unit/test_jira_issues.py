"""Tests for Jira issue and link client methods."""

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


class TestJiraIssues:
    @pytest.mark.asyncio
    async def test_create_issue(self):
        async with respx.mock(base_url=BASE) as router:
            router.post("/rest/api/2/issue").mock(
                return_value=httpx.Response(
                    201, json={"id": "10001", "key": "PROJ-1", "self": "https://jira/issue/10001"}
                )
            )
            client = _make_client()
            result = await client.create_issue("PROJ", "Test issue")
            assert result["key"] == "PROJ-1"

    @pytest.mark.asyncio
    async def test_create_issue_with_custom_fields(self):
        async with respx.mock(base_url=BASE) as router:
            route = router.post("/rest/api/2/issue").mock(
                return_value=httpx.Response(201, json={"id": "10002", "key": "PROJ-2"})
            )
            client = _make_client()
            result = await client.create_issue(
                "PROJ",
                "Custom fields test",
                custom_fields={"customfield_10004": 5, "customfield_17220": {"value": "CustomValue"}},
            )
            assert result["key"] == "PROJ-2"
            sent_body = route.calls[0].request.content
            import json

            payload = json.loads(sent_body)
            assert payload["fields"]["customfield_10004"] == 5
            assert payload["fields"]["customfield_17220"] == {"value": "CustomValue"}

    @pytest.mark.asyncio
    async def test_update_issue(self):
        async with respx.mock(base_url=BASE) as router:
            router.put("/rest/api/2/issue/PROJ-1").mock(return_value=httpx.Response(204))
            client = _make_client()
            result = await client.update_issue(
                "PROJ-1", fields={"summary": "Updated"}, custom_fields={"customfield_10004": 8}
            )
            assert result is None

    @pytest.mark.asyncio
    async def test_create_issue_link(self):
        async with respx.mock(base_url=BASE) as router:
            router.post("/rest/api/2/issueLink").mock(return_value=httpx.Response(201))
            client = _make_client()
            result = await client.create_issue_link("Relates", "PROJ-1", "PROJ-2")
            assert result is None

    @pytest.mark.asyncio
    async def test_delete_issue_link(self):
        async with respx.mock(base_url=BASE) as router:
            router.delete("/rest/api/2/issueLink/456").mock(return_value=httpx.Response(204))
            client = _make_client()
            result = await client.delete_issue_link("456")
            assert result is None

    @pytest.mark.asyncio
    async def test_get_issue_links(self):
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/api/2/issue/PROJ-1").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "fields": {
                            "issuelinks": [
                                {
                                    "id": "100",
                                    "type": {"name": "Relates"},
                                    "outwardIssue": {"key": "PROJ-2"},
                                }
                            ]
                        }
                    },
                )
            )
            client = _make_client()
            result = await client.get_issue_links("PROJ-1")
            assert len(result) == 1
            assert result[0]["type"]["name"] == "Relates"

    @pytest.mark.asyncio
    async def test_create_issue_auth_error(self):
        async with respx.mock(base_url=BASE) as router:
            router.post("/rest/api/2/issue").mock(
                return_value=httpx.Response(401, text="Unauthorized")
            )
            client = _make_client()
            with pytest.raises(AtlassianAuthError):
                await client.create_issue("PROJ", "Fail")

    @pytest.mark.asyncio
    async def test_create_issue_link_with_comment(self):
        async with respx.mock(base_url=BASE) as router:
            route = router.post("/rest/api/2/issueLink").mock(return_value=httpx.Response(201))
            client = _make_client()
            await client.create_issue_link(
                "Blocks", "PROJ-1", "PROJ-2", comment="Blocking dependency"
            )
            import json

            payload = json.loads(route.calls[0].request.content)
            assert payload["comment"]["body"] == "Blocking dependency"
