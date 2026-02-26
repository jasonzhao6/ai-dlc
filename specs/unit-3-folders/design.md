# Unit 3: Folder Management — Design

## Lambda: `folders`

Single consolidated Lambda handling all folder management routes.

### Handler Routing

```python
# backend/folders/handler.py

def lambda_handler(event, context):
    method = event["httpMethod"]
    path = event["resource"]

    routes = {
        ("GET", "/folders"): handle_list_folders,
        ("POST", "/folders"): handle_create_folder,
        ("PUT", "/folders/{folderId}"): handle_update_folder,
        ("DELETE", "/folders/{folderId}"): handle_delete_folder,
        ("GET", "/folders/{folderId}/assignments"): handle_list_assignments,
        ("POST", "/folders/{folderId}/assignments"): handle_assign_users,
        ("DELETE", "/folders/{folderId}/assignments/{username}"): handle_unassign_user,
    }

    handler = routes.get((method, path))
    if not handler:
        return error("Not found", 404)
    return handler(event, context)
```

### API Routes

| Method | Path | Auth | Admin | Handler |
|---|---|---|---|---|
| GET | `/folders` | Yes | No* | `handle_list_folders` |
| POST | `/folders` | Yes | Yes | `handle_create_folder` |
| PUT | `/folders/{folderId}` | Yes | Yes | `handle_update_folder` |
| DELETE | `/folders/{folderId}` | Yes | Yes | `handle_delete_folder` |
| GET | `/folders/{folderId}/assignments` | Yes | Yes | `handle_list_assignments` |
| POST | `/folders/{folderId}/assignments` | Yes | Yes | `handle_assign_users` |
| DELETE | `/folders/{folderId}/assignments/{username}` | Yes | Yes | `handle_unassign_user` |

*GET `/folders` is available to all authenticated users but returns filtered results for non-Admin.

### Nested Folder Data Model

Uses the single-table design from Unit 1:

```
Folder record:   PK=FOLDER#<id>, SK=META       → {name, parent_id, created_at}
Child lookup:    GSI1PK=PARENT#<parent_id>      → lists children of a folder
Root folders:    GSI1PK=PARENT#ROOT             → lists top-level folders
Assignment:      PK=FOLDER#<id>, SK=ASSIGN#<u>  → {assigned_at}
User's folders:  GSI1PK=USER#<u>, GSI1SK begins_with ASSIGN#FOLDER# → lists assigned folders
```

### Folder Hierarchy Traversal

**Building the tree (Admin view)**:
1. Query GSI1 for `PARENT#ROOT` → get root folders
2. For each root, query GSI1 for `PARENT#<folder_id>` → get children
3. Recurse or use batch queries to build full tree
4. Return as nested JSON

**Filtered view (non-Admin)**:
1. Query GSI1 for `USER#<username>`, SK begins_with `ASSIGN#FOLDER#` → get directly assigned folder IDs
2. For each assigned folder, traverse up (get parent chain) to build breadcrumb
3. For each assigned folder, traverse down to include all sub-folders
4. Return filtered tree

### Assignment Inheritance Logic

- When checking if a user can access `FOLDER#X`:
  1. Query user's assignments: GSI1PK=`USER#<username>`, GSI1SK begins_with `ASSIGN#FOLDER#`
  2. Get the full parent chain for `FOLDER#X` (walk up via parent_id)
  3. If any folder in the chain is in the user's assignments → access granted
- This means assignments are stored only at the explicitly assigned folder level
- Sub-folder access is derived at runtime

### Cascade Delete Flow

```
delete_folder(folder_id):
    1. Query PK=FOLDER#<folder_id>, SK begins_with FILE# → collect file S3 keys
    2. Query GSI1PK=PARENT#<folder_id> → collect child folder IDs
    3. For each child: recurse delete_folder(child_id)
    4. Batch delete from S3: all collected file keys
    5. Batch delete from DynamoDB: folder META, all FILE# records, all ASSIGN# records
```

### React Pages

| Page | Route | Description |
|---|---|---|
| Folder Browser | `/folders` | Tree/list view of folders; Admin sees all, others see assigned |
| Folder Detail | `/folders/:folderId` | View files + sub-folders in a folder; breadcrumb nav |
| Admin Folder Management | `/admin/folders` | Create, rename, delete folders |
| Folder Assignments | `/admin/folders/:folderId/assignments` | Assign/unassign users to a folder |

### Update to Unit 2: Edit User Page

With folder management now available, the Admin Edit User page (T2.21) can now include folder assignment editing. The Edit User page should allow adding/removing folder assignments inline.
