# Create a {issue_type} in project {project_key}

## Steps

1. **Check available fields** — use `jira_list_fields` to identify required and optional fields for the {issue_type} type in {project_key}.
2. **Gather information** — collect from the user:
   - Summary (clear, concise title)
   - Description (using the appropriate template for {issue_type})
   - Priority
   - Assignee
   - Story points (if applicable)
   - Labels
   - Epic link (if applicable)
3. **Set quality fields**:
   - **Definition of Done** — add acceptance criteria checklist items
   - **Privacy concerns** — assess and set (Yes/No)
   - **Security concerns** — assess and set (Yes/No)
4. **Create the issue** — use `jira_create_issue` with project_key="{project_key}", issue_type="{issue_type}", and all gathered fields.
5. **Add links** — if the issue relates to other tickets, use `jira_create_link` to establish relationships (blocks, relates to, duplicates).
6. **Verify** — confirm the issue was created and report the issue key and URL.

## Templates by Type

- **Story**: "As a [user], I want [goal], so that [benefit]" + acceptance criteria
- **Bug**: Steps to reproduce, expected vs actual behavior, environment details
- **Task**: Clear objective, technical approach, definition of done
- **Epic**: Business goal, scope boundaries, success metrics
