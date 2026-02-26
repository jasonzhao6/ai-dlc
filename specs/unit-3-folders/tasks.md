# Unit 3: Folder Management — Tasks

## Backend Tasks

- [ ] **T3.1**: Implement `handle_create_folder` — create folder with name + parent_id (or ROOT), reject duplicate names at same level
- [ ] **T3.2**: Implement `handle_update_folder` (rename) — update name, validate no sibling conflict
- [ ] **T3.3**: Implement `handle_delete_folder` — cascade delete sub-folders, file metadata, S3 objects, and assignments
- [ ] **T3.4**: Implement `handle_list_folders` — Admin: full tree; non-Admin: filtered by assignments with inheritance
- [ ] **T3.5**: Implement assignment inheritance check utility — walk parent chain to determine folder access
- [ ] **T3.6**: Implement `handle_assign_users` — create assignment records in DynamoDB
- [ ] **T3.7**: Implement `handle_unassign_user` — delete assignment record
- [ ] **T3.8**: Implement `handle_list_assignments` — list users assigned to a folder
- [ ] **T3.9**: Update SAM template: wire `folders` Lambda to API Gateway routes (including assignment sub-routes)

## Frontend Tasks

- [ ] **T3.10**: Build Folder Browser page — tree/list view with expand/collapse, respects role-based filtering
- [ ] **T3.11**: Build Folder Detail page — shows files (placeholder until Unit 4) + sub-folders, breadcrumb navigation
- [ ] **T3.12**: Build Admin Folder Management page — create, rename, delete folders with confirmation dialog
- [ ] **T3.13**: Build Folder Assignments page — assign/unassign users with multi-select
- [ ] **T3.14**: Update Admin Edit User page (from Unit 2) — add folder assignment editing

## Integration Test Tasks

- [ ] **T3.15**: Test POST `/folders` — Admin creates folder → 201; duplicate name → 409; non-Admin → 403
- [ ] **T3.16**: Test POST `/folders` with parent_id — create sub-folder → 201; invalid parent → 404
- [ ] **T3.17**: Test PUT `/folders/{folderId}` — rename → 200; name conflict → 409
- [ ] **T3.18**: Test DELETE `/folders/{folderId}` — empty folder → 200; folder with files → 200 (cascade); non-Admin → 403
- [ ] **T3.19**: Test GET `/folders` — Admin sees all; assigned user sees assigned only; unassigned user sees nothing
- [ ] **T3.20**: Test POST `/folders/{folderId}/assignments` — assign user → 200; non-Admin → 403
- [ ] **T3.21**: Test DELETE `/folders/{folderId}/assignments/{username}` — unassign → 200; verify access revoked
- [ ] **T3.22**: Test assignment inheritance — assign to parent, verify child folder access
