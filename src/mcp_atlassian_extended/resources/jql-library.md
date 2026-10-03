# JQL Query Library

Replace `PROJ` with your project key. Lines starting with `--` are labels, not JQL —
Jira has no comment syntax, so copy only the query line.

## Sprint Management

```jql
-- Current sprint work
project = PROJ AND sprint in openSprints() ORDER BY status ASC, priority DESC

-- My tickets
project = PROJ AND sprint in openSprints() AND assignee = currentUser()

-- Carry-over candidates
project = PROJ AND sprint in closedSprints() AND status NOT IN (Closed, Done)
  AND sprint NOT IN openSprints()

-- Added mid-sprint: native JQL has no sprint-start function. Use the Jira Sprint
-- Report, which flags issues added after the sprint began. (A startOfSprint()-style
-- function needs a Marketplace app such as JQL Tricks.)
```

## Blocker Detection

```jql
-- Blocked tickets
project = PROJ AND sprint in openSprints() AND labels = "blocked" AND status != Closed

-- Issues linked to ONE ticket by a link type (linkedIssues takes a single key, not a wildcard)
project = PROJ AND issue in linkedIssues("PROJ-123", "blocks") AND status NOT IN (Closed, Done)
-- Listing every ticket that has a "blocks" link project-wide needs a Marketplace app
-- (e.g. ScriptRunner's hasLinks); native JQL cannot express it.
```

## Stale Tickets

```jql
-- In Progress without update (>5 days)
project = PROJ AND status = "In Progress" AND updated < -5d

-- Review without update (>3 days)
project = PROJ AND status = "Review" AND updated < -3d

-- Unassigned in sprint
project = PROJ AND sprint in openSprints() AND assignee is EMPTY AND status != Closed
```

## Workload

```jql
-- Unsized tickets
project = PROJ AND "Story Points" is EMPTY AND status NOT IN (Closed, Done)

-- High-priority unassigned
project = PROJ AND priority IN (Highest, High) AND assignee is EMPTY AND status != Closed
```

## Reporting

```jql
-- Completed this sprint
project = PROJ AND sprint in openSprints() AND status IN (Closed, Done)

-- Bugs this week
project = PROJ AND type = Bug AND created >= startOfWeek()
```

## Operators

| Operator | Example |
|----------|---------|
| `=`, `!=` | `status = "In Progress"` |
| `IN`, `NOT IN` | `status IN (Closed, Done)` |
| `~`, `!~` | `summary ~ "auth"` |
| `is EMPTY` | `assignee is EMPTY` |
| `-Nd` | `updated < -5d` |

## Functions

| Function | Example |
|----------|---------|
| `currentUser()` | `assignee = currentUser()` |
| `openSprints()` | `sprint in openSprints()` |
| `closedSprints()` | `sprint in closedSprints()` |
| `startOfWeek()` | `created >= startOfWeek()` |
| `startOfDay()` | `updated >= startOfDay(-3d)` |

Native date functions cover day/week/month/year only (`startOf…`/`endOf…`); there is no
`startOfSprint()`.

## Query Performance Tips

- Avoid `text ~ "word"` on large instances -- triggers full-text scan across all text fields
- Use indexed fields: `status`, `assignee`, `labels`, `sprint`, `priority`, `issuetype`
- Prefer `=` over `~` when the exact value is known
- Add `ORDER BY` to avoid arbitrary result ordering
- Use `maxResults` parameter when fetching via API to limit payload size
- `project = X` as the first clause narrows the search scope early

**Slow vs fast patterns:**

| Slow | Fast |
|------|------|
| `text ~ "authentication"` | `summary ~ "authentication" AND project = PROJ` |
| `labels is not EMPTY` (then filter client-side) | `labels = "specific-label"` |
| `sprint IN openSprints() AND sprint IN closedSprints()` | Impossible -- simplify logic |

## Saved Filter Management

**Naming convention:** `[Team] - Purpose`

Examples:
- `[Platform] - Blocked tickets in sprint`
- `[Platform] - Carry-over candidates`
- `[QA] - Bugs this week`

**Governance:**
- Share filters via group permissions, not individual users
- Review quarterly: delete unused filters (check "last executed" date)
- Update broken JQL after workflow changes (new statuses, renamed fields)
- Do not create personal filters for queries used in dashboards -- use shared filters
