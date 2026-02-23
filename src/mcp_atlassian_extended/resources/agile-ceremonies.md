# Agile Ceremony Standards

## Sprint Planning

**Timebox**: 2h max (2-week sprint), 1h (1-week)

1. Sprint goal (10 min)
2. Backlog review (30 min) -- confirm Definition of Ready
3. Capacity check (10 min) -- PTO, on-call
4. Commitment (30 min) -- team pulls tickets
5. Task breakdown (30 min)

Plan to 80% capacity. Team commits, not PO.

## Daily Standup

**Timebox**: 15 min hard stop.

Each person:
1. What will I work on today?
2. Am I blocked?

Alternative: walk the board right-to-left. No problem-solving -- take offline.

## Sprint Review (Demo)

**Timebox**: 1h max (2-week), 30 min (1-week)

1. Goal recap (5 min)
2. Demos (30-40 min) -- working software, not slides
3. Stakeholder feedback (15 min)
4. Metrics (5 min)

Only demo completed work (passes DoD).

## Retrospective

**Timebox**: 45-60 min (2-week), 30 min (1-week)

Formats: Start/Stop/Continue, 4Ls, Mad/Sad/Glad, Sailboat

1. Review previous action items (10 min)
2. Gather observations (15 min)
3. Vote on themes (5 min)
4. Generate actions (15 min) -- max 2-3 items
5. Assign owners (5 min)

Rules: what's said stays, no blame, actionable items only, rotate facilitator.

## Async Standup Formats

For distributed or remote-first teams:

**Slack-based standup:**
- Post by 10am local time in the team channel
- Format: "Working on: / Blocked by: / Will finish:"
- Thread replies for discussion -- keep the main channel scannable
- Bot reminder at 9:45am for missing updates
- Scrum master reviews threads by 11am, escalates blockers

**Written standup template:**

```
*Working on:* PROJ-123 — implementing auth flow
*Blocked by:* Waiting on SRE for staging access (day 2)
*Will finish:* PROJ-123 code complete by EOD
```

Rules:
- No "Working on it" without a ticket reference
- Blocked items must include how many days blocked
- If you have nothing to report, say so -- silence is ambiguous

## Distributed Team Time Zones

Ceremony scheduling for multi-timezone teams:

| Ceremony | Scheduling rule |
|----------|----------------|
| Sprint planning | Overlap hours (mandatory sync) |
| Daily standup | Async for >6h TZ spread; sync for <=6h |
| Sprint review | Record and share async; live Q&A in overlap hours |
| Retrospective | Must be synchronous -- rotate friendly hours quarterly |

**Max 6-hour TZ spread for synchronous ceremonies.** Beyond that:
- Use async standups (Slack/written)
- Record sprint demos for async viewing
- Schedule retros at alternating times to share the inconvenience
