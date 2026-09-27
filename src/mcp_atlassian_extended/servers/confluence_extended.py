"""Confluence Extended tools — calendars, time-off, sprint capacity."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Annotated

from fastmcp import Context
from pydantic import Field

from . import mcp
from ._helpers import _get_confluence, _ok, _paginated, tool_result


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

    # Beyond the documented keywords, only ISO dates (YYYY-MM-DD) are accepted.
    try:
        return date.fromisoformat(v).strftime("%Y-%m-%d")
    except ValueError:
        msg = (
            f"Unrecognised date {value!r}; use YYYY-MM-DD, 'today', "
            "'tomorrow', '+Nd', '-Nd' or 'next week'"
        )
        raise ValueError(msg) from None


@mcp.tool(
    tags={"confluence", "calendars", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": True},
)
@tool_result
async def confluence_list_calendars(
    ctx: Context,
    filter_type: Annotated[
        str | None, Field(description="Filter by calendar type (e.g. 'leaves')")
    ] = None,
    search: Annotated[
        str | None,
        Field(description="Filter by calendar name, space name, or space key (case-insensitive)"),
    ] = None,
) -> str:
    """List Confluence calendars, optionally narrowed by type or a name/space search."""
    data = await _get_confluence(ctx).list_calendars()
    if filter_type:
        ft = filter_type.lower()
        data = [
            w
            for w in data
            if ft in w.get("subCalendar", {}).get("typeKey", "").lower()
            or ft in w.get("subCalendar", {}).get("name", "").lower()
        ]
    if search:
        q = search.lower()
        data = [
            w
            for w in data
            if any(
                q in w.get("subCalendar", {}).get(k, "").lower()
                for k in ("name", "spaceName", "spaceKey")
            )
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
    return _paginated(result)


@mcp.tool(
    tags={"confluence", "time_off", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": True},
)
@tool_result
async def confluence_get_time_off(
    ctx: Context,
    start_date: Annotated[str, Field(description="Start date (YYYY-MM-DD, 'today', '+14d', etc.)")],
    end_date: Annotated[str, Field(description="End date (YYYY-MM-DD, 'today', '+14d', etc.)")],
    calendar_name: Annotated[str | None, Field(description="Filter by calendar name")] = None,
    person: Annotated[
        str | None,
        Field(description="Return only this person's events (exact, case-insensitive name match)"),
    ] = None,
    group_by_person: Annotated[bool, Field(description="Group results by person")] = False,
) -> str:
    """Get time-off events for a date range across all leave calendars.

    Pass ``person`` for one person's events, or a single day for ``start_date`` and
    ``end_date`` to see who is out on that day.
    """
    start = _resolve_date(start_date)
    end = _resolve_date(end_date)
    events = await _get_confluence(ctx).get_time_off_events(start, end, calendar_name)

    if person:
        pl = person.lower()
        events = [e for e in events if e["person_name"].lower() == pl]

    if group_by_person:
        grouped: dict[str, list[dict]] = {}
        for e in events:
            name = e["person_name"]
            grouped.setdefault(name, []).append(e)
        return _ok({"start": start, "end": end, "people": grouped})

    return _ok({"start": start, "end": end, "events": events})


@mcp.tool(
    tags={"confluence", "time_off", "read"},
    annotations={"readOnlyHint": True, "idempotentHint": True, "openWorldHint": True},
)
@tool_result
async def confluence_sprint_capacity(
    ctx: Context,
    team_members: Annotated[list[str], Field(description="List of team member names")],
    sprint_start: Annotated[str, Field(description="Sprint start date")],
    sprint_end: Annotated[str, Field(description="Sprint end date")],
    working_days_per_week: Annotated[
        int, Field(description="Working days per week", ge=1, le=7)
    ] = 5,
) -> str:
    """Calculate sprint capacity considering team time-off."""
    start = _resolve_date(sprint_start)
    end = _resolve_date(sprint_end)

    # Calculate working days
    start_dt = date.fromisoformat(start)
    end_dt = date.fromisoformat(end)
    total_days = 0
    current = start_dt
    # Map working_days_per_week to non-working weekdays.
    # 7=all days, 6=skip Sun, 5=skip Sat+Sun, 4=skip Fri+Sat+Sun, etc.
    weekend_days = set(range(working_days_per_week, 7))
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
        # Exact match: a substring test counts John's leave for member "Jo" too.
        member_events = [e for e in all_events if e["person_name"].lower() == member_lower]

        # Count unique off-days (within sprint working days)
        off_dates: set[str] = set()
        for event in member_events:
            ev_start = max(date.fromisoformat(event["start_date"]), start_dt)
            ev_end = min(date.fromisoformat(event["end_date"]), end_dt)
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
