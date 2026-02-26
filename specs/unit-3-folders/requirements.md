# Unit 3: Folder Management — Requirements

## Dependencies

- **Depends on**: Unit 2 (auth middleware, user records for assignments)

## Stories Covered

| Story | Title | Summary |
|---|---|---|
| US-011 | Create Folder | Admin creates a top-level folder |
| US-012 | Create Sub-Folder | Admin creates nested folders with parent reference |
| US-013 | Rename Folder | Admin renames a folder without affecting contents |
| US-014 | Delete Folder | Admin deletes folder with cascade (files + sub-folders) |
| US-015 | List and Browse Folders | Admin sees hierarchical folder view |
| US-016 | Assign Users to Folders | Admin assigns users to folders; parent grants sub-folder access |
| US-017 | Unassign Users from Folders | Admin removes user assignments |

## Functional Requirements

### FR-1: Folder CRUD (US-011, US-012, US-013, US-014, US-015)
- Create top-level folder: name stored in DynamoDB, parent=ROOT
- Create sub-folder: name + parent_id stored in DynamoDB
- Duplicate names within the same parent are rejected
- Rename: update name in DynamoDB; S3 keys use folder_id (not name), so rename has no S3 impact
- Delete: cascade delete all sub-folders, file metadata in DynamoDB, and files in S3; confirmation required on front-end
- List: return folder hierarchy; Admin sees all, non-Admin sees assigned folders only
- Breadcrumb navigation using parent_id chain

### FR-2: User-Folder Assignments (US-016, US-017)
- Admin can assign one or more users to a folder
- Assigning to a parent folder grants access to all sub-folders (resolved at query time, not stored per sub-folder)
- Admin can unassign users from a folder
- Unassignment takes effect immediately (no re-login needed)
- Files uploaded by unassigned users remain in the folder
- Assignment records stored in DynamoDB: `PK=FOLDER#<id>`, `SK=ASSIGN#<username>`

### FR-3: Folder Access for Non-Admin Users
- Non-Admin users only see folders they are assigned to (direct or via parent)
- Folder browsing respects the assignment hierarchy
- The folder Lambda checks assignments via the auth middleware context + DynamoDB query

## Non-Functional Requirements

- Cascade delete must be atomic where possible (batch writes)
- No hard limit on nesting depth, but UI should handle deep nesting gracefully
- Folder operations are Admin-only (403 for other roles)
