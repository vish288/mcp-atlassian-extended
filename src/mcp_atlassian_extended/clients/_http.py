"""Request sending and response handling shared by the Jira and Confluence clients."""

from __future__ import annotations

import asyncio
import json
import math
import random
from collections.abc import Callable
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import httpx

from ..exceptions import (
    AtlassianApiError,
    AtlassianAuthError,
    AtlassianConnectionError,
    AtlassianRateLimitError,
    AtlassianTimeoutError,
)

# Transport retry policy (R2). Idempotent GETs are retried on a transient
# upstream status; writes are never retried. httpx's AsyncHTTPTransport(retries=)
# already covers connection-level failures, so this layer only adds status
# retries. "Max 2 attempts" = the initial request plus at most one retry.
_RETRY_STATUSES = frozenset({502, 503, 504})
_MAX_ATTEMPTS = 2
_MAX_RETRY_AFTER = 5.0  # only honour a 429 Retry-After at most this long (seconds)
_jitter = random.SystemRandom()  # jitter source; SystemRandom sidesteps the S311 lint


def _retry_after_seconds(resp: httpx.Response) -> float | None:
    """Parse a ``Retry-After`` header to seconds-from-now, or None when absent.

    Both forms are handled: delta-seconds, and an HTTP-date (RFC 7231), which is
    converted to the delay from now. The result is clamped to >= 0 (a past date
    means "retry now") and non-finite values are rejected."""
    raw = resp.headers.get("Retry-After")
    if raw is None:
        return None
    raw = raw.strip()
    try:
        seconds = float(raw)
    except ValueError:
        try:
            when = parsedate_to_datetime(raw)
        except (TypeError, ValueError):
            return None
        if when is None:
            return None
        if when.tzinfo is None:
            when = when.replace(tzinfo=timezone.utc)
        seconds = (when - datetime.now(timezone.utc)).total_seconds()
    if not math.isfinite(seconds):
        return None
    return max(0.0, seconds)


def _retry_delay(resp: httpx.Response) -> float | None:
    """Seconds to wait before retrying this response, or None to not retry.

    502/503/504 get a jittered backoff; a 429 is retried only when it names a
    ``Retry-After`` of at most ``_MAX_RETRY_AFTER`` seconds."""
    if resp.status_code in _RETRY_STATUSES:
        return _jitter.uniform(0.5, 1.5)
    if resp.status_code == 429:
        after = _retry_after_seconds(resp)
        if after is not None and after <= _MAX_RETRY_AFTER:
            return after
    return None


def _transport_error(exc: httpx.TransportError, unreachable_url: str) -> Exception:
    """Map a transport exception to the right expected error, shared by the
    request path and the streamed-download path.

    A ``ConnectTimeout`` means the host was never reached, so it is unreachable,
    not a slow request (it is a ``TimeoutException`` subclass, so it is tested
    first). Userinfo is stripped so a credential in the URL never lands in an
    error (as mcp-argocd/mcp-gitlab/mcp-coda do)."""
    safe = str(httpx.URL(unreachable_url).copy_with(username=None, password=None))
    if isinstance(exc, httpx.ConnectTimeout):
        return AtlassianConnectionError(safe, str(exc))
    if isinstance(exc, httpx.TimeoutException):
        return AtlassianTimeoutError(safe, str(exc))
    return AtlassianConnectionError(safe, str(exc))


async def _send(
    client: httpx.AsyncClient, method: str, path: str, *, unreachable_url: str, **kwargs: Any
) -> httpx.Response:
    """One send path with the R2 retry policy, shared by both product clients.

    Idempotent GETs are retried on a transient upstream status (502/503/504, or a
    429 naming a short ``Retry-After``) with jitter; writes are never retried.
    Connection-level failures are retried beneath this by
    ``AsyncHTTPTransport(retries=2)``. A timeout and an unreachable host become
    distinct expected errors (the split is ported from mcp-argocd)."""
    resp: httpx.Response
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            resp = await client.request(method, path, **kwargs)
        except httpx.TransportError as e:
            raise _transport_error(e, unreachable_url) from e
        if method == "GET" and attempt < _MAX_ATTEMPTS:
            delay = _retry_delay(resp)
            if delay is not None:
                await asyncio.sleep(delay)
                continue
        return resp
    return resp  # pragma: no cover — the loop always returns


def _raise_for_atlassian(
    resp: httpx.Response, *, not_found: Callable[[str], Exception] | None = None
) -> None:
    """Map an Atlassian error response to the matching exception.

    *not_found* gives a 404 a more specific meaning for one namespace (Confluence's
    Team Calendars add-on); it is called with the response body.
    """
    if resp.status_code in (401, 403):
        raise AtlassianAuthError(resp.status_code, resp.text)
    if resp.status_code == 404 and not_found is not None:
        raise not_found(resp.text[:500])
    if resp.status_code == 429:
        raise AtlassianRateLimitError(
            resp.status_code, resp.text, retry_after=_retry_after_seconds(resp)
        )
    if not resp.is_success:
        raise AtlassianApiError(resp.status_code, resp.reason_phrase or "", resp.text)


def _parse_json(resp: httpx.Response) -> Any:
    """Decode a successful response body; ``None`` when it is empty."""
    if not resp.content:
        return None
    if "text/html" in resp.headers.get("content-type", ""):
        raise AtlassianApiError(
            resp.status_code, "Unexpected HTML response — check auth", resp.text[:500]
        )
    try:
        return resp.json()
    except json.JSONDecodeError as e:
        raise AtlassianApiError(resp.status_code, f"JSON parse error: {e}", resp.text[:500]) from e
