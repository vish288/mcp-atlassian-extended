"""Confluence Extended API client — calendar and time-off tools."""

from __future__ import annotations

import json
from typing import Any

import httpx

from ..config import ConfluenceConfig
from ..exceptions import AtlassianApiError, AtlassianAuthError

LEAVE_KEYWORDS = ("vacation", "time off", "leaves", "time-off", "pto")


class ConfluenceExtendedClient:
    """Async HTTP client for Confluence calendar services API."""

    def __init__(self, config: ConfluenceConfig | None = None) -> None:
        self.config = config or ConfluenceConfig.from_env()
        self._client = httpx.AsyncClient(
            base_url=self.config.url,
            headers={
                "Authorization": f"Bearer {self.config.token}",
                "Content-Type": "application/json",
            },
            timeout=self.config.timeout,
            verify=self.config.ssl_verify,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        resp = await self._client.get(path, params=params)
        if resp.status_code in (401, 403):
            raise AtlassianAuthError(resp.status_code, resp.text)
        if not resp.is_success:
            raise AtlassianApiError(resp.status_code, resp.reason_phrase or "", resp.text)
        if not resp.content:
            return None
        content_type = resp.headers.get("content-type", "")
        if "text/html" in content_type:
            raise AtlassianApiError(resp.status_code, "Unexpected HTML response", resp.text[:500])
        try:
            return resp.json()
        except json.JSONDecodeError as e:
            raise AtlassianApiError(
                resp.status_code, f"JSON parse error: {e}", resp.text[:500]
            ) from e

    # ── Calendars ─────────────────────────────────────────────────

    async def list_calendars(self) -> list[dict]:
        data = await self._get("/rest/calendar-services/1.0/calendar/subcalendars.json")
        if isinstance(data, dict):
            return data.get("payload", [])
        return data or []

    async def get_events(
        self,
        sub_calendar_ids: list[str],
        start: str,
        end: str,
    ) -> list[dict]:
        """Get events from one or more sub-calendars."""
        params: list[tuple[str, str]] = [("start", start), ("end", end)]
        for cal_id in sub_calendar_ids:
            params.append(("subCalendarId", cal_id))
        resp = await self._client.get(
            "/rest/calendar-services/1.0/calendar/events.json",
            params=params,
        )
        if not resp.is_success:
            raise AtlassianApiError(resp.status_code, resp.reason_phrase or "", resp.text)
        data = resp.json()
        events = data.get("events", []) if isinstance(data, dict) else data
        return events or []

    async def get_all_leave_calendars(self) -> list[dict]:
        """Find all calendar wrappers that contain leave/time-off calendars."""
        all_cals = await self.list_calendars()
        result = []
        for wrapper in all_cals:
            sub = wrapper.get("subCalendar", {})
            name_lower = sub.get("name", "").lower()
            if any(kw in name_lower for kw in LEAVE_KEYWORDS):
                result.append(wrapper)
                continue
            # Check child calendars
            children = wrapper.get("childSubCalendars", [])
            for child_wrapper in children:
                child_sub = child_wrapper.get("subCalendar", {})
                child_name = child_sub.get("name", "").lower()
                if any(kw in child_name for kw in LEAVE_KEYWORDS):
                    result.append(wrapper)
                    break
        return result

    async def get_time_off_events(
        self,
        start: str,
        end: str,
        calendar_name: str | None = None,
    ) -> list[dict]:
        """Get time-off events across all leave calendars."""
        leave_cals = await self.get_all_leave_calendars()
        if calendar_name:
            leave_cals = [
                w
                for w in leave_cals
                if calendar_name.lower() in w.get("subCalendar", {}).get("name", "").lower()
            ]

        all_events: list[dict] = []
        for wrapper in leave_cals:
            # Collect child sub-calendar IDs (children-only to avoid API 0-result bug)
            cal_ids: list[str] = []
            children = wrapper.get("childSubCalendars", [])
            if children:
                for child in children:
                    child_sub = child.get("subCalendar", {})
                    child_name = child_sub.get("name", "").lower()
                    if any(kw in child_name for kw in LEAVE_KEYWORDS):
                        cal_ids.append(child_sub["id"])
            else:
                cal_ids.append(wrapper["subCalendar"]["id"])

            if not cal_ids:
                continue

            events = await self.get_events(cal_ids, start, end)
            cal_name = wrapper.get("subCalendar", {}).get("name", "")
            for event in events:
                event_type = event.get("eventType", "")
                class_name = event.get("className", "")
                if event_type == "leaves" or class_name == "leaves":
                    invitees = event.get("invitees", [])
                    person = invitees[0] if invitees else {}
                    all_events.append(
                        {
                            "id": event.get("id"),
                            "person_name": person.get("displayName", event.get("title", "")),
                            "person_email": person.get("email"),
                            "description": event.get("title", ""),
                            "start_date": event.get("start", "")[:10],
                            "end_date": event.get("end", "")[:10],
                            "calendar_name": cal_name,
                            "calendar_id": event.get("subCalendarId"),
                            "all_day": event.get("allDay", True),
                        }
                    )

        return all_events
