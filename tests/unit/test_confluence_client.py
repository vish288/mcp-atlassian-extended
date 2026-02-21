"""Tests for Confluence Extended client."""

from __future__ import annotations

import httpx
import pytest
import respx

from mcp_atlassian_extended.clients.confluence import ConfluenceExtendedClient
from mcp_atlassian_extended.config import ConfluenceConfig

BASE = "https://confluence.example.com"


def _make_client() -> ConfluenceExtendedClient:
    return ConfluenceExtendedClient(ConfluenceConfig(url=BASE, token="test-token"))


class TestConfluenceClient:
    @pytest.mark.asyncio
    async def test_list_calendars(self):
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "payload": [
                            {
                                "subCalendar": {
                                    "id": "cal-1",
                                    "name": "Team Calendar",
                                    "typeKey": "events",
                                },
                                "childSubCalendars": [],
                            }
                        ]
                    },
                )
            )
            client = _make_client()
            result = await client.list_calendars()
            assert len(result) == 1
            assert result[0]["subCalendar"]["name"] == "Team Calendar"

    @pytest.mark.asyncio
    async def test_get_leave_calendars(self):
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/calendar-services/1.0/calendar/subcalendars.json").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "payload": [
                            {
                                "subCalendar": {
                                    "id": "cal-1",
                                    "name": "Team Vacation",
                                    "typeKey": "leaves",
                                },
                                "childSubCalendars": [],
                            },
                            {
                                "subCalendar": {
                                    "id": "cal-2",
                                    "name": "Sprint Events",
                                    "typeKey": "events",
                                },
                                "childSubCalendars": [],
                            },
                        ]
                    },
                )
            )
            client = _make_client()
            result = await client.get_all_leave_calendars()
            assert len(result) == 1
            assert result[0]["subCalendar"]["name"] == "Team Vacation"

    @pytest.mark.asyncio
    async def test_get_events(self):
        async with respx.mock(base_url=BASE) as router:
            router.get("/rest/calendar-services/1.0/calendar/events.json").mock(
                return_value=httpx.Response(
                    200,
                    json={
                        "events": [
                            {
                                "id": "e1",
                                "title": "PTO",
                                "eventType": "leaves",
                                "start": "2026-03-01",
                                "end": "2026-03-05",
                            }
                        ]
                    },
                )
            )
            client = _make_client()
            result = await client.get_events(["cal-1"], "2026-03-01", "2026-03-31")
            assert len(result) == 1
            assert result[0]["title"] == "PTO"
