# Jira Issue Hierarchy

## Structure

```
Epic (measurable outcome, spans sprints)
  +-- Story (user-facing deliverable, fits in one sprint)
       +-- Task (technical unit of work, no direct user story)
            +-- Subtask (atomic action within a Task)
  +-- Bug (defect against a Story or standalone)
  +-- Spike (time-boxed research, produces knowledge not code)
```

## Type Definitions

| Type | Delivers | Fits in Sprint | Example |
|------|----------|---------------|---------|
| Epic | Measurable outcome | No (multi-sprint) | Reduce checkout abandonment by 15% |
| Story | User-facing capability | Yes (8 pts max) | User can save address for future orders |
| Task | Technical work | Yes | Migrate session store from Redis 6 to 7 |
| Subtask | Atomic piece of Task | Yes (child of Task) | Write migration script for key format |
| Bug | Defect fix | Yes | Cart total shows negative after coupon |
| Spike | Research output | Yes (time-boxed) | Evaluate WebSocket vs SSE |

## When to Use Each Type

- **Epic**: business objective, not feature list. Must have: objective, measurable outcome, time bound, out of scope, dependencies
- **Story**: answers "as a [user], I can [do something] so that [benefit]". Max 8 points.
- **Task**: technical work without user story. Still requires verifiable acceptance criteria.
- **Subtask**: use sparingly. Only when parallel work within a Task requires separate assignees. If >5 subtasks, the Task is too large.
- **Bug**: link to the Story/Epic it breaks. Always include: steps to reproduce, expected vs actual, severity.
- **Spike**: time-boxed 1-3 days. Deliverable is recommendation, not code. Creates follow-up tickets.

## Splitting Rules

| Signal | Action |
|--------|--------|
| Story estimated at 13+ points | Split into 2-3 smaller Stories |
| Task has 6+ subtasks | Split into multiple Tasks |
| Epic has no clear measurable outcome | Redefine or split |

How to split:
1. By user workflow step
2. By data entity
3. By platform/environment
4. By acceptance criterion
5. By happy path vs edge cases

Anti-patterns: splitting by technical layer (not independently shippable), "Part 1/Part 2" (each must deliver value), subtasks as mini-Stories.

## Hierarchy Linking

| Relationship | How |
|-------------|-----|
| Story/Task -> Epic | Epic Link field (`customfield_10008`), NOT `parent` |
| Subtask -> Task | Standard parent field |
| Bug -> Story/Epic | Epic Link or `relates to` link |
| Spike -> Story | `relates to` link |

## Cross-Epic Work Patterns

When a Story touches work tracked under multiple Epics:

1. **Single-owner rule** -- the Story lives under one Epic (the primary deliverable)
2. Link to the other Epic(s) with `relates to`
3. If overlap is significant, create a tracking Story in each secondary Epic referencing the primary
4. Do not duplicate acceptance criteria across tracking Stories -- point to the source

**Initiative-level tracking** (multiple Epics forming a theme):
- Use Jira labels (e.g., `initiative:checkout-revamp`) to group Epics
- JQL: `issuetype = Epic AND labels = "initiative:checkout-revamp"`
- Create a Confluence page as the initiative dashboard
- Review initiative progress at the monthly product sync, not sprint ceremonies

## 13-Point Story Decomposition

A 13-point Story signals too many unknowns or too much scope. Decompose before sprint entry.

1. List every acceptance criterion on the Story
2. For each criterion, ask: "Can this ship independently and deliver user value?"
3. Group criteria by user workflow step (e.g., form entry, validation, confirmation)
4. Create one child Story per independent group -- each must have its own user story sentence
5. Verify each child is 1-8 points. If any child is still 8, check whether it splits further
6. Re-estimate children with the team (do not divide the original 13 mathematically)
7. Link children to the same Epic; close the original 13-point Story

| Check | Pass? |
|-------|-------|
| Each child delivers value on its own | |
| No child is just a technical layer (frontend-only, backend-only) | |
| Each child has testable acceptance criteria | |
| Children can be worked in parallel by different developers | |

## Bug vs Task Decision Tree

| Condition | Type | Rationale |
|-----------|------|-----------|
| User-reported defect against existing feature | Bug | Tracks regression/defect metrics |
| Test failure on previously passing feature | Bug | Regression -- needs root cause |
| Internal tech improvement (refactor, cleanup) | Task | No user-facing defect |
| Library/framework upgrade or migration | Task | Planned technical work |
| Missing feature reported as "broken" | Story | New capability, not a defect |
| Performance degradation vs documented SLA | Bug | Measurable regression |
| Performance improvement without existing SLA | Task | Enhancement, not defect |
| Security vulnerability (CVE, pen test finding) | Bug | Defect in security posture |
| Flaky test stabilization | Task | Internal quality improvement |
