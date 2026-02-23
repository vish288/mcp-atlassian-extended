# Git-Jira Integration Patterns

## Branch Naming for Auto-Linking

Include Jira issue key in branch name:

```bash
feat/PROJ-123-user-login
fix/PROJ-456-cart-null-crash
```

Key must be uppercase, hyphen-separated from description.

## Smart Commits

```
PROJ-123 #comment Fixed the null check
PROJ-123 #time 1h 30m
PROJ-123 #transition Review
```

Committer email must match Jira account. Commands only in subject line.

## PR/MR Title

Include issue key: `[PROJ-123] Add email login to auth service`

Jira links from: PR title, description, branch name, commit messages.

## Development Panel

Shows: branches, commits, PRs, builds, deployments linked to the ticket.

## Automation Rules

1. PR created with issue key -> transition to Review
2. PR merged -> transition to Test
3. Deployment successful -> transition to Closed

## Field Notes

- **Epic Link**: use `customfield_10008`, NOT `parent` (parent is for subtasks)
- **LOB field**: may be screen-restricted on Task/Epic. Retry without it if creation fails.
- **Select fields** (Privacy, Security): use `{"value": "No"}` not plain string

## Confluence Macros

```
{jira:jql=project = PROJ AND sprint in openSprints()|columns=key,summary,status}
{jira:key=PROJ-123}
```

## Monorepo Linking

When multiple services share one repository:

**Branch naming:** `feat/PROJ-123-service-name-description`

```bash
feat/PROJ-123-auth-service-token-rotation
fix/PROJ-456-payment-service-retry-logic
```

**PR title:** Include service scope: `[PROJ-123][auth-service] Add token rotation`

**Commit scope:** Use Conventional Commits scope for the service:

```
feat(auth-service): add token rotation on session expiry
fix(payment-service): handle retry on 503
```

This ensures Jira can link to the correct ticket, and the service scope provides context for reviewers in a multi-service PR history.

## Stale PR-to-Jira Link Resolution

PRs abandoned >30 days with linked Jira tickets create noise in the Development Panel.

**Cleanup process:**

1. Query: list open PRs with no activity in 30 days
2. For each stale PR:
   - Close the PR with a comment: "Closing stale PR. Reopen if work resumes."
   - Comment on the linked Jira ticket: "PR [#N] closed as stale."
   - If no other active PR exists, transition the Jira ticket back to Committed
3. Run monthly as part of repository hygiene

**Automation rule:**
- Trigger: PR has no commits or comments for 30 days
- Action: Add `stale` label to PR, notify author
- If no response in 7 more days: auto-close PR
