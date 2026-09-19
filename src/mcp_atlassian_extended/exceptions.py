"""Atlassian API exceptions."""

from __future__ import annotations


class AtlassianError(Exception):
    """Base exception for Atlassian operations."""


class AtlassianApiError(AtlassianError):
    """Raised when the API returns a non-success response."""

    def __init__(self, status_code: int, message: str, body: str = "") -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"Atlassian API Error {status_code}: {message}")


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


class WriteDisabledError(AtlassianError):
    """Raised when a write operation is attempted in read-only mode."""

    def __init__(self) -> None:
        super().__init__("Write operations are disabled (ATLASSIAN_READ_ONLY=true)")
