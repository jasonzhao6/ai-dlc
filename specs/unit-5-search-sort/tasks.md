# Unit 5: Search & Sort — Tasks

## Backend Tasks

- [x] **T5.1**: Implement `handle_search_files` — scan/query with name filter, scope by role + folder assignments
- [x] **T5.2**: Implement `get_folder_path` utility — walk parent chain to build folder path string for search results
- [x] **T5.3**: Add GET `/files/search` route to `files` Lambda handler
- [x] **T5.4**: Update SAM template: add `/files/search` API Gateway route

## Frontend Tasks

- [x] **T5.5**: Build Search Bar component — text input with debounce (300ms), search icon
- [x] **T5.6**: Build Search Results view — display results with file name, size, date, uploader, folder path
- [x] **T5.7**: Make file list column headers clickable for sorting (Name, Date Uploaded, Size)
- [x] **T5.8**: Implement client-side sort logic — ascending/descending toggle, arrow indicator
- [x] **T5.9**: Set default sort to alphabetical by name (ascending)
- [x] **T5.10**: Ensure sort state persists within same folder but resets on folder navigation

## Integration Test Tasks

- [x] **T5.11**: Test GET `/files/search?q=report` — Admin gets results across all folders
- [x] **T5.12**: Test GET `/files/search?q=report` — non-Admin gets results only from assigned folders
- [x] **T5.13**: Test GET `/files/search?q=` — empty query returns 400
- [x] **T5.14**: Test search is case-insensitive — search "REPORT" matches "report.pdf"
- [x] **T5.15**: Test search partial match — search "rep" matches "report.pdf"
