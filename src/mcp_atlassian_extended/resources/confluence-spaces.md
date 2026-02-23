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

Default: team edit, cross-team read. Restrict admin to leads. Use page restrictions sparingly.

## Maintenance

- Monthly: review recent updates, archive stale drafts
- Quarterly: archive completed projects, review permissions
- Annual: audit all spaces, export critical content

## Cross-Space Linking

Best practices for linking between Confluence spaces:

- Use full page title in links (not page ID) for readability
- Add a "See also" section at the bottom of pages that reference other spaces
- Avoid deep-linking to specific headings within a page -- heading anchors break on page rename
- Use page labels for cross-space discoverability (e.g., `runbook`, `adr`, `onboarding`)
- When linking to another team's space, verify the link periodically -- they may reorganize

**Link format in wiki markup:**

```
[Page Title|SPACE:Page Title]
```

## Archive Retrieval

How to find and restore archived content:

- Confluence search includes archived spaces by default -- use space key filter to narrow results
- Archived spaces follow the `ARCHIVE-*` naming convention
- To restore a page: move it from the archive space back to the active space
- To restore an entire space: contact Confluence admin (space unarchive requires admin permissions)
- Before archiving: verify no active pages link to content in the space being archived

**JQL for finding cross-references to archive candidates:**

Search for pages that link to the target space before archiving.
