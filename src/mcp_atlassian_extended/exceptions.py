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


class WriteDisabledError(AtlassianError):
    """Raised when a write operation is attempted in read-only mode."""

    def __init__(self) -> None:
        super().__init__("Write operations are disabled (ATLASSIAN_READ_ONLY=true)")
