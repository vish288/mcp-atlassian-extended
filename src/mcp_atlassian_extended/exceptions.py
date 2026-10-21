"""Atlassian API exceptions."""

from __future__ import annotations


class AtlassianError(Exception):
    """Base exception for Atlassian operations."""


class AtlassianApiError(AtlassianError):
    """Raised when the API returns a non-success response."""

    def __init__(self, status_code: int, message: str, body: str = "") -> None:
        self.status_code = status_code
        self.body = body
        detail = f": {message}" if message else ""
        super().__init__(f"Atlassian API Error {status_code}{detail}")


class AtlassianAuthError(AtlassianApiError):
    """Raised on 401/403 authentication failures."""

    def __init__(self, status_code: int, body: str = "") -> None:
        super().__init__(status_code, "Authentication failed", body)


class TeamCalendarsUnavailableError(AtlassianApiError):
    """Raised when the Team Calendars add-on endpoints return 404.

    Every Confluence calendar tool goes through ``/rest/calendar-services/1.0/``,
    which only exists when the Team Calendars add-on is installed.
    """

    def __init__(self, body: str = "") -> None:
        super().__init__(
            404,
            "Team Calendars add-on not available — /rest/calendar-services/1.0/ returned 404",
            body,
        )


class AtlassianRateLimitError(AtlassianApiError):
    """Raised on a 429 that the bounded retry did not resolve.

    ``retry_after`` is the parsed ``Retry-After`` delta-seconds (None when the
    header was absent or an HTTP-date); it is surfaced in the error envelope so
    the caller knows how long to wait. Mirrors mcp-coda/mcp-argocd.
    """

    def __init__(
        self, status_code: int, body: str = "", *, retry_after: float | None = None
    ) -> None:
        super().__init__(status_code, "Rate limited", body)
        self.retry_after = retry_after


class AtlassianTimeoutError(AtlassianError):
    """A request to the Atlassian API exceeded its deadline (connect/read/write).

    Split out from ``AtlassianConnectionError`` (ported from mcp-argocd) so "the
    server is slow" is distinguishable from "the server is unreachable".
    """

    def __init__(self, url: str, detail: str = "") -> None:
        self.url = url
        self.detail = detail
        msg = f"Timed out reaching {url}"
        if detail:
            msg = f"{msg}: {detail}"
        super().__init__(msg)


class AtlassianConnectionError(AtlassianError):
    """The Atlassian API could not be reached (DNS, connect, TLS — not a timeout)."""

    def __init__(self, url: str, detail: str = "") -> None:
        self.url = url
        self.detail = detail
        msg = f"Cannot reach {url}"
        if detail:
            msg = f"{msg}: {detail}"
        super().__init__(msg)


class WriteDisabledError(AtlassianError):
    """Raised when a write operation is attempted in read-only mode."""

    def __init__(self) -> None:
        super().__init__("Write operations are disabled (MCP_READ_ONLY / ATLASSIAN_READ_ONLY)")
