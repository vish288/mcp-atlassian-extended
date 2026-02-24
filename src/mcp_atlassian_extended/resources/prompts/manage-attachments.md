# Manage attachments for {issue_key}

## Steps

1. **List current attachments** — use `jira_get_attachments` with issue_key="{issue_key}" to retrieve all attached files. Note filename, size, author, and upload date.
2. **Analyze attachments** — identify:
   - **Stale files**: attachments older than the last status transition
   - **Duplicates**: files with identical names or very similar sizes
   - **Large files**: attachments over 10 MB that could be stored elsewhere
   - **Missing context**: attachments without a comment referencing them
3. **Download if needed** — use `jira_download_attachment` to retrieve specific files for inspection or migration.
4. **Upload new files** — use `jira_upload_attachment` to add any new files (screenshots, logs, documentation).
5. **Clean up** — use `jira_delete_attachment` to remove:
   - Confirmed duplicates (keep the most recent)
   - Superseded files (old screenshots replaced by newer ones)
   - Files that should not be in the issue tracker (credentials, large binaries)
6. **Summary** — report:
   - Attachments kept (with purpose)
   - Attachments removed (with reason)
   - Total storage freed
