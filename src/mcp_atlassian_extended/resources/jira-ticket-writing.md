# Jira Ticket Writing Standards

## Summary Line

Format: `[Component] Imperative description under 80 characters`

```
Good:
  [Auth] Add refresh token rotation on session expiry
  [Checkout] Fix shipping estimate rounding for CA provinces

Bad:
  Updated the auth logic
  Bug fix
```

Rules:
- Start with imperative verb: Add, Fix, Remove, Migrate, Refactor, Update, Expose
- Component prefix in brackets when team has multiple components
- Under 80 characters
- No "WIP", "TODO", "temp" in active sprint summaries
- No ALL CAPS urgency markers -- use priority field

## Description Templates

Use Jira wiki markup (not markdown) in descriptions and comments.

### Story

```
h3. Context / Problem
[Why this work exists.]

h3. User Story
As a [role], I want [capability] so that [benefit].

h3. Acceptance Criteria
* Given [precondition], when [action], then [outcome]

h3. Out of Scope
* [Explicit exclusions]

h3. Technical Notes
[Optional: architecture decisions, constraints]
```

### Bug

```
h3. Steps to Reproduce
1. Navigate to [URL]
2. [Action]

h3. Expected Behavior
[What should happen]

h3. Actual Behavior
[What happens instead]

h3. Environment
* Browser / OS: [e.g. Chrome 121, macOS 14]
* Version: [e.g. v2.4.1]

h3. Severity
[Critical | High | Medium | Low -- justification]
```

### Task

```
h3. Context
[Why this technical work is needed.]

h3. Scope
* [Action 1]
* [Action 2]

h3. Acceptance Criteria
* [Verifiable condition 1]

h3. Out of Scope
* [Exclusions]
```

### Spike

```
h3. Question
[Specific question to answer.]

h3. Time Box
[Max 1-3 days]

h3. Deliverables
* Written recommendation
* Follow-up tickets for implementation
```

## Comment Policy

Comments are for decisions and reasoning, not status updates.

Good: "Chose server-side invalidation over client-side expiry for compliance. Client-side has 15-min window."
Bad: "Working on this." / "Almost done." / "Done."

Structure: brief context + bullet evidence + next steps.
Use Jira wiki markup with real newlines (no escaped sequences).

## Insufficient Context Escalation

Do not start work on a ticket that lacks actionable detail. Push back when:

| Signal | Action |
|--------|--------|
| No acceptance criteria | Ask PO to add before sprint entry |
| Vague directive ("make it better", "improve UX") | Request measurable outcome |
| No user story or problem statement | Ask "who benefits and how?" |
| Missing reproduction steps (Bug) | Return to reporter with template |
| Conflicting requirements in description vs comments | Flag contradiction, request PO resolution |

**Escalation template** (post as Jira comment):

```
h3. Blocked: Insufficient Context

This ticket cannot be started because:
* [Specific missing information]

To unblock, please provide:
* [Specific ask 1]
* [Specific ask 2]

Moving back to *Committed* until context is available.
```

Rules:
- Do not silently interpret vague requirements -- wrong assumptions cost more than a 1-day delay
- Escalate within 24 hours of picking up the ticket, not at end of sprint
- If PO does not respond within 2 days, raise in standup and consider swapping the ticket out

## Research Spike Template

Spikes are time-boxed investigations that produce knowledge, not code.

```
h3. Question
[Single, specific question this spike will answer.]

h3. Constraints
* Time box: [1-3 days]
* Must evaluate: [minimum options to compare]
* Out of scope: [what this spike will NOT investigate]

h3. Deliverables
* Written recommendation (Confluence page or Jira comment)
* Follow-up tickets created for chosen approach
* Estimate for follow-up work

h3. Decision Criteria
|| Criterion || Weight ||
| Performance impact | High |
| Implementation effort | Medium |
| Maintenance burden | Medium |
```
