"""Jira Extended API client — attachments, agile, links, users, metadata."""

from __future__ import annotations

import asyncio
import mimetypes
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlparse

import httpx

from ..config import JiraConfig
from ._http import _parse_json, _raise_for_atlassian

MIME_OVERRIDES = {
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".json": "application/json",
}

_DEFAULT_PORTS = {"http": 80, "https": 443}

# Default backlog fields: a board can hold hundreds of issues, and ``*all`` on
# each is hundreds of KB of context. Callers opt into more via the ``fields`` arg.
_BACKLOG_DEFAULT_FIELDS = "summary,status,issuetype,priority,assignee,labels"


def _seg(value: Any) -> str:
    """Percent-encode one REST path segment so a caller-supplied id/key cannot
    inject extra path segments or a query string.

    Every path this client builds interpolates a caller value (issue key,
    attachment/link/version id, project key). httpx normalises ``..`` but not
    ``%2F``, so quoting with ``safe=""`` is what stops ``../issue/PROJ-1`` in an
    attachment id from turning a DELETE-attachment into a DELETE-issue.
    """
    return quote(str(value), safe="")


def _origin(url: str) -> tuple[str, str, int | None]:
    """Return (scheme, host, port) with the scheme's default port filled in.

    Comparing full origins rather than bare hostnames: a downgrade to http, or a
    different port on the same host, is a different destination, and the request
    that follows carries the Bearer token.
    """
    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    return (scheme, (parsed.hostname or "").lower(), parsed.port or _DEFAULT_PORTS.get(scheme))


class JiraExtendedClient:
    """Async HTTP client for Jira REST API v2 + Agile API."""

    def __init__(self, config: JiraConfig | None = None) -> None:
        self.config = config or JiraConfig.from_env()
        # No client-level Content-Type: httpx sets it per request — application/json
        # for ``json=`` bodies, multipart/form-data (with boundary) for ``files=``.
        # A client-level value wins over both and would send attachment uploads
        # labelled application/json with no boundary.
        headers = dict(self.config.auth_header)
        self._client = httpx.AsyncClient(
            base_url=self.config.url,
            headers=headers,
            timeout=self.config.timeout,
            verify=self.config.ssl_verify,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json_data: Any = None,
        params: dict[str, Any] | None = None,
        content: bytes | None = None,
        extra_headers: dict[str, str] | None = None,
        raw: bool = False,
    ) -> Any:
        headers = {}
        if extra_headers:
            headers.update(extra_headers)

        kwargs: dict[str, Any] = {"params": params, "headers": headers}
        if json_data is not None:
            kwargs["json"] = json_data
        if content is not None:
            kwargs["content"] = content

        resp = await self._client.request(method, path, **kwargs)
        _raise_for_atlassian(resp)
        if raw:
            return resp.content
        return _parse_json(resp)

    async def get(self, path: str, params: dict[str, Any] | None = None, **kw: Any) -> Any:
        return await self._request("GET", path, params=params, **kw)

    async def post(self, path: str, json_data: Any = None, **kw: Any) -> Any:
        return await self._request("POST", path, json_data=json_data, **kw)

    async def put(self, path: str, json_data: Any = None, **kw: Any) -> Any:
        return await self._request("PUT", path, json_data=json_data, **kw)

    async def delete(self, path: str, **kw: Any) -> Any:
        return await self._request("DELETE", path, **kw)

    # ── Path Validation ─────────────────────────────────────────────

    @staticmethod
    def _validate_file_path(path: str) -> Path:
        """Validate file path is safe — no traversal, reasonable size."""
        resolved = Path(path).resolve()
        if ".." in Path(path).parts:
            msg = f"Path traversal detected: {path}"
            raise ValueError(msg)
        if not resolved.is_file():
            msg = f"File not found: {resolved}"
            raise FileNotFoundError(msg)
        size_mb = resolved.stat().st_size / (1024 * 1024)
        if size_mb > 100:
            msg = f"File too large ({size_mb:.1f}MB). Max 100MB."
            raise ValueError(msg)
        return resolved

    def _validate_download_url(self, url: str) -> str:
        """Validate a download URL points at the configured Jira instance.

        The whole origin must match, not just the host. Checking the hostname
        alone let ``http://jira.example.com:9999/...`` through against an
        ``https://jira.example.com`` config -- and the request that follows
        sends the Bearer token, so a downgrade to cleartext or a redirect to
        another port on the same host leaked the credential this check exists
        to protect.
        """
        parsed = urlparse(url)
        # Any scheme or network location makes this an absolute destination, not
        # a path relative to the configured base_url. ``startswith(("http://",
        # ...))`` missed ``HTTPS://`` (case) and ``//host`` (scheme-relative),
        # either of which httpx then sends absolute -- with the Bearer header.
        if parsed.scheme or parsed.netloc:
            actual, expected = _origin(url), _origin(self.config.url)
            if actual != expected:
                msg = (
                    f"URL origin {actual[0]}://{actual[1]}:{actual[2]} doesn't match "
                    f"configured Jira URL {expected[0]}://{expected[1]}:{expected[2]}"
                )
                raise ValueError(msg)
        return url

    # ── Attachments ───────────────────────────────────────────────

    async def get_attachments(self, issue_key: str) -> list[dict]:
        data = await self.get(
            f"/rest/api/2/issue/{_seg(issue_key)}", params={"fields": "attachment"}
        )
        return data.get("fields", {}).get("attachment", [])

    async def upload_attachment(
        self, issue_key: str, file_path: str, filename: str | None = None
    ) -> list[dict]:
        p = self._validate_file_path(file_path)
        fname = filename or p.name
        content_type = (
            MIME_OVERRIDES.get(p.suffix.lower())
            or mimetypes.guess_type(fname)[0]
            or "application/octet-stream"
        )

        data = await asyncio.to_thread(p.read_bytes)
        files = {"file": (fname, data, content_type)}
        # Auth header is already set client-side; only the CSRF opt-out is per request.
        resp = await self._client.post(
            f"/rest/api/2/issue/{_seg(issue_key)}/attachments",
            files=files,
            headers={"X-Atlassian-Token": "no-check"},
        )
        _raise_for_atlassian(resp)
        return _parse_json(resp)

    async def download_attachment(self, content_url: str) -> bytes:
        """Download attachment content. Handles both absolute and relative URLs.

        ``redirect=false`` keeps Jira Cloud from answering 303 to a pre-signed
        media host (``api.media.atlassian.com``) that this client, which does not
        follow redirects, would raise on. With it Cloud returns the bytes inline;
        Server/DC ignores the unknown param. Following the redirect instead would
        leak the Authorization header off-origin, so it is deliberately not done.
        See https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-attachments/#api-rest-api-3-attachment-content-id-get
        """
        content_url = self._validate_download_url(content_url)
        params = {"redirect": "false"}
        # Case-insensitive: ``HTTPS://`` is still absolute and must not be sent
        # as a path relative to base_url.
        if urlparse(content_url).scheme:
            # Auth header is already set client-side; no need to repeat it here.
            resp = await self._client.request("GET", content_url, params=params)
            _raise_for_atlassian(resp)
            return resp.content
        return await self.get(content_url, params=params, raw=True)

    async def delete_attachment(self, attachment_id: str) -> None:
        await self.delete(f"/rest/api/2/attachment/{_seg(attachment_id)}")

    # ── Users ─────────────────────────────────────────────────────

    async def search_users(
        self, query: str, max_results: int = 10, start_at: int = 0
    ) -> list[dict]:
        # Jira Cloud removed ``username`` in the GDPR user-privacy migration and
        # answers 400 unless ``query`` (or ``accountId``) is used; Server/DC still
        # takes ``username``. Pick by deployment, which the config already detects
        # from the auth mode (Cloud = basic auth).
        # https://developer.atlassian.com/cloud/jira/platform/rest/v2/api-group-user-search/#api-rest-api-2-user-search-get
        key = "query" if self.config.is_cloud else "username"
        return await self.get(
            "/rest/api/2/user/search",
            params={key: query, "maxResults": max_results, "startAt": start_at},
        )

    # ── Metadata ──────────────────────────────────────────────────

    async def list_projects(self) -> list[dict]:
        return await self.get("/rest/api/2/project")

    async def list_fields(self) -> list[dict]:
        return await self.get("/rest/api/2/field")

    # ── Agile: Boards ─────────────────────────────────────────────

    async def get_board(self, board_id: int) -> dict:
        return await self.get(f"/rest/agile/1.0/board/{_seg(board_id)}")

    async def get_board_config(self, board_id: int) -> dict:
        return await self.get(f"/rest/agile/1.0/board/{_seg(board_id)}/configuration")

    async def get_backlog(
        self,
        board_id: int,
        max_results: int = 50,
        start_at: int = 0,
        fields: str = _BACKLOG_DEFAULT_FIELDS,
    ) -> dict:
        return await self.get(
            f"/rest/agile/1.0/board/{_seg(board_id)}/backlog",
            params={"fields": fields, "maxResults": max_results, "startAt": start_at},
        )

    # ── Agile: Sprints ────────────────────────────────────────────

    async def get_sprint(self, sprint_id: int) -> dict:
        return await self.get(f"/rest/agile/1.0/sprint/{_seg(sprint_id)}")

    async def move_to_sprint(self, sprint_id: int, issue_keys: list[str]) -> None:
        await self.post(
            f"/rest/agile/1.0/sprint/{_seg(sprint_id)}/issue",
            {"issues": issue_keys},
        )

    # ── Issues ─────────────────────────────────────────────────────

    async def create_issue(
        self,
        project_key: str,
        summary: str,
        issue_type: str = "Story",
        *,
        description: str | None = None,
        labels: list[str] | None = None,
        priority: str | None = None,
        custom_fields: dict[str, Any] | None = None,
    ) -> dict:
        """Create a Jira issue. custom_fields are merged directly into the fields payload."""
        fields: dict[str, Any] = {
            "project": {"key": project_key},
            "summary": summary,
            "issuetype": {"name": issue_type},
        }
        if description is not None:
            fields["description"] = description
        if labels:
            fields["labels"] = labels
        if priority:
            fields["priority"] = {"name": priority}
        if custom_fields:
            fields.update(custom_fields)
        return await self.post("/rest/api/2/issue", {"fields": fields})

    async def update_issue(
        self,
        issue_key: str,
        *,
        fields: dict[str, Any] | None = None,
        custom_fields: dict[str, Any] | None = None,
    ) -> None:
        """Update a Jira issue. fields and custom_fields are merged into the payload."""
        merged = {**(fields or {}), **(custom_fields or {})}
        if merged:
            await self.put(f"/rest/api/2/issue/{_seg(issue_key)}", {"fields": merged})

    async def create_issue_link(
        self,
        link_type: str,
        inward_issue_key: str,
        outward_issue_key: str,
        *,
        comment: str | None = None,
    ) -> None:
        """Create a link between two issues."""
        body: dict[str, Any] = {
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_issue_key},
            "outwardIssue": {"key": outward_issue_key},
        }
        if comment:
            body["comment"] = {"body": comment}
        await self.post("/rest/api/2/issueLink", body)

    async def delete_issue_link(self, link_id: str) -> None:
        """Delete an issue link by ID."""
        await self.delete(f"/rest/api/2/issueLink/{_seg(link_id)}")

    async def get_issue_links(self, issue_key: str) -> list[dict]:
        """Get all links for an issue."""
        data = await self.get(
            f"/rest/api/2/issue/{_seg(issue_key)}",
            params={"fields": "issuelinks"},
        )
        return data.get("fields", {}).get("issuelinks", [])

    # ── Versions ──────────────────────────────────────────────────

    async def get_project_versions(self, project_key: str) -> list[dict]:
        """Get all versions for a project."""
        return await self.get(f"/rest/api/2/project/{_seg(project_key)}/versions")

    async def create_version(
        self,
        project_key: str,
        name: str,
        *,
        description: str | None = None,
        release_date: str | None = None,
        start_date: str | None = None,
        released: bool | None = None,
        archived: bool | None = None,
    ) -> dict:
        """Create a new version in a project.

        Uses REST API v2 (/rest/api/2/version) which works on both
        Server/Data Center and Cloud. The upstream mcp-atlassian package
        uses /rest/api/3/version which is Cloud-only.
        """
        payload: dict[str, Any] = {"project": project_key, "name": name}
        if description is not None:
            payload["description"] = description
        if release_date is not None:
            payload["releaseDate"] = release_date
        if start_date is not None:
            payload["startDate"] = start_date
        if released is not None:
            payload["released"] = released
        if archived is not None:
            payload["archived"] = archived
        return await self.post("/rest/api/2/version", payload)

    async def update_version(
        self,
        version_id: str,
        *,
        name: str | None = None,
        description: str | None = None,
        release_date: str | None = None,
        start_date: str | None = None,
        released: bool | None = None,
        archived: bool | None = None,
    ) -> dict:
        """Update an existing version by ID."""
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if release_date is not None:
            payload["releaseDate"] = release_date
        if start_date is not None:
            payload["startDate"] = start_date
        if released is not None:
            payload["released"] = released
        if archived is not None:
            payload["archived"] = archived
        if not payload:
            return await self.get(f"/rest/api/2/version/{_seg(version_id)}")
        return await self.put(f"/rest/api/2/version/{_seg(version_id)}", payload)
