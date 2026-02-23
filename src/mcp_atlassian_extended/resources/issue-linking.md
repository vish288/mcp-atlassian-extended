# Issue Linking Best Practices

## Link Types

| Link type | Meaning | When to use |
|-----------|---------|-------------|
| `blocks` / `is blocked by` | Hard dependency | Technical prerequisite |
| `relates to` | Soft dependency | Cross-team awareness |
| `duplicates` | Same issue reported twice | Close one, keep other |
| `covers` / `is covered by` | Supersedes | Newer ticket covers older |
| `clones` | Copy to another project | Cross-project mirroring |

## Rules

### `blocks` Links
- Always add a comment explaining why
- Blocking ticket should be in same or earlier sprint
- If blocker is in another team's backlog, escalate immediately
- Remove links when dependency is resolved

### `relates to` Links
- Cross-team awareness without hard dependency
- Do not overuse -- if everything "relates to" everything, links add no signal

### `duplicates` Links
- Close the duplicate, keep the original (more context)
- Transfer unique context before closing

### `covers` Links
- Close superseded ticket with comment
- Transfer uncompleted DoD items to covering ticket

## Cross-Team Patterns

Create tickets in both projects and link with `relates to`. Add banner panels:

```
{panel:title=Cross-Team Dependency|borderStyle=solid|borderColor=#FF5630}
This ticket depends on work from [Partner Team|PARTNER-200].
Contact: @sre-lead
{panel}
```

## Cleanup

- Sprint retro: review all `blocks` links
- Ticket closure: resolve all outgoing links
- Epic closure: verify all children closed or moved

## Circular Dependency Detection

How to spot: A blocks B, B blocks C, C blocks A.

**JQL to find potential cycles:**

```jql
project = PROJ AND issue in linkedIssues("PROJ-*", "is blocked by") AND issue in linkedIssues("PROJ-*", "blocks")
```

This finds tickets that both block and are blocked by others -- potential cycle members.

**Resolution:**
1. Map the full dependency chain on a whiteboard or Confluence page
2. Identify the weakest link (the dependency that could be eliminated via feature flags or interface contracts)
3. Break that link: convert `blocks` to `relates to`, add a comment explaining the decoupling approach
4. Create a shared prerequisite ticket if the dependency is on shared infrastructure

## Breaking Hard Dependencies

When two tickets genuinely block each other's progress:

| Strategy | When to use |
|----------|-------------|
| Feature flags | Ship both behind flags, remove coupling from deploy order |
| Interface contracts | Agree on API shape, implement independently against the contract |
| Shared spike | 1-day time-box where both teams align on the integration point |
| Mock/stub | Blocked team builds against a mock, integrates when blocker resolves |
| Vertical slice | Redefine scope so each ticket delivers an independent vertical slice |

Anti-pattern: leaving `blocks` links in place across sprints without escalation. If a blocker persists >1 sprint, it needs management attention.
