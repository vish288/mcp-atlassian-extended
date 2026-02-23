# Sprint Hygiene Rules

## Definition of Ready

A ticket must meet all of these before entering a sprint:

- Summary follows format
- Description populated with template
- Acceptance criteria written and testable
- Story points estimated by team
- Dependencies identified and linked
- No unresolved questions
- Design reviewed if applicable
- Priority set by product owner

## WIP Limits

| Team size | Max WIP per person |
|-----------|-------------------|
| 1-3 | 1 |
| 4-6 | 1-2 |
| 7+ | 1 (strictly enforced) |

Finish before starting. Blocked tickets count toward WIP.

## Refinement

- Refine 1-2 sprints ahead (not more)
- 5-10% of sprint capacity for refinement
- Use Fibonacci: 1, 2, 3, 5, 8, 13
- 13-point stories must decompose before sprint entry

## Carry-Over Policy

| Sprint | Action |
|--------|--------|
| 2nd sprint | Re-estimate, add comment |
| 3rd sprint | Mandatory team discussion -- split, descope, or escalate |
| 4th sprint | Escalate to product owner |

## Mid-Sprint Rules

- No tickets added without sizing
- Adding requires removing equal points
- Blocked tickets need: comment, label, linked blocker
- Remove `blocked` label immediately when unblocked

## Sprint Goal

One sentence describing the primary outcome. Not a list of tickets.

Good: "Users can complete checkout with saved addresses"
Bad: "Complete PROJ-123, PROJ-124, PROJ-125"

## Blocked Tickets in WIP Calculation

Blocked tickets count toward WIP limits. A developer with 1 blocked ticket and 1 active ticket is at WIP=2.

**Escalation timeline:**

| Day | Action |
|-----|--------|
| Day 1 | Add `blocked` label, comment with blocker details, link blocking ticket |
| Day 3 | Escalate to team lead / scrum master in standup |
| Day 5 | Sprint scope review: swap blocked ticket out, pull replacement from backlog |
| Day 7+ | Escalate to product owner and dependent team's manager |

Rules:
- Do not start new work to "stay busy" while blocked -- help unblock or pick up another in-progress ticket
- If the blocker is external, document the contact person and expected resolution date
- Remove `blocked` label immediately when unblocked -- stale labels corrupt WIP metrics

## PTO Capacity Adjustment

**Formula:**

```
adjusted_capacity = (team_size - (total_PTO_days / sprint_days)) * avg_velocity_per_person
```

Where `avg_velocity_per_person = team_avg_velocity / team_size` over last 3 sprints.

**Example:**

| Variable | Value |
|----------|-------|
| Team size | 5 developers |
| Sprint length | 10 days (2 weeks) |
| Team avg velocity (last 3 sprints) | 40 points |
| Avg velocity per person | 40 / 5 = 8 points |
| PTO this sprint | Dev A: 5 days, Dev B: 2 days = 7 days total |
| Adjusted capacity | (5 - 7/10) * 8 = 4.3 * 8 = 34.4 points |
| Sprint commitment | 34 points (round down) |

On-call rotation counts as 50% PTO (reduced focus, not zero).
