"""Jira Extended API client — attachments, agile, links, users, metadata."""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path
from typing import Any

import httpx

from ..config import JiraConfig
from ..exceptions import AtlassianApiError, AtlassianAuthError

MIME_OVERRIDES = {
    ".md": "text/markdown",
    ".txt": "text/plain",
    ".json": "application/json",
}


class JiraExtendedClient:
    """Async HTTP client for Jira REST API v2 + Agile API."""

    def __init__(self, config: JiraConfig | None = None) -> None:
        self.config = config or JiraConfig.from_env()
        headers = {"Content-Type": "application/json", **self.config.auth_header}
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

        if resp.status_code in (401, 403):
            raise AtlassianAuthError(resp.status_code, resp.text)
        if not resp.is_success:
            raise AtlassianApiError(resp.status_code, resp.reason_phrase or "", resp.text)

        if resp.status_code == 204 or not resp.content:
            return None

        if raw:
            return resp.content

        content_type = resp.headers.get("content-type", "")
        if "text/html" in content_type:
            raise AtlassianApiError(
                resp.status_code, "Unexpected HTML response — check auth", resp.text[:500]
            )

        try:
            return resp.json()
        except json.JSONDecodeError as e:
            raise AtlassianApiError(
                resp.status_code, f"JSON parse error: {e}", resp.text[:500]
            ) from e

    async def get(self, path: str, params: dict[str, Any] | None = None, **kw: Any) -> Any:
        return await self._request("GET", path, params=params, **kw)

    async def post(self, path: str, json_data: Any = None, **kw: Any) -> Any:
        return await self._request("POST", path, json_data=json_data, **kw)

    async def put(self, path: str, json_data: Any = None, **kw: Any) -> Any:
        return await self._request("PUT", path, json_data=json_data, **kw)

    async def delete(self, path: str, **kw: Any) -> Any:
        return await self._request("DELETE", path, **kw)

    # ── Attachments ───────────────────────────────────────────────

    async def get_attachments(self, issue_key: str) -> list[dict]:
        data = await self.get(f"/rest/api/2/issue/{issue_key}", params={"fields": "attachment"})
        return data.get("fields", {}).get("attachment", [])

    async def upload_attachment(
        self, issue_key: str, file_path: str, filename: str | None = None
    ) -> list[dict]:
        p = Path(file_path)
        fname = filename or p.name
        content_type = (
            MIME_OVERRIDES.get(p.suffix.lower())
            or mimetypes.guess_type(fname)[0]
            or "application/octet-stream"
        )

        files = {"file": (fname, p.read_bytes(), content_type)}
        resp = await self._client.post(
            f"/rest/api/2/issue/{issue_key}/attachments",
            files=files,
            headers={
                "X-Atlassian-Token": "no-check",
                "Authorization": f"Bearer {self.config.token}",
            },
        )
        if not resp.is_success:
            raise AtlassianApiError(resp.status_code, resp.reason_phrase or "", resp.text)
        return resp.json()

    async def download_attachment(self, content_url: str) -> bytes:
        return await self.get(content_url, raw=True)

    async def delete_attachment(self, attachment_id: str) -> None:
        await self.delete(f"/rest/api/2/attachment/{attachment_id}")

    # ── Users ─────────────────────────────────────────────────────

    async def search_users(self, query: str, max_results: int = 10) -> list[dict]:
        return await self.get(
            "/rest/api/2/user/search",
            params={"username": query, "maxResults": max_results},
        )

    # ── Metadata ──────────────────────────────────────────────────

    async def list_projects(self) -> list[dict]:
        return await self.get("/rest/api/2/project")

    async def list_fields(self) -> list[dict]:
        return await self.get("/rest/api/2/field")

    # ── Agile: Boards ─────────────────────────────────────────────

    async def get_board(self, board_id: int) -> dict:
        return await self.get(f"/rest/agile/1.0/board/{board_id}")

    async def get_board_config(self, board_id: int) -> dict:
        return await self.get(f"/rest/agile/1.0/board/{board_id}/configuration")

    async def get_backlog(self, board_id: int, max_results: int = 50) -> dict:
        return await self.get(
            f"/rest/agile/1.0/board/{board_id}/backlog",
            params={"fields": "*all", "maxResults": max_results},
        )

    # ── Agile: Sprints ────────────────────────────────────────────

    async def get_sprint(self, sprint_id: int) -> dict:
        return await self.get(f"/rest/agile/1.0/sprint/{sprint_id}")

    async def move_to_sprint(self, sprint_id: int, issue_keys: list[str]) -> None:
        await self.post(
            f"/rest/agile/1.0/sprint/{sprint_id}/issue",
            {"issues": issue_keys},
        )
