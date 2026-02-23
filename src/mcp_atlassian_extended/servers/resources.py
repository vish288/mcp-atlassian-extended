"""MCP resources for Atlassian — curated rules and guides for Jira/Confluence workflows."""

from __future__ import annotations

from . import mcp

# ════════════════════════════════════════════════════════════════════
# Rules
# ════════════════════════════════════════════════════════════════════


@mcp.resource(
    "resource://rules/jira-hierarchy",
    name="Jira Issue Hierarchy",
    description="Epic → Story → Task → Subtask structure, splitting rules, and type selection",
    mime_type="text/markdown",
    tags={"rule", "jira"},
)
def jira_hierarchy_rules() -> str:
    """Jira issue hierarchy and type definitions."""
    return _JIRA_HIERARCHY_CONTENT


@mcp.resource(
    "resource://rules/jira-ticket-writing",
    name="Jira Ticket Writing Standards",
    description="Summary format, Story/Bug/Task/Spike description templates, comment policy",
    mime_type="text/markdown",
    tags={"rule", "jira"},
)
def jira_ticket_writing_rules() -> str:
    """Jira ticket writing standards and templates."""
    return _JIRA_TICKET_WRITING_CONTENT


@mcp.resource(
    "resource://rules/acceptance-criteria",
    name="Acceptance Criteria Standards",
    description="Given/When/Then format, rule-oriented criteria, writing rules",
    mime_type="text/markdown",
    tags={"rule", "jira"},
)
def acceptance_criteria_rules() -> str:
    """Acceptance criteria standards and formats."""
    return _ACCEPTANCE_CRITERIA_CONTENT


@mcp.resource(
    "resource://rules/sprint-hygiene",
    name="Sprint Hygiene Rules",
    description="Definition of Ready, WIP limits, carry-over policy, refinement standards",
    mime_type="text/markdown",
    tags={"rule", "jira", "agile"},
)
def sprint_hygiene_rules() -> str:
    """Sprint hygiene rules and practices."""
    return _SPRINT_HYGIENE_CONTENT


@mcp.resource(
    "resource://rules/jira-workflow",
    name="Jira Workflow & Automation",
    description="Status transitions, automation rule patterns, workflow governance",
    mime_type="text/markdown",
    tags={"rule", "jira"},
)
def jira_workflow_rules() -> str:
    """Jira workflow transitions and automation patterns."""
    return _JIRA_WORKFLOW_CONTENT


@mcp.resource(
    "resource://rules/issue-linking",
    name="Issue Linking Best Practices",
    description="Link types, correct usage, cross-team patterns, cleanup",
    mime_type="text/markdown",
    tags={"rule", "jira"},
)
def issue_linking_rules() -> str:
    """Issue linking best practices and cross-team patterns."""
    return _ISSUE_LINKING_CONTENT


# ════════════════════════════════════════════════════════════════════
# Guides
# ════════════════════════════════════════════════════════════════════


@mcp.resource(
    "resource://guides/story-points",
    name="Story Point Estimation",
    description="Fibonacci scale, Planning Poker, relative sizing, velocity",
    mime_type="text/markdown",
    tags={"guide", "jira", "agile"},
)
def story_points_guide() -> str:
    """Story point estimation guide."""
    return _STORY_POINTS_CONTENT


@mcp.resource(
    "resource://guides/definition-of-done",
    name="Definition of Done Checklists",
    description="Story/Bug/Task DoD templates, enforcement rules, governance",
    mime_type="text/markdown",
    tags={"guide", "jira", "agile"},
)
def definition_of_done_guide() -> str:
    """Definition of Done checklists and governance."""
    return _DEFINITION_OF_DONE_CONTENT


@mcp.resource(
    "resource://guides/jira-labels",
    name="Jira Label Taxonomy",
    description="Standard labels, naming rules, governance, JQL usage",
    mime_type="text/markdown",
    tags={"guide", "jira"},
)
def jira_labels_guide() -> str:
    """Jira label taxonomy and governance."""
    return _JIRA_LABELS_CONTENT


@mcp.resource(
    "resource://guides/jql-library",
    name="JQL Query Library",
    description="15 query patterns for sprint management, blockers, stale tickets, reporting",
    mime_type="text/markdown",
    tags={"guide", "jira"},
)
def jql_library_guide() -> str:
    """JQL query library with reusable patterns."""
    return _JQL_LIBRARY_CONTENT


@mcp.resource(
    "resource://guides/custom-fields",
    name="Jira Custom Field Governance",
    description="Creation process, naming conventions, field contexts, audit",
    mime_type="text/markdown",
    tags={"guide", "jira"},
)
def custom_fields_guide() -> str:
    """Jira custom field governance guide."""
    return _CUSTOM_FIELDS_CONTENT


@mcp.resource(
    "resource://guides/confluence-spaces",
    name="Confluence Space Organization",
    description="Space taxonomy, page hierarchy, naming conventions, maintenance",
    mime_type="text/markdown",
    tags={"guide", "confluence"},
)
def confluence_spaces_guide() -> str:
    """Confluence space organization guide."""
    return _CONFLUENCE_SPACES_CONTENT


@mcp.resource(
    "resource://guides/agile-ceremonies",
    name="Agile Ceremony Standards",
    description="Sprint planning, standup, review, retrospective formats and rules",
    mime_type="text/markdown",
    tags={"guide", "jira", "agile"},
)
def agile_ceremonies_guide() -> str:
    """Agile ceremony standards and formats."""
    return _AGILE_CEREMONIES_CONTENT


@mcp.resource(
    "resource://guides/git-jira-integration",
    name="Git-Jira Integration Patterns",
    description="Branch naming for auto-linking, smart commits, automation rules, macros",
    mime_type="text/markdown",
    tags={"guide", "jira", "git"},
)
def git_jira_integration_guide() -> str:
    """Git-Jira integration patterns."""
    return _GIT_JIRA_INTEGRATION_CONTENT


# ════════════════════════════════════════════════════════════════════
# Templates
# ════════════════════════════════════════════════════════════════════


@mcp.resource(
    "resource://templates/confluence-pages",
    name="Confluence Page Templates",
    description="ADR, RFC, Runbook, Retrospective, DACI, and Meeting Notes templates",
    mime_type="text/markdown",
    tags={"template", "confluence"},
)
def confluence_page_templates() -> str:
    """Confluence page templates in wiki markup."""
    return _CONFLUENCE_PAGES_CONTENT


# ════════════════════════════════════════════════════════════════════
# Content constants
# ════════════════════════════════════════════════════════════════════

_JIRA_HIERARCHY_CONTENT = """\
# Jira Issue Hierarchy

## Structure

```
Epic (measurable outcome, spans sprints)
  +-- Story (user-facing deliverable, fits in one sprint)
       +-- Task (technical unit of work, no direct user story)
            +-- Subtask (atomic action within a Task)
  +-- Bug (defect against a Story or standalone)
  +-- Spike (time-boxed research, produces knowledge not code)
```

## Type Definitions

| Type | Delivers | Fits in Sprint | Example |
|------|----------|---------------|---------|
| Epic | Measurable outcome | No (multi-sprint) | Reduce checkout abandonment by 15% |
| Story | User-facing capability | Yes (8 pts max) | User can save address for future orders |
| Task | Technical work | Yes | Migrate session store from Redis 6 to 7 |
| Subtask | Atomic piece of Task | Yes (child of Task) | Write migration script for key format |
| Bug | Defect fix | Yes | Cart total shows negative after coupon |
| Spike | Research output | Yes (time-boxed) | Evaluate WebSocket vs SSE |

## When to Use Each Type

- **Epic**: business objective, not feature list. Must have: objective, measurable outcome, \
time bound, out of scope, dependencies
- **Story**: answers "as a [user], I can [do something] so that [benefit]". Max 8 points.
- **Task**: technical work without user story. Still requires verifiable acceptance criteria.
- **Subtask**: use sparingly. Only when parallel work within a Task requires separate assignees. \
If >5 subtasks, the Task is too large.
- **Bug**: link to the Story/Epic it breaks. Always include: steps to reproduce, \
expected vs actual, severity.
- **Spike**: time-boxed 1-3 days. Deliverable is recommendation, not code. \
Creates follow-up tickets.

## Splitting Rules

| Signal | Action |
|--------|--------|
| Story estimated at 13+ points | Split into 2-3 smaller Stories |
| Task has 6+ subtasks | Split into multiple Tasks |
| Epic has no clear measurable outcome | Redefine or split |

How to split:
1. By user workflow step
2. By data entity
3. By platform/environment
4. By acceptance criterion
5. By happy path vs edge cases

Anti-patterns: splitting by technical layer (not independently shippable), \
"Part 1/Part 2" (each must deliver value), subtasks as mini-Stories.

## Hierarchy Linking

| Relationship | How |
|-------------|-----|
| Story/Task -> Epic | Epic Link field (`customfield_10008`), NOT `parent` |
| Subtask -> Task | Standard parent field |
| Bug -> Story/Epic | Epic Link or `relates to` link |
| Spike -> Story | `relates to` link |
"""

_JIRA_TICKET_WRITING_CONTENT = """\
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

Good: "Chose server-side invalidation over client-side expiry for compliance. \
Client-side has 15-min window."
Bad: "Working on this." / "Almost done." / "Done."

Structure: brief context + bullet evidence + next steps.
Use Jira wiki markup with real newlines (no escaped sequences).
"""

_ACCEPTANCE_CRITERIA_CONTENT = """\
# Acceptance Criteria Standards

## Formats

### Given/When/Then (Behavioral)

```
Given the user is on the checkout page with items in the cart,
when they select a province,
then the shipping estimate updates within 500ms without page reload.
```

### Checklist (Rule-Oriented)

```
[ ] Shipping estimate updates on province change
[ ] No full page reload
[ ] Response time under 500ms at p95
[ ] Province selector has aria-label
```

### Hybrid

Combine both when a feature has a primary workflow plus independent requirements.

## Writing Rules

### Must Be Testable

Every criterion maps to a verifiable condition.

Good: "Response time under 500ms at p95 under 100 concurrent users"
Bad: "The page should be fast"

### Must Be Specific

Include numbers, thresholds, exact behaviors.

Good: "File upload accepts PNG, JPG, GIF up to 10MB"
Bad: "File upload should work for common formats"

### Must Be Independent

Each criterion verifiable on its own.

### Must Reflect User Value

Describe outcomes, not implementation.

Good: "User sees order history sorted by date, newest first"
Bad: "Query uses ORDER BY created_at DESC"

## Anti-Patterns

- **Vague**: "Should work properly" -- define what "properly" means
- **Implementation-prescriptive**: "Use Redis with 5-min TTL" -- describe behavior instead
- **Untestable**: "UI should be intuitive" -- add measurable threshold
- **Too many**: 25 criteria on one Story -- split the Story
"""

_SPRINT_HYGIENE_CONTENT = """\
# Sprint Hygiene Rules

## Definition of Ready

A ticket must meet all of these before entering a sprint:

- Summary follows format
- Description populated with template
- Acceptance criteria written and testable
- Story points estimated by team
- Dependencies identified and linked
- No unresolved questions
- Design reviewed if applicable
- Priority set by product owner

## WIP Limits

| Team size | Max WIP per person |
|-----------|-------------------|
| 1-3 | 1 |
| 4-6 | 1-2 |
| 7+ | 1 (strictly enforced) |

Finish before starting. Blocked tickets count toward WIP.

## Refinement

- Refine 1-2 sprints ahead (not more)
- 5-10% of sprint capacity for refinement
- Use Fibonacci: 1, 2, 3, 5, 8, 13
- 13-point stories must decompose before sprint entry

## Carry-Over Policy

| Sprint | Action |
|--------|--------|
| 2nd sprint | Re-estimate, add comment |
| 3rd sprint | Mandatory team discussion -- split, descope, or escalate |
| 4th sprint | Escalate to product owner |

## Mid-Sprint Rules

- No tickets added without sizing
- Adding requires removing equal points
- Blocked tickets need: comment, label, linked blocker
- Remove `blocked` label immediately when unblocked

## Sprint Goal

One sentence describing the primary outcome. Not a list of tickets.

Good: "Users can complete checkout with saved addresses"
Bad: "Complete PROJ-123, PROJ-124, PROJ-125"
"""

_JIRA_WORKFLOW_CONTENT = """\
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
"""

_ISSUE_LINKING_CONTENT = """\
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
"""

_STORY_POINTS_CONTENT = """\
# Story Point Estimation

## Fibonacci Scale

| Points | Complexity | Unknowns | Example |
|--------|-----------|----------|---------|
| 1 | Trivial | None | Fix typo, update config |
| 2 | Small | Minimal | Add form field, update API response |
| 3 | Moderate, 1-2 integration points | Some | New API endpoint with tests |
| 5 | Significant, multiple parts | Moderate | Third-party integration |
| 8 | Large, cross-cutting | High | DB migration with backfill |
| 13 | Too large | Very high | Must decompose |

## Planning Poker

1. PO presents ticket
2. Team asks questions (3 min)
3. Simultaneous vote
4. If within 1 Fibonacci: accept
5. If >2 gap: discuss, re-vote once
6. Still divergent: use higher estimate or create spike

Rules: everyone votes, simultaneous reveal, no averaging.

## What Points Do NOT Measure

- Hours (senior may take 3h, junior 2 days -- same estimate)
- Lines of code (1-point rename may touch 50 files)
- Individual performance
- Value

## Velocity

- Track over 3-5 sprints for reliable baseline
- Use for capacity planning, not performance measurement
- Never compare across teams
- Investigate if drops >30% for 2+ sprints
"""

_DEFINITION_OF_DONE_CONTENT = """\
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

Before closing: verify every DoD item checked, criteria met, PR merged, \
no open threads. Some workflows gate Closed on DoD completion.
"""

_JIRA_LABELS_CONTENT = """\
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
"""

_JQL_LIBRARY_CONTENT = """\
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
"""

_CUSTOM_FIELDS_CONTENT = """\
# Jira Custom Field Governance

## Before Creating

1. Does a built-in field cover this?
2. Can a label serve the same purpose?
3. Will it be used on >50% of tickets?
4. Who will populate it?
5. Can it be queried via JQL?

## Naming

- Descriptive: "Definition of Done" not "DoD"
- No abbreviations
- No team prefix if shared
- No duplicate semantics

## Field Types

| Type | JQL | Example |
|------|-----|---------|
| Select (single) | `= "value"` | Privacy Concerns: Yes/No |
| Select (multi) | `in ("a", "b")` | Affected Services |
| Text | `~ "text"` | External reference |
| Number | `> 5` | (avoid -- use story points) |
| Checklist (plugin) | N/A | Definition of Done |

For select fields, use `{"value": "Option Text"}` in API calls.

## Contexts

- Narrow by default (specific projects/types)
- Expand only when needed
- Screen-restricted fields cannot be set on create screen

## Common Fields

| Field | ID | Type |
|-------|-----|------|
| Definition of Done | `customfield_NNNNN` | Checklist (plugin) |
| Privacy Concerns | `customfield_NNNNN` | Select |
| Security Concerns | `customfield_NNNNN` | Select |
| Epic Link | `customfield_10008` | Epic link |

## Governance

- Creation: request to admin with justification
- Quarterly audit: check fill rates, merge duplicates
- Retirement: remove from screens, hide context (don't delete)
"""

_CONFLUENCE_SPACES_CONTENT = """\
# Confluence Space Organization

## Taxonomy

| Type | Pattern | Example |
|------|---------|---------|
| Team | `TEAM-<name>` | TEAM-Platform |
| Project | `PROJ-<key>` | PROJ-Checkout |
| Knowledge base | `KB-<domain>` | KB-Engineering |
| Archive | `ARCHIVE-<year>` | ARCHIVE-2024 |

One team = one space. Archive rather than delete.

## Page Hierarchy

```
Space Home (dashboard, not a document)
+-- Overview (mission, contacts, links)
+-- How We Work
+-- Architecture
|   +-- ADRs
+-- Meeting Notes
+-- Sprints
+-- Retrospectives
```

Max 4 levels deep. Date prefix for chronological content.

## Naming

- Date for chronological: `YYYY-MM-DD Title`
- Type prefix for structured: ADR, RFC, Runbook
- No "Draft" in titles -- use Confluence draft status
- Specific enough for search results

## Permissions

Default: team edit, cross-team read. Restrict admin to leads. \
Use page restrictions sparingly.

## Maintenance

- Monthly: review recent updates, archive stale drafts
- Quarterly: archive completed projects, review permissions
- Annual: audit all spaces, export critical content
"""

_AGILE_CEREMONIES_CONTENT = """\
# Agile Ceremony Standards

## Sprint Planning

**Timebox**: 2h max (2-week sprint), 1h (1-week)

1. Sprint goal (10 min)
2. Backlog review (30 min) -- confirm Definition of Ready
3. Capacity check (10 min) -- PTO, on-call
4. Commitment (30 min) -- team pulls tickets
5. Task breakdown (30 min)

Plan to 80% capacity. Team commits, not PO.

## Daily Standup

**Timebox**: 15 min hard stop.

Each person:
1. What will I work on today?
2. Am I blocked?

Alternative: walk the board right-to-left. No problem-solving -- take offline.

## Sprint Review (Demo)

**Timebox**: 1h max (2-week), 30 min (1-week)

1. Goal recap (5 min)
2. Demos (30-40 min) -- working software, not slides
3. Stakeholder feedback (15 min)
4. Metrics (5 min)

Only demo completed work (passes DoD).

## Retrospective

**Timebox**: 45-60 min (2-week), 30 min (1-week)

Formats: Start/Stop/Continue, 4Ls, Mad/Sad/Glad, Sailboat

1. Review previous action items (10 min)
2. Gather observations (15 min)
3. Vote on themes (5 min)
4. Generate actions (15 min) -- max 2-3 items
5. Assign owners (5 min)

Rules: what's said stays, no blame, actionable items only, rotate facilitator.
"""

_GIT_JIRA_INTEGRATION_CONTENT = """\
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
"""

_CONFLUENCE_PAGES_CONTENT = """\
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
"""
