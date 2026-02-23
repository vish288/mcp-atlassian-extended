# JQL Query Library

Replace `PROJ` with your project key.

## Sprint Management

```jql
-- Current sprint work
project = PROJ AND sprint in openSprints() ORDER BY status ASC, priority DESC

-- My tickets
project = PROJ AND sprint in openSprints() AND assignee = currentUser()

-- Carry-over candidates
project = PROJ AND sprint in closedSprints() AND status NOT IN (Closed, Done)
  AND sprint NOT IN openSprints()

-- Added mid-sprint
project = PROJ AND sprint in openSprints() AND created > startOfSprint()
```

## Blocker Detection

```jql
-- Blocked tickets
project = PROJ AND sprint in openSprints() AND labels = "blocked" AND status != Closed

-- Tickets blocking others
project = PROJ AND issue in linkedIssues("PROJ-*", "blocks") AND status NOT IN (Closed, Done)
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
| `startOfWeek()` | `created >= startOfWeek()` |
| `startOfSprint()` | `created > startOfSprint()` |

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
| `labels IN labelsOfIssue("PROJ-1")` | `labels = "specific-label"` |
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
