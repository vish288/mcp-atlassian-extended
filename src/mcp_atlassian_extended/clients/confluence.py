"""Confluence Extended API client — calendar and time-off tools."""

from __future__ import annotations

from typing import Any

import httpx

from ..config import ConfluenceConfig
from ..exceptions import TeamCalendarsUnavailableError
from ._http import _parse_json, _raise_for_atlassian, _send

LEAVE_KEYWORDS = ("vacation", "time off", "leaves", "time-off", "pto")

# Every calendar endpoint lives under the Team Calendars add-on namespace.
CALENDAR_API = "/rest/calendar-services/1.0/calendar"


class ConfluenceExtendedClient:
    """Async HTTP client for Confluence calendar services API."""

    def __init__(self, config: ConfluenceConfig | None = None) -> None:
        self.config = config or ConfluenceConfig.from_env()
        headers = {"Content-Type": "application/json", **self.config.auth_header}
        self._client = httpx.AsyncClient(
            base_url=self.config.url,
            headers=headers,
            timeout=httpx.Timeout(self.config.timeout, connect=min(10, self.config.timeout)),
            verify=self.config.ssl_verify,
            # verify= on the transport too: httpx 0.28 ignores the client-level
            # verify once a transport is supplied, but the client-level one is
            # still used for proxy mounts, so both carry the same value.
            transport=httpx.AsyncHTTPTransport(retries=2, verify=self.config.ssl_verify),
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, params: Any = None) -> Any:
        resp = await _send(
            self._client, "GET", path, unreachable_url=self.config.url, params=params
        )
        # Only the Team Calendars namespace turns a 404 into "add-on not installed".
        not_found = TeamCalendarsUnavailableError if path.startswith(CALENDAR_API) else None
        _raise_for_atlassian(resp, not_found=not_found)
        return _parse_json(resp)

    # ── Calendars ─────────────────────────────────────────────────

    @property
    def leave_keywords(self) -> tuple[str, ...]:
        """Built-in leave keywords plus any from ``CONFLUENCE_LEAVE_KEYWORDS``."""
        return LEAVE_KEYWORDS + self.config.leave_keywords

    async def list_calendars(self, space_key: str | None = None) -> list[dict]:
        """List calendars. Without *space_key* the API returns only the calendars the
        user subscribed to; with it, every calendar of that space."""
        params = (
            {"calendarContext": "spaceCalendars", "viewingSpaceKey": space_key}
            if space_key
            else None
        )
        data = await self._get(f"{CALENDAR_API}/subcalendars.json", params=params)
        if isinstance(data, dict):
            return data.get("payload", [])
        return data or []

    async def get_events(
        self,
        sub_calendar_ids: list[str],
        start: str,
        end: str,
        time_zone: str | None = None,
    ) -> list[dict]:
        """Get events from one or more sub-calendars.

        One request per sub-calendar: events.json answers only for the first
        ``subCalendarId`` when several are passed in one query.
        """
        events: list[dict] = []
        for cal_id in sub_calendar_ids:
            params: list[tuple[str, str]] = [
                ("start", start),
                ("end", end),
                ("subCalendarId", cal_id),
            ]
            if time_zone:
                params.append(("userTimeZoneId", time_zone))
            data = await self._get(f"{CALENDAR_API}/events.json", params=params)
            # An empty calendar answers {"success": true} with no "events" key.
            events.extend((data.get("events", []) if isinstance(data, dict) else data) or [])
        return events

    async def get_calendar_events(
        self,
        start: str,
        end: str,
        space_key: str | None = None,
        calendar: str | None = None,
        time_zone: str | None = None,
    ) -> list[dict]:
        """Get events of every calendar, optionally narrowed to a space and/or a calendar.

        *calendar* matches a parent or child calendar by exact ID or by name
        (case-insensitive substring). Events live on the child calendars, so a
        matched parent is expanded into its children.
        """
        wrappers = await self.list_calendars(space_key)
        wanted = calendar.lower() if calendar else None

        def matches(sub: dict) -> bool:
            return (
                wanted is None or sub.get("id") == calendar or wanted in sub.get("name", "").lower()
            )

        # sub-calendar id -> (calendar name, parent calendar name)
        targets: dict[str, tuple[str, str]] = {}
        # Custom event types are defined on the parent; their titles are the
        # category names the Confluence UI shows ("Wartungsfenster", ...).
        type_titles: dict[str, str] = {}
        for wrapper in wrappers:
            parent = wrapper.get("subCalendar", {})
            parent_name = parent.get("name", "")
            for t in parent.get("customEventTypes", []):
                type_titles[t.get("customEventTypeId", "")] = t.get("title", "")
            children = [c.get("subCalendar", {}) for c in wrapper.get("childSubCalendars", [])]
            parent_hit = matches(parent)
            for child in children:
                if parent_hit or matches(child):
                    targets[child["id"]] = (child.get("name", ""), parent_name)
            if not children and parent_hit:
                targets[parent["id"]] = (parent_name, parent_name)

        result: list[dict] = []
        for cal_id, (cal_name, parent_name) in targets.items():
            for event in await self.get_events([cal_id], start, end, time_zone):
                ev_start = event.get("start") or ""
                ev_end = event.get("end") or ev_start
                # events.json pads the range to whole calendar views; keep only
                # events that overlap [start, end] (both dates inclusive).
                if ev_start[:10] > end or ev_end[:10] < start:
                    continue
                invitees = event.get("invitees", [])
                result.append(
                    {
                        "id": event.get("id"),
                        "title": event.get("title", ""),
                        "start": event.get("start"),
                        "end": event.get("end"),
                        "all_day": event.get("allDay", False),
                        "event_type": event.get("eventType"),
                        "category": type_titles.get(
                            event.get("customEventTypeId", ""), event.get("className")
                        ),
                        "description": event.get("description", ""),
                        "location": event.get("where"),
                        "url": event.get("url"),
                        "invitees": [i.get("displayName") for i in invitees],
                        "calendar_name": cal_name,
                        "parent_calendar_name": parent_name,
                        "calendar_id": cal_id,
                    }
                )
        result.sort(key=lambda e: e["start"] or "")
        return result

    async def get_all_leave_calendars(self) -> list[dict]:
        """Find all calendar wrappers that contain leave/time-off calendars."""
        all_cals = await self.list_calendars()
        keywords = self.leave_keywords
        result = []
        for wrapper in all_cals:
            sub = wrapper.get("subCalendar", {})
            name_lower = sub.get("name", "").lower()
            if any(kw in name_lower for kw in keywords):
                result.append(wrapper)
                continue
            # Check child calendars
            children = wrapper.get("childSubCalendars", [])
            for child_wrapper in children:
                child_sub = child_wrapper.get("subCalendar", {})
                child_name = child_sub.get("name", "").lower()
                if any(kw in child_name for kw in keywords):
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
                    if any(kw in child_name for kw in self.leave_keywords):
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
