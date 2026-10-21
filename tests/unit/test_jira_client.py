"""Tests for Jira Extended client."""

from __future__ import annotations

import asyncio
import itertools
import ssl
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime

import httpx
import pytest
import respx

from mcp_atlassian_extended.clients import _http
from mcp_atlassian_extended.clients.confluence import ConfluenceExtendedClient
from mcp_atlassian_extended.clients.jira import JiraExtendedClient
from mcp_atlassian_extended.config import ConfluenceConfig, JiraConfig
from mcp_atlassian_extended.exceptions import (
    AtlassianApiError,
    AtlassianAuthError,
    AtlassianConnectionError,
    AtlassianRateLimitError,
    AtlassianTimeoutError,
)

BASE = "https://jira.example.com"
CONFLUENCE_BASE = "https://confluence.example.com"


def _make_client() -> JiraExtendedClient:
    return JiraExtendedClient(JiraConfig(url=BASE, token="test-token"))


class TestJiraClient:
    """Client-level failure that is not pinned by the contract table.

    The passthrough happy paths (get_attachments, search_users, list_projects,
    get_board, get_sprint, move_to_sprint, delete_attachment) are each a row in
    ``test_tool_contract.py`` — which pins the wire shape and the response
    mapping through the real server — so they were removed here. The 401 → auth
    error below is kept because it exercises the client's own error mapping
    (``_raise_for_atlassian``) directly, independent of any tool.
    """

    async def test_auth_error(self):
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/api/2/project").mock(
                return_value=httpx.Response(401, text="Unauthorized")
            )
            client = _make_client()
            with pytest.raises(AtlassianAuthError):
                await client.list_projects()


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


class TestTransportRetries:
    """R2: GET-only retries, Retry-After, and the timeout-vs-unreachable split,
    shared by both product clients via clients/_http._send."""

    @pytest.fixture
    def _no_jitter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import mcp_atlassian_extended.clients._http as http_mod

        monkeypatch.setattr(http_mod._jitter, "uniform", lambda _a, _b: 0.0)

    async def test_get_retries_on_503_then_succeeds(self, _no_jitter: None) -> None:
        async with respx.mock(base_url=BASE) as router:
            route = router.get("/rest/api/2/project").mock(
                side_effect=[
                    httpx.Response(503, headers={"Retry-After": "1"}, text="unavailable"),
                    httpx.Response(200, json=[{"key": "PROJ"}]),
                ]
            )
            client = _make_client()
            result = await client.get("/rest/api/2/project")
            assert result == [{"key": "PROJ"}]
            assert route.call_count == 2

    async def test_get_retries_on_429_with_short_retry_after(self) -> None:
        async with respx.mock(base_url=BASE) as router:
            route = router.get("/rest/api/2/project").mock(
                side_effect=[
                    httpx.Response(429, headers={"Retry-After": "0"}, text="slow down"),
                    httpx.Response(200, json=[]),
                ]
            )
            client = _make_client()
            assert await client.get("/rest/api/2/project") == []
            assert route.call_count == 2

    async def test_write_is_never_retried(self) -> None:
        async with respx.mock(base_url=BASE) as router:
            route = router.delete("/rest/api/2/issue/PROJ-1").mock(
                side_effect=[httpx.Response(503, text="unavailable"), httpx.Response(204)]
            )
            client = _make_client()
            with pytest.raises(AtlassianApiError) as exc:
                await client.delete("/rest/api/2/issue/PROJ-1")
            assert exc.value.status_code == 503
            assert route.call_count == 1

    async def test_long_retry_after_429_surfaces_retry_after(self) -> None:
        async with respx.mock(base_url=BASE) as router:
            route = router.get("/rest/api/2/project").mock(
                return_value=httpx.Response(429, headers={"Retry-After": "30"}, text="slow")
            )
            client = _make_client()
            with pytest.raises(AtlassianRateLimitError) as exc:
                await client.get("/rest/api/2/project")
            assert exc.value.retry_after == 30.0
            assert exc.value.status_code == 429
            assert route.call_count == 1

    async def test_timeout_is_distinct_from_unreachable(self) -> None:
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/api/2/project").mock(side_effect=httpx.ReadTimeout("slow"))
            client = _make_client()
            with pytest.raises(AtlassianTimeoutError):
                await client.get("/rest/api/2/project")

    async def test_connect_error_is_unreachable(self) -> None:
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/api/2/project").mock(side_effect=httpx.ConnectError("refused"))
            client = _make_client()
            with pytest.raises(AtlassianConnectionError):
                await client.get("/rest/api/2/project")

    async def test_connect_phase_capped(self) -> None:
        client = JiraExtendedClient(JiraConfig(url=BASE, token="t", timeout=50))
        assert client._client.timeout.connect == 10  # min(10, 50)
        assert client._client.timeout.read == 50
        assert isinstance(client._client._transport, httpx.AsyncHTTPTransport)

    async def test_confluence_client_shares_retry_path(self, _no_jitter: None) -> None:
        async with respx.mock(base_url=CONFLUENCE_BASE) as router:
            route = router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
                side_effect=[
                    httpx.Response(503, text="unavailable"),
                    httpx.Response(200, json={"payload": [{"id": "c1"}]}),
                ]
            )
            client = ConfluenceExtendedClient(ConfluenceConfig(url=CONFLUENCE_BASE, token="t"))
            result = await client.list_calendars()
            assert result == [{"id": "c1"}]
            assert route.call_count == 2


class TestTransportTLS:
    """R2 fix: verify= must be on the transport (httpx 0.28 ignores the
    client-level verify once a transport is supplied)."""

    def test_jira_transport_verify_false(self) -> None:
        client = JiraExtendedClient(JiraConfig(url=BASE, token="t", ssl_verify=False))
        assert client._client._transport._pool._ssl_context.verify_mode == ssl.CERT_NONE

    def test_jira_transport_verify_true(self) -> None:
        client = JiraExtendedClient(JiraConfig(url=BASE, token="t", ssl_verify=True))
        assert client._client._transport._pool._ssl_context.verify_mode == ssl.CERT_REQUIRED

    def test_confluence_transport_verify_false(self) -> None:
        client = ConfluenceExtendedClient(
            ConfluenceConfig(url=CONFLUENCE_BASE, token="t", ssl_verify=False)
        )
        assert client._client._transport._pool._ssl_context.verify_mode == ssl.CERT_NONE

    def test_confluence_transport_verify_true(self) -> None:
        client = ConfluenceExtendedClient(
            ConfluenceConfig(url=CONFLUENCE_BASE, token="t", ssl_verify=True)
        )
        assert client._client._transport._pool._ssl_context.verify_mode == ssl.CERT_REQUIRED


class TestTransportBounds:
    """R2 fix: retry is bounded, cancellation is not swallowed, ConnectTimeout is
    unreachable, and credentials never leak into error text."""

    @pytest.fixture
    def _no_jitter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(_http._jitter, "uniform", lambda _a, _b: 0.0)

    async def test_connect_timeout_is_unreachable(self) -> None:
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/api/2/project").mock(side_effect=httpx.ConnectTimeout("no route"))
            with pytest.raises(AtlassianConnectionError):
                await _make_client().get("/rest/api/2/project")

    async def test_get_gives_up_after_two_attempts(self, _no_jitter: None) -> None:
        async with respx.mock(base_url=BASE) as router:
            route = router.get("/rest/api/2/project").mock(
                return_value=httpx.Response(503, text="unavailable")
            )
            with pytest.raises(AtlassianApiError) as exc:
                await _make_client().get("/rest/api/2/project")
            assert exc.value.status_code == 503
            assert route.call_count == 2

    async def test_cancellation_propagates_without_retry(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # respx cannot carry a BaseException side_effect; patch the httpx client.
        client = _make_client()
        calls = 0

        async def _boom(*_a, **_k):
            nonlocal calls
            calls += 1
            raise asyncio.CancelledError

        monkeypatch.setattr(client._client, "request", _boom)
        with pytest.raises(asyncio.CancelledError):
            await client.get("/rest/api/2/project")
        assert calls == 1

    async def test_url_userinfo_stripped_from_error(self) -> None:
        client = JiraExtendedClient(
            JiraConfig(url="https://user:secret@jira.example.com", token="t")
        )
        async with respx.mock(base_url="https://jira.example.com") as router:
            router.get("/rest/api/2/project").mock(side_effect=httpx.ConnectError("refused"))
            with pytest.raises(AtlassianConnectionError) as exc:
                await client.get("/rest/api/2/project")
            assert "secret" not in str(exc.value)


class TestStreamingDownloadTransport:
    """R2 fix 7: the streamed attachment download gets the same mapping."""

    async def test_stream_read_timeout_is_timeout(self) -> None:
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/api/2/attachment/content/9").mock(
                side_effect=httpx.ReadTimeout("slow")
            )
            with pytest.raises(AtlassianTimeoutError):
                await _make_client().download_attachment("/rest/api/2/attachment/content/9")

    async def test_stream_connect_error_is_unreachable(self) -> None:
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/api/2/attachment/content/9").mock(
                side_effect=httpx.ConnectError("refused")
            )
            with pytest.raises(AtlassianConnectionError):
                await _make_client().download_attachment("/rest/api/2/attachment/content/9")


class TestRetryAfterParsing:
    """_retry_after_seconds handles both forms, clamps, and rejects non-finite."""

    @staticmethod
    def _resp(retry_after: str | None) -> httpx.Response:
        headers = {"Retry-After": retry_after} if retry_after is not None else {}
        return httpx.Response(429, headers=headers)

    def test_delta_seconds(self) -> None:
        assert _http._retry_after_seconds(self._resp("5")) == 5.0

    def test_http_date(self) -> None:
        when = format_datetime(datetime.now(timezone.utc) + timedelta(seconds=100))
        secs = _http._retry_after_seconds(self._resp(when))
        assert secs is not None
        assert 80 <= secs <= 100

    def test_past_date_and_negative_clamped(self) -> None:
        assert _http._retry_after_seconds(self._resp("Wed, 21 Oct 2015 07:28:00 GMT")) == 0.0
        assert _http._retry_after_seconds(self._resp("-5")) == 0.0

    def test_non_finite_rejected(self) -> None:
        assert _http._retry_after_seconds(self._resp("nan")) is None
        assert _http._retry_after_seconds(self._resp("inf")) is None

    def test_absent(self) -> None:
        assert _http._retry_after_seconds(self._resp(None)) is None
