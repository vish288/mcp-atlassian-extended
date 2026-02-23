# Definition of Done Checklists

## Story DoD

```
[ ] Code reviewed and approved (1+ approval)
[ ] All acceptance criteria verified
[ ] Unit tests written and passing (>=90% on new code)
[ ] Integration / E2E tests updated if applicable
[ ] No new linting or type errors
[ ] Feature flag added if behind flag
[ ] Documentation updated if applicable
[ ] Deployed to staging and smoke-tested
[ ] Accessibility checked (WCAG 2.1 AA) if UI change
[ ] Security review if PII or auth changes
[ ] PR merged and branch deleted
[ ] Ticket transitioned
```

## Bug DoD

```
[ ] Root cause identified and documented
[ ] Fix addresses root cause, not symptoms
[ ] Regression test added
[ ] All existing tests passing
[ ] Code reviewed and approved
[ ] Verified in staging
[ ] PR merged and branch deleted
```

## Task DoD

```
[ ] Acceptance criteria met
[ ] Code reviewed and approved
[ ] Tests added/updated
[ ] No regressions (CI green)
[ ] Documentation updated if applicable
[ ] PR merged and branch deleted
```

## DoD Management Rules

### Read-Before-Write

1. Fetch existing DoD items first
2. Preserve all existing items -- never overwrite
3. Mark completed items as checked
4. Only append genuinely new criteria
5. Implementation evidence belongs in comments, not DoD

### What Belongs Where

| DoD | Comments |
|-----|----------|
| "Unit tests passing" | "Added 12 tests in auth.test.ts" |
| "Security review done" | "Reviewed with @lead, no concerns" |

### Enforcement

Before closing: verify every DoD item checked, criteria met, PR merged, no open threads. Some workflows gate Closed on DoD completion.

## Conditional DoD Items

Some DoD items only apply to certain types of changes:

| Condition | DoD Item |
|-----------|----------|
| UI change | Accessibility checked (WCAG 2.1 AA) |
| PII or auth change | Security review completed |
| API change | API documentation updated |
| Database change | Migration tested with rollback |
| Feature flag added | Flag cleanup ticket created |

**Naming convention:** Prefix conditional items with the condition:
```
[If UI] Accessibility verified against WCAG 2.1 AA
[If API] OpenAPI spec updated
[If DB] Migration and rollback tested in staging
```

This avoids confusion about which items are required for each ticket.

## DoD vs Deliverable Mismatch Detection

Signs the DoD doesn't match the actual work:

| Signal | Problem | Fix |
|--------|---------|-----|
| DoD items reference features not in the PR | Copy-pasted from another ticket | Rewrite DoD to match this ticket's scope |
| PR changes files not covered by any DoD item | DoD is incomplete | Add missing DoD items before merging |
| DoD has 15+ generic items | Boilerplate, not ticket-specific | Trim to items that are verifiable for this change |
| Placeholder text remains ("[If applicable]") | DoD was not reviewed | Fill in or remove all placeholders |

Review DoD during sprint planning, not at merge time. Catching mismatches early avoids last-minute rework.
