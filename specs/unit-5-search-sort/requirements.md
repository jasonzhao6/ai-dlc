# Unit 5: Search & Sort — Requirements

## Dependencies

- **Depends on**: Unit 4 (files must exist to search and sort)

## Stories Covered

| Story | Title | Summary |
|---|---|---|
| US-023 | Search Files by Name | Case-insensitive partial name search across assigned folders |
| US-024 | Sort Files | Sort file list by name, date uploaded, or size |

## Functional Requirements

### FR-1: Search Files by Name (US-023)
- Search input available on the file browsing view
- Case-insensitive partial name matching
- Results scoped to user's assigned folders (Admin sees all)
- Results display: file name, size, upload date, uploader, folder path
- Each result includes the folder path so user knows the file location

### FR-2: Sort Files (US-024)
- Clickable column headers: Name, Date Uploaded, Size
- Each column supports ascending and descending sort
- Visual indicator (arrow) shows current sort column and direction
- Default sort: alphabetical by name, ascending
- Sort state persists while navigating within the same folder

## Non-Functional Requirements

- Search should return results within a reasonable time (< 2 seconds for typical data sets)
- Sort can be client-side for folder contents (since file lists per folder are bounded)
- Search across folders requires server-side query
