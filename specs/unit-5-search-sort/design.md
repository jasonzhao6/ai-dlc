# Unit 5: Search & Sort — Design

## Sort: Client-Side Implementation

Sorting files within a single folder is done entirely on the front-end. No backend changes needed for sort.

### Sort Logic

```javascript
// Sort columns and directions
const SORT_OPTIONS = {
  name: (a, b) => a.name.localeCompare(b.name),
  uploaded_at: (a, b) => new Date(a.uploaded_at) - new Date(b.uploaded_at),
  size: (a, b) => a.size - b.size,
};

// Default: name ascending
// Toggle: click same column → reverse direction; click different column → ascending
```

### UI Behavior

- Column headers are clickable
- Arrow indicator: `▲` for ascending, `▼` for descending
- Sort state stored in React component state (resets on folder navigation per AC5 interpretation — persists within same folder)

## Search: Server-Side Implementation

Search spans multiple folders, so it requires a backend API.

### API Route

| Method | Path | Auth | Handler |
|---|---|---|---|
| GET | `/files/search?q=<term>` | Yes | `handle_search_files` |

Added to the existing `files` Lambda.

### Search Strategy

DynamoDB does not support full-text search natively. Given the scope of this project, the approach is:

**Approach: DynamoDB Scan with Filter**

1. **Admin**: Scan the table for items where SK begins_with `FILE#` and `name` contains the search term (case-insensitive)
2. **Non-Admin**:
   - First, get user's assigned folder IDs (including inherited sub-folders)
   - For each assigned folder, query PK=`FOLDER#<id>`, SK begins_with `FILE#`
   - Filter results where `name` contains the search term (case-insensitive)
3. Return results with folder path for each match

**Why this approach**:
- The data volume for a file-sharing system is manageable (not millions of records)
- Avoids adding external search infrastructure (ElasticSearch/OpenSearch)
- DynamoDB `contains` filter works for partial matching
- For Admin, a Scan is acceptable given bounded data; for non-Admin, folder-scoped queries are efficient

### Search Response Format

```json
{
  "results": [
    {
      "file_id": "abc123",
      "name": "report.pdf",
      "size": 1048576,
      "uploaded_at": "2026-02-20T10:00:00Z",
      "uploaded_by": "jsmith",
      "folder_id": "folder-xyz",
      "folder_path": "Projects / Q1 Reports"
    }
  ]
}
```

### Handler Implementation

```python
def handle_search_files(event, context):
    user = event["user"]
    query_term = event["queryStringParameters"].get("q", "").strip().lower()

    if not query_term:
        return error("Search term required", 400)

    if user["role"] == "Admin":
        # Scan for all FILE# items, filter by name contains query_term
        results = scan_files_by_name(query_term)
    else:
        # Get user's accessible folder IDs (direct + inherited)
        folder_ids = get_accessible_folders(user["username"])
        results = []
        for folder_id in folder_ids:
            files = query_files_in_folder(folder_id, name_filter=query_term)
            results.extend(files)

    # Enrich with folder path
    for result in results:
        result["folder_path"] = get_folder_path(result["folder_id"])

    return success({"results": results})
```

### React Components

| Component | Location | Description |
|---|---|---|
| Search Bar | File browser header | Text input with search icon, debounced (300ms) |
| Search Results | Below search bar / overlay | List of matching files with folder path, same columns as file list |
| Sortable Column Header | File list table | Clickable header with sort arrow indicator |

### Updated File List Table

```
┌──────────────────────────────────────────────────────────────────┐
│ [🔍 Search files...                                           ] │
├──────────────────────────────────────────────────────────────────┤
│ Name ▲          │ Size      │ Date Uploaded  │ Uploaded By      │
├─────────────────┼───────────┼────────────────┼──────────────────┤
│ document.pdf    │ 2.4 MB    │ 2026-02-20     │ jsmith           │
│ photo.jpg       │ 856 KB    │ 2026-02-19     │ admin            │
│ report.xlsx     │ 1.1 MB    │ 2026-02-18     │ jdoe             │
└─────────────────┴───────────┴────────────────┴──────────────────┘
```
