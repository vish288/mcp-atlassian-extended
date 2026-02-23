"""Confluence Extended tools — calendars, time-off, sprint capacity."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Annotated

from dateutil.parser import parse as parse_date
from fastmcp import Context
from pydantic import Field

from . import mcp
from ._helpers import _err, _get_confluence, _ok


def _resolve_date(value: str) -> str:
    """Resolve relative dates like 'today', '+14d', 'next week' to ISO format."""
    v = value.strip().lower()
    now = datetime.now()

    if v == "today":
        return now.strftime("%Y-%m-%d")
    if v == "tomorrow":
        return (now + timedelta(days=1)).strftime("%Y-%m-%d")
    if v == "next week":
        days_until_monday = (7 - now.weekday()) % 7 or 7
        return (now + timedelta(days=days_until_monday)).strftime("%Y-%m-%d")
    if v.startswith("+") and v.endswith("d"):
        days = int(v[1:-1])
        return (now + timedelta(days=days)).strftime("%Y-%m-%d")
    if v.startswith("-") and v.endswith("d"):
        days = int(v[1:-1])
        return (now - timedelta(days=days)).strftime("%Y-%m-%d")

    # Try ISO parse
    return parse_date(value).strftime("%Y-%m-%d")


@mcp.tool(
    tags={"confluence", "calendars", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def confluence_list_calendars(
    ctx: Context,
    filter_type: Annotated[
        str | None, Field(description="Filter by calendar type (e.g. 'leaves')")
    ] = None,
) -> str:
    """List all Confluence calendars."""
    try:
        data = await _get_confluence(ctx).list_calendars()
        if filter_type:
            ft = filter_type.lower()
            data = [
                w
                for w in data
                if ft in w.get("subCalendar", {}).get("typeKey", "").lower()
                or ft in w.get("subCalendar", {}).get("name", "").lower()
            ]
        # Simplify output
        result = []
        for wrapper in data:
            sub = wrapper.get("subCalendar", {})
            children = wrapper.get("childSubCalendars", [])
            result.append(
                {
                    "id": sub.get("id"),
                    "name": sub.get("name"),
                    "type": sub.get("typeKey"),
                    "space_key": sub.get("spaceKey"),
                    "space_name": sub.get("spaceName"),
                    "child_count": len(children),
                    "child_ids": [c.get("subCalendar", {}).get("id") for c in children],
                }
            )
        return _ok(result)
    except Exception as e:
        return _err(e)


@mcp.tool(
    tags={"confluence", "calendars", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def confluence_search_calendars(
    ctx: Context,
    query: Annotated[str, Field(description="Search by calendar name, space name, or space key")],
) -> str:
    """Search Confluence calendars by name or space."""
    try:
        data = await _get_confluence(ctx).list_calendars()
        q = query.lower()
        matched = []
        for wrapper in data:
            sub = wrapper.get("subCalendar", {})
            if (
                q in sub.get("name", "").lower()
                or q in sub.get("spaceName", "").lower()
                or q in sub.get("spaceKey", "").lower()
            ):
                matched.append(
                    {
                        "id": sub.get("id"),
                        "name": sub.get("name"),
                        "type": sub.get("typeKey"),
                        "space_key": sub.get("spaceKey"),
                        "space_name": sub.get("spaceName"),
                    }
                )
        return _ok(matched)
    except Exception as e:
        return _err(e)


@mcp.tool(
    tags={"confluence", "time_off", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def confluence_get_time_off(
    ctx: Context,
    start_date: Annotated[str, Field(description="Start date (YYYY-MM-DD, 'today', '+14d', etc.)")],
    end_date: Annotated[str, Field(description="End date (YYYY-MM-DD, 'today', '+14d', etc.)")],
    calendar_name: Annotated[str | None, Field(description="Filter by calendar name")] = None,
    group_by_person: Annotated[bool, Field(description="Group results by person")] = False,
) -> str:
    """Get time-off events for a date range across all leave calendars."""
    try:
        start = _resolve_date(start_date)
        end = _resolve_date(end_date)
        events = await _get_confluence(ctx).get_time_off_events(start, end, calendar_name)

        if group_by_person:
            grouped: dict[str, list[dict]] = {}
            for e in events:
                name = e["person_name"]
                grouped.setdefault(name, []).append(e)
            return _ok({"start": start, "end": end, "people": grouped})

        return _ok({"start": start, "end": end, "events": events})
    except Exception as e:
        return _err(e)


@mcp.tool(
    tags={"confluence", "time_off", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def confluence_who_is_out(
    ctx: Context,
    date: Annotated[str, Field(description="Date to check (default: 'today')")] = "today",
) -> str:
    """Check who is out on a specific date."""
    try:
        d = _resolve_date(date)
        events = await _get_confluence(ctx).get_time_off_events(d, d)
        people = list({e["person_name"] for e in events})
        return _ok({"date": d, "people_out": people, "count": len(people)})
    except Exception as e:
        return _err(e)


@mcp.tool(
    tags={"confluence", "time_off", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def confluence_get_person_time_off(
    ctx: Context,
    person: Annotated[str, Field(description="Person name to search for")],
    calendar_name: Annotated[str, Field(description="Calendar name to search in")],
    start_date: Annotated[str, Field(description="Start date")],
    end_date: Annotated[str, Field(description="End date")],
) -> str:
    """Get a specific person's time-off events."""
    try:
        start = _resolve_date(start_date)
        end = _resolve_date(end_date)
        all_events = await _get_confluence(ctx).get_time_off_events(start, end, calendar_name)
        person_lower = person.lower()
        matched = [e for e in all_events if person_lower in e["person_name"].lower()]
        return _ok({"person": person, "start": start, "end": end, "events": matched})
    except Exception as e:
        return _err(e)


@mcp.tool(
    tags={"confluence", "time_off", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True},
)
async def confluence_sprint_capacity(
    ctx: Context,
    team_members: Annotated[list[str], Field(description="List of team member names")],
    sprint_start: Annotated[str, Field(description="Sprint start date")],
    sprint_end: Annotated[str, Field(description="Sprint end date")],
    working_days_per_week: Annotated[int, Field(description="Working days per week")] = 5,
) -> str:
    """Calculate sprint capacity considering team time-off."""
    try:
        start = _resolve_date(sprint_start)
        end = _resolve_date(sprint_end)

        # Calculate working days
        start_dt = parse_date(start)
        end_dt = parse_date(end)
        total_days = 0
        current = start_dt
        weekend_days = set(range(5, 7)) if working_days_per_week == 5 else set()
        while current <= end_dt:
            if current.weekday() not in weekend_days:
                total_days += 1
            current += timedelta(days=1)

        # Get time-off events
        all_events = await _get_confluence(ctx).get_time_off_events(start, end)

        member_breakdown = []
        total_days_off = 0

        for member in team_members:
            member_lower = member.lower()
            member_events = [e for e in all_events if member_lower in e["person_name"].lower()]

            # Count unique off-days (within sprint working days)
            off_dates: set[str] = set()
            for event in member_events:
                ev_start = max(parse_date(event["start_date"]), start_dt)
                ev_end = min(parse_date(event["end_date"]), end_dt)
                d = ev_start
                while d <= ev_end:
                    if d.weekday() not in weekend_days:
                        off_dates.add(d.strftime("%Y-%m-%d"))
                    d += timedelta(days=1)

            days_off = len(off_dates)
            total_days_off += days_off
            member_breakdown.append(
                {
                    "member": member,
                    "days_off": days_off,
                    "available_days": total_days - days_off,
                    "events": [
                        {
                            "description": e["description"],
                            "dates": f"{e['start_date']} to {e['end_date']}",
                        }
                        for e in member_events
                    ],
                }
            )

        max_capacity = total_days * len(team_members)
        available = max_capacity - total_days_off
        pct = round((available / max_capacity * 100), 1) if max_capacity > 0 else 0

        return _ok(
            {
                "sprint": {"start": start, "end": end, "working_days": total_days},
                "team": {
                    "members": len(team_members),
                    "max_capacity_days": max_capacity,
                    "total_days_off": total_days_off,
                    "available_capacity_days": available,
                    "capacity_percentage": pct,
                },
                "member_breakdown": member_breakdown,
            }
        )
    except Exception as e:
        return _err(e)
