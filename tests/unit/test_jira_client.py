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

    async def test_list_projects(self):
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/api/2/project").mock(
                return_value=httpx.Response(200, json=[{"key": "PROJ", "name": "Project"}])
            )
            client = _make_client()
            result = await client.list_projects()
            assert result[0]["key"] == "PROJ"

    async def test_get_board(self):
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/agile/1.0/board/42").mock(
                return_value=httpx.Response(200, json={"id": 42, "name": "Sprint Board"})
            )
            client = _make_client()
            result = await client.get_board(42)
            assert result["id"] == 42

    async def test_auth_error(self):
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/api/2/project").mock(
                return_value=httpx.Response(401, text="Unauthorized")
            )
            client = _make_client()
            with pytest.raises(AtlassianAuthError):
                await client.list_projects()

    async def test_delete_attachment(self):
        async with respx.mock(base_url=BASE) as router:
            router.delete("/rest/api/2/attachment/123").mock(return_value=httpx.Response(204))
            client = _make_client()
            result = await client.delete_attachment("123")
            assert result is None

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

    @pytest.mark.parametrize(
        "url",
        [
            # Same host, downgraded to cleartext.
            "http://jira.example.com/rest/api/2/attachment/content/123",
            # Same host and scheme, different port.
            "https://jira.example.com:9999/rest/api/2/attachment/content/123",
            # Both.
            "http://jira.example.com:9999/rest/api/2/attachment/content/123",
        ],
    )
    def test_rejects_same_host_different_origin(self, url):
        """The request that follows carries the Bearer token.

        Comparing hostname alone let a cleartext downgrade, or another port on
        the same host, through -- leaking the credential the check protects.
        """
        client = _make_client()
        with pytest.raises(ValueError, match="doesn't match"):
            client._validate_download_url(url)

    def test_accepts_explicit_default_port(self):
        """https://host and https://host:443 are the same origin."""
        client = _make_client()
        url = "https://jira.example.com:443/rest/api/2/attachment/content/123"
        assert client._validate_download_url(url) == url

    @pytest.mark.parametrize(
        "url",
        [
            # AT-R02: an upper/mixed-case scheme skipped the check entirely before.
            "HTTPS://evil.example.net/x",
            "HtTp://evil.example.net/x",
            # Scheme-relative: a netloc with no scheme is still off-origin.
            "//evil.example.net/x",
        ],
    )
    def test_rejects_case_and_scheme_relative(self, url):
        """A case-insensitive, urlparse-based origin check — not startswith."""
        client = _make_client()
        with pytest.raises(ValueError, match="doesn't match"):
            client._validate_download_url(url)

    def test_accepts_uppercase_scheme_same_origin(self):
        """Normalisation lowercases the scheme before comparing."""
        client = _make_client()
        url = "HTTPS://jira.example.com/rest/api/2/attachment/content/123"
        assert client._validate_download_url(url) == url


class TestVersions:
    async def test_get_project_versions(self):
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/api/2/project/PROJ/versions").mock(
                return_value=httpx.Response(
                    200, json=[{"id": "100", "name": "v1.0.0", "released": True}]
                )
            )
            client = _make_client()
            result = await client.get_project_versions("PROJ")
            assert len(result) == 1
            assert result[0]["name"] == "v1.0.0"

    async def test_create_version(self):
        async with respx.mock(base_url=BASE) as router:
            router.post("/rest/api/2/version").mock(
                return_value=httpx.Response(
                    201, json={"id": "200", "name": "v2.0.0", "project": "PROJ"}
                )
            )
            client = _make_client()
            result = await client.create_version(
                "PROJ", "v2.0.0", description="New release", release_date="2026-03-04"
            )
            assert result["id"] == "200"
            assert result["name"] == "v2.0.0"

    async def test_create_version_minimal(self):
        async with respx.mock(base_url=BASE) as router:
            router.post("/rest/api/2/version").mock(
                return_value=httpx.Response(
                    201, json={"id": "201", "name": "v3.0.0", "project": "PROJ"}
                )
            )
            client = _make_client()
            result = await client.create_version("PROJ", "v3.0.0")
            assert result["name"] == "v3.0.0"

    async def test_update_version(self):
        async with respx.mock(base_url=BASE) as router:
            router.put("/rest/api/2/version/200").mock(
                return_value=httpx.Response(
                    200, json={"id": "200", "name": "v2.0.0", "released": True}
                )
            )
            client = _make_client()
            result = await client.update_version("200", released=True)
            assert result["released"] is True


class TestPathInjection:
    """AT-R01: caller-supplied ids/keys must not inject extra path segments.

    httpx normalises ``..`` but not ``%2F``; without ``quote(safe="")`` a value
    like ``../issue/PROJ-1`` in an attachment id turns a DELETE-attachment into a
    DELETE-issue.
    """

    async def test_delete_attachment_escapes_segment(self):
        async with respx.mock(base_url=BASE) as router:
            route = router.route(method="DELETE").mock(return_value=httpx.Response(204))
            client = _make_client()
            await client.delete_attachment("../issue/PROJ-1")
            raw = route.calls.last.request.url.raw_path
            assert b"attachment/..%2Fissue%2FPROJ-1" in raw
            assert b"/rest/api/2/issue/PROJ-1" not in raw

    async def test_update_version_escapes_segment(self):
        async with respx.mock(base_url=BASE) as router:
            route = router.route(method="PUT").mock(return_value=httpx.Response(200, json={}))
            client = _make_client()
            await client.update_version("1/../../issue/PROJ-1", name="x")
            raw = route.calls.last.request.url.raw_path
            assert b"/rest/api/2/version/" in raw
            assert b"%2F" in raw


class TestDownloadRedirect:
    """AT-R03: Jira Cloud 303-redirects attachment content to a media host the
    client cannot follow; ``redirect=false`` makes it return the bytes inline."""

    async def test_absolute_url_sends_redirect_false(self):
        async with respx.mock(base_url=BASE) as router:
            route = router.get("/rest/api/2/attachment/content/9").mock(
                return_value=httpx.Response(200, content=b"bytes")
            )
            client = _make_client()
            await client.download_attachment(f"{BASE}/rest/api/2/attachment/content/9")
            assert route.calls.last.request.url.params.get("redirect") == "false"

    async def test_relative_url_sends_redirect_false(self):
        async with respx.mock(base_url=BASE) as router:
            route = router.get("/rest/api/2/attachment/content/9").mock(
                return_value=httpx.Response(200, content=b"bytes")
            )
            client = _make_client()
            await client.download_attachment("/rest/api/2/attachment/content/9")
            assert route.calls.last.request.url.params.get("redirect") == "false"


class TestUserSearchParam:
    """AT-R04: Cloud removed ``username`` (GDPR) and needs ``query``; Server/DC
    still takes ``username``. Deployment is decided by the URL host, not the auth
    mode — DC also supports basic auth, so basic auth alone must not mean Cloud.
    """

    async def _params(self, config: JiraConfig) -> httpx.QueryParams:
        async with respx.mock() as router:
            route = router.get(url__regex=r".*/rest/api/2/user/search").mock(
                return_value=httpx.Response(200, json=[])
            )
            client = JiraExtendedClient(config)
            await client.search_users("ali")
            return route.calls.last.request.url.params

    async def test_cloud_host_uses_query(self):
        params = await self._params(
            JiraConfig(url="https://acme.atlassian.net", username="me@acme.com", api_token="tok")
        )
        assert params.get("query") == "ali"
        assert "username" not in params

    async def test_server_bearer_uses_username(self):
        params = await self._params(JiraConfig(url=BASE, token="test-token"))
        assert params.get("username") == "ali"
        assert "query" not in params

    async def test_dc_basic_auth_uses_username(self):
        """Data Center on basic auth (non-atlassian.net host) is NOT Cloud."""
        params = await self._params(JiraConfig(url=BASE, username="svc", api_token="tok"))
        assert params.get("username") == "ali"
        assert "query" not in params


class TestContentType:
    """A client-level Content-Type would override httpx's per-request value."""

    async def test_upload_sends_multipart(self, tmp_path):
        f = tmp_path / "note.txt"
        f.write_text("hello")
        async with respx.mock(base_url=BASE) as router:
            route = router.post("/rest/api/2/issue/PROJ-123/attachments").mock(
                return_value=httpx.Response(200, json=[{"id": "9", "filename": "note.txt"}])
            )
            client = _make_client()
            await client.upload_attachment("PROJ-123", str(f))
            sent = route.calls.last.request
            content_type = sent.headers["content-type"]
            assert content_type.startswith("multipart/form-data")
            assert "boundary=" in content_type
            assert sent.headers["x-atlassian-token"] == "no-check"

    async def test_json_request_still_sends_json(self):
        async with respx.mock(base_url=BASE) as router:
            route = router.post("/rest/api/2/issue").mock(
                return_value=httpx.Response(201, json={"key": "PROJ-1"})
            )
            client = _make_client()
            await client.create_issue("PROJ", "Summary")
            assert route.calls.last.request.headers["content-type"] == "application/json"
