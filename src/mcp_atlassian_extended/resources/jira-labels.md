# Jira Label Taxonomy

## Standard Labels

| Label | Use when |
|-------|---------|
| `tech-debt` | Refactoring without user-visible change |
| `security` | Auth, data handling, CVE fixes |
| `accessibility` | a11y improvements |
| `performance` | Latency, bundle size |
| `breaking-change` | Impacts downstream consumers |
| `spike` | Time-boxed research |
| `blocked` | Blocked by external dependency |
| `quick-win` | <2 hours, good for slack time |
| `regression` | Reintroduces previously fixed behavior |

## Naming Rules

1. Lowercase, hyphen-separated: `tech-debt`
2. No duplicates (search first)
3. No status labels (`in-progress` -> use workflow)
4. No priority labels (`urgent` -> use Priority field)
5. No sprint labels (`sprint-14` -> use Sprint field)

## Governance

- Assign label owner (TPM or tech lead)
- Quarterly cleanup: remove labels with <3 uses in 6 months
- Before creating: check existing labels, follow naming rules

## JQL

```jql
labels = "tech-debt" AND sprint in openSprints()
labels = "blocked" AND sprint in openSprints() AND status != Closed
labels = "security" AND created >= startOfQuarter()
```

## Label Deprecation Strategy

Process to retire unused labels:

1. **Identify candidates**: JQL `labels = "old-label"` -- if <3 uses in 6 months, candidate for deprecation
2. **Announce**: Post in team channel with 2-sprint notice period
3. **Bulk-remove**: After notice period, use automation or bulk change to remove the label from all tickets
4. **Delete**: Remove the label from Jira (or hide if deletion is not allowed)
5. **Document**: Record deprecated labels and their replacements in team wiki

**JQL to find low-use labels:**

```jql
labels = "candidate-label" AND updated >= -180d
```

If the result count is <3, the label is a deprecation candidate.

## Synonym Detection

Common label duplicates that create signal noise:

| Labels | Canonical | Action |
|--------|-----------|--------|
| `tech-debt`, `refactor`, `cleanup` | `tech-debt` | Bulk-relabel, delete synonyms |
| `urgent`, `critical`, `p0` | None -- use Priority field | Remove all, train team on Priority |
| `frontend`, `fe`, `ui` | `frontend` | Standardize |

**Detection method:**
1. Export all labels with usage counts
2. Group by semantic meaning
3. For each group, pick the canonical label (most used, most descriptive)
4. Bulk-replace synonyms with canonical label
