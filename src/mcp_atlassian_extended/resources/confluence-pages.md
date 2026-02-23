# Confluence Page Templates

All templates use Confluence wiki markup.

## ADR (Architecture Decision Record)

```
h1. ADR-NNN: [Decision Title]

|| Field || Value ||
| Status | Proposed / Accepted / Deprecated / Superseded |
| Date | YYYY-MM-DD |
| Deciders | @name1, @name2 |

h2. Context
[What motivates this decision?]

h2. Decision
[State the decision. Active voice.]

h2. Alternatives Considered
|| Option || Pros || Cons ||
| Option A | ... | ... |
| Option B (chosen) | ... | ... |

h2. Consequences
h3. Positive
* [Benefit]

h3. Negative
* [Tradeoff]
```

## RFC (Request for Comments)

```
h1. RFC: [Proposal Title]

|| Field || Value ||
| Author | @name |
| Status | Draft / In Review / Approved / Rejected |
| Deadline | YYYY-MM-DD |

h2. Problem Statement
[What and why?]

h2. Proposal
[Detailed solution]

h2. Alternatives
|| Alternative || Why not? ||

h2. Open Questions
* [Question -- owner, deadline]

h2. Success Criteria
* [Measurable criterion]
```

## Runbook

```
h1. Runbook: [Service Name]

{panel:title=Quick Reference|borderStyle=solid}
* Service: [name]
* Owner: @team
* Dashboard: [link]
* Logs: [link]
{panel}

h2. Prerequisites
* Access to [system]

h2. Procedures
h3. Procedure 1: [Name]
# Step 1
# Step 2

h2. Rollback
# [rollback steps]

h2. Escalation
|| Level || Contact || When ||
| L1 | @on-call | First 15 min |
| L2 | @lead | 30 min |
```

## Retrospective

```
h1. Sprint [N] Retro -- YYYY-MM-DD

h2. What Went Well
* [item]

h2. What Didn't
* [item]

h2. Action Items
|| Action || Owner || Deadline || Status ||
| [action] | @name | date | Open |
```

## DACI

```
h1. DACI: [Decision Title]

|| Role || Person ||
| Driver | @name |
| Approver | @name |
| Contributors | @name1, @name2 |
| Informed | @name1, @name2 |

h2. Options
h3. Option A
* Pros / Cons / Effort / Risk

h2. Recommendation
[Driver's recommendation]

h2. Decision
[Filled after review]
```

## Meeting Notes

```
h1. [Type] -- YYYY-MM-DD

|| Attendees || @name1, @name2 ||

h2. Agenda
# [topic]

h2. Decisions
* [Decision -- by @name]

h2. Action Items
|| Action || Owner || Deadline ||
| [action] | @name | date |
```

## Template Maintenance Strategy

Templates drift as processes change. Keep them current:

- Version templates with a date suffix: `[Template v2024-Q3]`
- When updating, deprecate the old version with a banner:
  ```
  {panel:title=Deprecated|borderStyle=solid|borderColor=#FF5630}
  This template version is deprecated. Use [Template v2024-Q4|SPACE:Template v2024-Q4] instead.
  {panel}
  ```
- Review quarterly: update examples, remove outdated references, verify wiki markup renders correctly
- Assign a template owner per team who is responsible for updates
- Track template versions in a Confluence table of contents page

## Common Template Mistakes

Anti-patterns when using templates:

| Mistake | Impact | Fix |
|---------|--------|-----|
| Using template headings without filling content | Published page has "[What motivates this decision?]" placeholder | Review before publishing; remove all `[placeholder]` text |
| Wrong template for document type | ADR template used for a meeting note | Match template to purpose: ADR = architectural decision, RFC = proposal for feedback |
| Copy-pasting template into existing page | Formatting conflicts, duplicate headings | Start from a fresh page with the template |
| Never updating the template | Teams use outdated formats for months | Quarterly template review with template owner |
| Skipping optional sections silently | Reader doesn't know if section was considered or just skipped | Write "N/A" or "Not applicable — [reason]" for skipped sections |
