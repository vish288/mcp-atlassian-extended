# Close ticket $issue_key

## Steps

1. **Fetch issue details** — retrieve the current status, description, linked merge requests, and Definition of Done checklist for $issue_key.
2. **Verify Definition of Done** — check each DoD item:
   - Are all acceptance criteria met?
   - Is there evidence for each item (linked MR, test results, documentation)?
   - Mark completed items as checked
3. **Verify linked MR** — check that any linked merge request:
   - Has passed CI pipeline
   - Has been approved
   - Has been merged to the target branch
4. **Check attachments** — use `jira_get_attachments` with issue_key="$issue_key" to verify any required documentation or screenshots are attached.
5. **Transition through statuses** — move the issue through required workflow states:
   - If in "In Progress": transition to "Review"
   - If in "Review": transition to "Test"
   - If in "Test": transition to "Closed"
   - Note: some workflows require sequential transitions
6. **Add closing comment** — summarize what was delivered and link to relevant artifacts.
7. **Verify closure** — confirm the issue is in "Closed" or "Done" status.

## Pre-closure Checklist

- [ ] All DoD items checked
- [ ] Linked MR merged
- [ ] No unresolved blockers
- [ ] Required documentation attached
- [ ] Stakeholders notified (if applicable)
