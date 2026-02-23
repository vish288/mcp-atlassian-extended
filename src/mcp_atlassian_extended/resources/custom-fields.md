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

## Field Retirement Migration

Steps to safely retire a custom field:

1. **Export field data**: JQL export all tickets with the field populated
2. **Audit dependencies**: Check dashboards, saved filters, automation rules, and API integrations that reference the field ID
3. **Migrate data**: If replacing with another field, bulk-update tickets to copy values
4. **Remove from screens**: Remove the field from all create/edit/view screens
5. **Set context to "no projects"**: This hides the field without deleting it (preserves historical data)
6. **Document**: Record the field ID, retirement date, and replacement in team wiki
7. **Do not delete**: Deletion is irreversible and removes historical data. Archive instead.

## Schema Drift Detection

Signs a custom field has drifted from its intended use:

| Signal | Problem | Fix |
|--------|---------|-----|
| Fill rate <10% across all projects | Field is not useful | Retire or make required |
| Same field has different values in different projects | Inconsistent usage | Add validation, retrain teams |
| Field used for different purpose than its name suggests | Naming drift | Rename or create a new field |
| Multiple fields capture the same information | Duplication | Merge into one, retire others |

**Quarterly audit checklist:**
- [ ] All custom fields have >10% fill rate in at least one project
- [ ] No duplicate-semantics fields exist
- [ ] All field names match their actual usage
- [ ] Screen contexts match intended projects
