# Manage attachments for $issue_key

## Steps

1. **List current attachments** — use `jira_get_attachments` with issue_key="$issue_key" to retrieve all attached files. Note filename, size, author, and upload date.
2. **Analyze attachments** — identify:
   - **Stale files**: attachments older than the last status transition
   - **Duplicates**: files with identical names or very similar sizes
   - **Large files**: attachments over 10 MB that could be stored elsewhere
   - **Missing context**: attachments without a comment referencing them
3. **Download if needed** — use `jira_download_attachment` to retrieve specific files for inspection or migration. Files are written to the download directory (`ATLASSIAN_DOWNLOAD_DIR`, default `./atlassian-downloads/`) and never overwrite an existing file.
4. **Upload new files** — use `jira_upload_attachment` to add any new files (screenshots, logs, documentation). The file must live under the upload directory (`ATLASSIAN_UPLOAD_DIR`, default the working directory).
5. **Clean up** — deletes are permanent, so confirm each one with the user first, then use `jira_delete_attachment` to remove:
   - Confirmed duplicates (keep the most recent)
   - Superseded files (old screenshots replaced by newer ones)
   - Files that should not be in the issue tracker (credentials, large binaries)
6. **Summary** — report:
   - Attachments kept (with purpose)
   - Attachments removed (with reason)
   - Total storage freed
