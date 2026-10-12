"""Tests for Jira Extended client."""

from __future__ import annotations

import itertools

import httpx
import pytest
import respx

from mcp_atlassian_extended.clients.jira import JiraExtendedClient
from mcp_atlassian_extended.config import JiraConfig
from mcp_atlassian_extended.exceptions import AtlassianApiError, AtlassianAuthError

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
    """Uploads are restricted to one root (ATLASSIAN_UPLOAD_DIR, else cwd).

    Containment is checked against the *resolved* path, so a symlink inside the
    root that points outside it is rejected. Dot components below the root are
    refused. The root itself may be a dot-directory.
    """

    @staticmethod
    def _client(upload_dir: str = "") -> JiraExtendedClient:
        return JiraExtendedClient(JiraConfig(url=BASE, token="t", upload_dir=upload_dir))

    def test_absolute_path_outside_root(self, tmp_path, monkeypatch):
        root = tmp_path / "root"
        root.mkdir()
        outside = tmp_path / "secret.txt"
        outside.write_text("x")
        monkeypatch.chdir(root)
        with pytest.raises(ValueError, match="outside the upload directory"):
            self._client()._validate_file_path(str(outside))

    def test_parent_traversal_outside_root(self, tmp_path, monkeypatch):
        root = tmp_path / "root"
        root.mkdir()
        (tmp_path / "secret.txt").write_text("x")
        monkeypatch.chdir(root)
        with pytest.raises(ValueError, match="outside the upload directory"):
            self._client()._validate_file_path("../secret.txt")

    def test_hidden_dir_component_rejected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        hidden = tmp_path / ".hidden"
        hidden.mkdir()
        (hidden / "x.txt").write_text("x")
        with pytest.raises(ValueError, match="hidden file"):
            self._client()._validate_file_path(str(hidden / "x.txt"))

    def test_dotfile_rejected(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".env").write_text("secret")
        with pytest.raises(ValueError, match="hidden file"):
            self._client()._validate_file_path(".env")

    def test_symlink_inside_pointing_outside(self, tmp_path, monkeypatch):
        root = tmp_path / "root"
        root.mkdir()
        secret = tmp_path / "secret.txt"
        secret.write_text("x")
        (root / "safe.txt").symlink_to(secret)
        monkeypatch.chdir(root)
        with pytest.raises(ValueError, match="outside the upload directory"):
            self._client()._validate_file_path("safe.txt")

    def test_symlink_inside_pointing_dotfile(self, tmp_path, monkeypatch):
        root = tmp_path / "root"
        root.mkdir()
        dotfile = root / ".env"
        dotfile.write_text("x")
        (root / "safe.txt").symlink_to(dotfile)
        monkeypatch.chdir(root)
        with pytest.raises(ValueError, match="hidden file"):
            self._client()._validate_file_path("safe.txt")

    def test_accepts_valid_file_inside_root(self, tmp_path, monkeypatch):
        root = tmp_path / "root"
        root.mkdir()
        valid = root / "doc.txt"
        valid.write_text("content")
        monkeypatch.chdir(root)
        assert self._client()._validate_file_path("doc.txt") == valid.resolve()

    def test_env_dir_wins_over_cwd(self, tmp_path, monkeypatch):
        uploads = tmp_path / "uploads"
        uploads.mkdir()
        cwd = tmp_path / "cwd"
        cwd.mkdir()
        here = cwd / "f.txt"
        here.write_text("x")
        monkeypatch.chdir(cwd)
        with pytest.raises(ValueError, match="outside the upload directory"):
            self._client(str(uploads))._validate_file_path(str(here))

    def test_root_itself_a_dot_dir(self, tmp_path):
        root = tmp_path / ".cache"
        root.mkdir()
        f = root / "plain.txt"
        f.write_text("x")
        assert self._client(str(root))._validate_file_path(str(f)) == f.resolve()

    def test_nonexistent_file_inside_root(self, tmp_path, monkeypatch):
        root = tmp_path / "root"
        root.mkdir()
        monkeypatch.chdir(root)
        with pytest.raises(FileNotFoundError, match="File not found"):
            self._client()._validate_file_path("nope.txt")

    def test_file_over_100mb_rejected(self, tmp_path, monkeypatch):
        """The 100 MB cap is on bytes, not a rounded MB figure. A sparse file
        just over the limit costs no real disk."""
        monkeypatch.chdir(tmp_path)
        big = tmp_path / "big.bin"
        with open(big, "wb") as fh:
            fh.truncate(100 * 1024 * 1024 + 1)
        with pytest.raises(ValueError, match="too large"):
            self._client()._validate_file_path("big.bin")


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

    async def test_303_is_not_followed_off_origin(self):
        """A 303 to a media host must not be followed — the Authorization header
        would leak off-origin. The client never follows redirects, so it surfaces
        the 303 as an error and the media host is never contacted."""
        async with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/rest/api/2/attachment/content/9").mock(
                return_value=httpx.Response(303, headers={"Location": "https://evil.example.net/x"})
            )
            evil = router.get("https://evil.example.net/x").mock(
                return_value=httpx.Response(200, content=b"leaked")
            )
            client = _make_client()
            with pytest.raises(AtlassianApiError) as exc:
                await client.download_attachment(f"{BASE}/rest/api/2/attachment/content/9")
            assert exc.value.status_code == 303
            assert route.called
            assert not evil.called


_CAP = 100 * 1024 * 1024
_MB = 1024 * 1024
_URL9 = f"{BASE}/rest/api/2/attachment/content/9"


class _CountingStream(httpx.AsyncByteStream):
    """Response body that tallies the bytes actually pulled from it.

    ``make_chunks`` is a zero-arg factory returning a fresh iterator of byte
    chunks, so nothing is materialised up front — the download is proven to abort
    before the whole oversized body is produced, not just before it is buffered.
    """

    def __init__(self, make_chunks, counter: list[int]) -> None:
        self._make_chunks = make_chunks
        self._counter = counter

    async def __aiter__(self):
        for chunk in self._make_chunks():
            self._counter[0] += len(chunk)
            yield chunk

    async def aclose(self) -> None:
        pass


def _stream_client(headers: dict[str, str], stream: httpx.AsyncByteStream):
    """A client whose transport streams ``stream`` back for any GET."""
    client = _make_client()
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, headers=headers, stream=stream)
    )
    client._client = httpx.AsyncClient(base_url=BASE, transport=transport)
    return client


class TestDownloadSizeCap:
    """Downloads are streamed and capped at 100 MB — a content URL is
    attacker-influenceable, so an oversized body must never be read whole."""

    async def test_oversized_content_length_rejected_before_read(self):
        """An honest oversized Content-Length is rejected before the body is
        pulled: near-zero bytes consumed, not the declared 150 MB. On the pre-fix
        client (which buffered the whole response first) ``read[0]`` is 150 MB."""
        read = [0]
        stream = _CountingStream(lambda: (b"\0" * _MB for _ in range(150)), read)
        client = _stream_client({"content-length": str(150 * _MB)}, stream)
        with pytest.raises(ValueError, match="too large"):
            await client.download_attachment(_URL9)
        assert read[0] < _CAP

    async def test_oversized_body_without_content_length_aborts_early(self):
        """No Content-Length: streaming aborts once the running total passes the
        cap — ~101 MB read from a 150 MB body, not the whole thing."""
        read = [0]
        stream = _CountingStream(lambda: (b"\0" * _MB for _ in range(150)), read)
        client = _stream_client({}, stream)
        with pytest.raises(ValueError, match="too large"):
            await client.download_attachment(_URL9)
        assert _CAP < read[0] < 150 * _MB

    async def test_exactly_at_cap_accepted(self):
        """Exactly _MAX_ATTACHMENT_BYTES is accepted — the cap is ``>``, not
        ``>=``. Built from a generator, never one >100 MB allocation."""
        read = [0]
        stream = _CountingStream(lambda: (b"\0" * _MB for _ in range(100)), read)
        client = _stream_client({}, stream)
        result = await client.download_attachment(_URL9)
        assert len(result) == _CAP

    async def test_one_byte_over_cap_rejected(self):
        """cap + 1 byte is rejected; the trailing byte tips it over ``>``."""
        read = [0]
        stream = _CountingStream(
            lambda: itertools.chain((b"\0" * _MB for _ in range(100)), [b"\0"]), read
        )
        client = _stream_client({}, stream)
        with pytest.raises(ValueError, match="too large"):
            await client.download_attachment(_URL9)


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

    async def test_upload_sends_multipart(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
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

    async def test_upload_multipart_part_has_filename_and_mime(self, tmp_path, monkeypatch):
        """The multipart part carries the file name and a MIME type from
        MIME_OVERRIDES — a .md uploads as text/markdown, not octet-stream."""
        monkeypatch.chdir(tmp_path)
        f = tmp_path / "note.md"
        f.write_text("# hello")
        async with respx.mock(base_url=BASE) as router:
            route = router.post("/rest/api/2/issue/PROJ-1/attachments").mock(
                return_value=httpx.Response(200, json=[{"id": "9"}])
            )
            client = _make_client()
            await client.upload_attachment("PROJ-1", str(f))
            body = route.calls.last.request.content
            assert b'filename="note.md"' in body
            assert b"Content-Type: text/markdown" in body

    async def test_upload_filename_override_wins(self, tmp_path, monkeypatch):
        """An explicit filename overrides the on-disk name in the multipart part."""
        monkeypatch.chdir(tmp_path)
        f = tmp_path / "note.md"
        f.write_text("# hello")
        async with respx.mock(base_url=BASE) as router:
            route = router.post("/rest/api/2/issue/PROJ-1/attachments").mock(
                return_value=httpx.Response(200, json=[{"id": "9"}])
            )
            client = _make_client()
            await client.upload_attachment("PROJ-1", str(f), filename="renamed.md")
            body = route.calls.last.request.content
            assert b'filename="renamed.md"' in body


class TestAuthorizationOnWire:
    """The Authorization header is actually sent — ``headers = {}`` in the client
    constructor survives every request-shape test that does not assert it."""

    async def test_bearer_sent(self):
        async with respx.mock(base_url=BASE) as router:
            route = router.get("/rest/api/2/project").mock(
                return_value=httpx.Response(200, json=[])
            )
            await JiraExtendedClient(JiraConfig(url=BASE, token="pat-xyz")).list_projects()
            assert route.calls.last.request.headers["authorization"] == "Bearer pat-xyz"

    async def test_basic_sent(self):
        import base64

        async with respx.mock(base_url=BASE) as router:
            route = router.get("/rest/api/2/project").mock(
                return_value=httpx.Response(200, json=[])
            )
            await JiraExtendedClient(
                JiraConfig(url=BASE, username="me@acme.com", api_token="api-tok")
            ).list_projects()
            sent = route.calls.last.request.headers["authorization"]
            assert sent.startswith("Basic ")
            assert base64.b64decode(sent.split(" ", 1)[1]).decode() == "me@acme.com:api-tok"
