# Jira Workflow & Automation

## Standard Workflow

```
Triage -> Committed -> In Progress -> Review -> Test -> Closed
```

| Status | Entry criteria | Exit criteria |
|--------|---------------|---------------|
| Triage | Ticket created | Prioritized, assigned |
| Committed | Accepted for sprint | Developer picks up |
| In Progress | Developer working | Code complete, PR opened |
| Review | PR open, CI green | Threads resolved, approved |
| Test | Merged, deployed to staging | QA verified |
| Closed | All DoD items checked | Complete |

Forward only in normal flow. Back transitions allowed with comment.

## Transition Triggers

| When | Transition |
|------|-----------|
| Start working | Committed -> In Progress |
| Open PR/MR | In Progress -> Review |
| PR merged | Review -> Test |
| QA sign-off | Test -> Closed |

## Automation Patterns

1. **Auto-transition on branch**: Branch matching `*/PROJ-*` -> In Progress
2. **Auto-transition on PR**: PR created with issue key -> Review
3. **Auto-close subtasks**: Parent closed -> close all subtasks
4. **Stale ticket alert**: In Progress >5 days -> comment + label
5. **Blocker escalation**: `blocked` label added -> Slack notification

## Governance

- 5-7 statuses maximum
- Same workflow across issue types (except Epic-only statuses)
- Map every status to clear ownership
- Review quarterly

## Invalid Transition Recovery

When a ticket is stuck in the wrong status:

1. Check available transitions: `GET /rest/api/2/issue/{key}/transitions`
2. If the target status is available, transition directly
3. If not, check whether intermediate statuses unlock it (e.g., must pass through Review before Test)
4. Add a comment explaining why the back-transition was needed
5. If no valid transition path exists, contact Jira admin

**Common stuck scenarios:**

| Stuck in | Want | Fix |
|----------|------|-----|
| Review | In Progress (reopen) | Transition back with comment: "Reopened: additional requirements identified" |
| Closed | In Progress | Some workflows block this. Create a new ticket with `relates to` link |
| Test | Review | Transition back: "QA found regression, returning to Review" |

## Workflow Variations by Issue Type

| Status | Epic | Story | Bug | Task | Spike |
|--------|------|-------|-----|------|-------|
| Triage | Yes | Yes | Yes | Yes | Yes |
| Committed | Yes | Yes | Yes | Yes | Yes |
| In Progress | Yes | Yes | Yes | Yes | Yes |
| Review | No | Yes | Yes | Yes | No |
| Test | No | Yes | Yes | Yes | No |
| Closed | Yes | Yes | Yes | Yes | Yes |

- **Epic**: No Review/Test (Epics track outcomes, not code). May have a "Release" status.
- **Bug**: May add "Reproduce" step between Triage and Committed.
- **Spike**: Ends at Closed after delivering recommendation. No Review/Test since output is a document.
