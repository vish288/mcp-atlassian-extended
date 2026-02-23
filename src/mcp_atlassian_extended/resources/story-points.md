# Story Point Estimation

## Fibonacci Scale

| Points | Complexity | Unknowns | Example |
|--------|-----------|----------|---------|
| 1 | Trivial | None | Fix typo, update config |
| 2 | Small | Minimal | Add form field, update API response |
| 3 | Moderate, 1-2 integration points | Some | New API endpoint with tests |
| 5 | Significant, multiple parts | Moderate | Third-party integration |
| 8 | Large, cross-cutting | High | DB migration with backfill |
| 13 | Too large | Very high | Must decompose |

## Planning Poker

1. PO presents ticket
2. Team asks questions (3 min)
3. Simultaneous vote
4. If within 1 Fibonacci: accept
5. If >2 gap: discuss, re-vote once
6. Still divergent: use higher estimate or create spike

Rules: everyone votes, simultaneous reveal, no averaging.

## What Points Do NOT Measure

- Hours (senior may take 3h, junior 2 days -- same estimate)
- Lines of code (1-point rename may touch 50 files)
- Individual performance
- Value

## Velocity

- Track over 3-5 sprints for reliable baseline
- Use for capacity planning, not performance measurement
- Never compare across teams
- Investigate if drops >30% for 2+ sprints

## Estimation Disagreement Resolution

After Planning Poker:

| Scenario | Action |
|----------|--------|
| Votes within 1 Fibonacci step (e.g., 3 and 5) | Use higher estimate |
| Votes span 2+ steps (e.g., 2 and 8) | Discuss unknowns for 3 minutes |
| Still divergent after discussion | High voter explains risk; low voter explains assumptions |
| Third round still divergent | Create a spike to reduce unknowns; estimate after spike |

Rules:
- Never average (3.5 is not a Fibonacci number)
- Never pressure toward the lower estimate
- If one person has domain knowledge others lack, weight their input in discussion (not their vote)

## Spike-Based Estimation

Create a spike before estimating when:
- Technology is unfamiliar to >50% of the team
- Integration point is unclear (e.g., undocumented third-party API)
- 3+ team members disagree by 2+ Fibonacci steps
- The ticket has been re-estimated 2+ times without convergence

**Spike output:**
1. Written recommendation with evidence
2. Revised estimate for the original ticket
3. Any scope changes discovered during investigation
4. Follow-up tickets if the spike reveals additional work
