# Application Build Plan — S3 File-Sharing System

## Objective

Build the complete S3 File-Sharing System following the 5-unit spec structure, testing each backend endpoint with SAM local before moving on.

## Environment

- Python 3.12, Node 25.x, npm 11.x
- AWS SAM CLI 1.154.0, Docker available
- AWS CLI installed (credentials to be configured)
- No containers for SAM build (`--use-container` NOT used)

## Color Theme

**Teal + Dark Gray** — professional, modern, not default blue.
- Primary: `#0d9488` (teal-600)
- Dark: `#1e293b` (slate-800)
- Accent: `#14b8a6` (teal-500)
- Light bg: `#f0fdfa` (teal-50)
- Text: `#334155` (slate-700)

## Plan Steps

### Phase 0: Project Setup

- [x] **Step 0.1 — Initialize SAM project and directory structure**
  Create the project scaffold per Unit 1 design: `template.yaml`, `backend/`, `frontend/`, `tests/`.

- [x] **Step 0.2 — Create SAM template with DynamoDB, S3, API Gateway**
  Define `FileShareTable` (PK, SK, GSI-1, TTL), S3 storage bucket (CORS), S3 frontend bucket, API Gateway REST API with all routes, and Lambda functions (placeholder handlers). Include Lambda Layer for shared code.
  > **Resolved**: SAM parameters with default `us-east-1`. AllowedValues: `us-east-1`, `us-east-2`, `us-west-2`.

- [x] **Step 0.3 — Create shared Lambda layer**
  Build `backend/shared/` as a Lambda Layer: `db.py` (DynamoDB client + Decimal serializer), `response.py` (success/error helpers). Create a layer verification script.

- [x] **Step 0.4 — Create placeholder Lambda handlers**
  Stub handlers for `auth_users`, `folders`, `files`, `seed` — all return 501 Not Implemented.

- [x] **Step 0.5 — Validate SAM template and test locally**
  Run `sam validate`, `sam build`, and `sam local invoke` to confirm the stack is correct.

- [x] **Step 0.6 — Initialize React project with Vite**
  Set up `frontend/` with Vite + React. Install Bootstrap 5 (CDN in index.html), React Router. Set up the teal color theme.

- [x] **Step 0.7 — Create React skeleton: Layout, ErrorBanner, API client, routing**
  Build the app shell (header, sidebar, content area), ErrorBanner component, API client module (`api/client.js`), and route structure. Build with `npm run build`.

- [x] **Step 0.8 — Create TODO file for post-deployment tasks**
  Create `TODO.md` at project root.

### Phase 1: Unit 2 — Auth, Sessions & User Management (Backend)

- [x] **Step 1.1 — Implement auth_middleware.py**
  `authenticate()`, `require_auth`, `require_admin` decorators in the shared layer. (T2.1)

- [x] **Step 1.2 — Implement handle_login**
  Validate credentials, create session in DynamoDB, return token + role. (T2.2)

- [x] **Step 1.3 — Implement handle_logout**
  Delete session from DynamoDB. (T2.3)

- [x] **Step 1.4 — Implement handle_change_password**
  Verify current password, hash new password, update user record. (T2.4)

- [x] **Step 1.5 — Implement handle_reset_password (Admin)**
  Generate temp password, set force_password_change flag. (T2.5)

- [x] **Step 1.6 — Implement handle_create_user**
  Create user with role, reject duplicates via conditional write. (T2.6)

- [x] **Step 1.7 — Implement handle_update_user**
  Update role/status, prevent Admin self-role-change. (T2.7)

- [x] **Step 1.8 — Implement handle_delete_user**
  Delete user record + invalidate all sessions, prevent self-delete. (T2.8)

- [x] **Step 1.9 — Implement handle_list_users**
  Query/scan users with optional role/status filter. (T2.9)

- [x] **Step 1.10 — Implement seed Lambda**
  Create default Admin account (CloudFormation Custom Resource). (T2.10)

- [x] **Step 1.11 — Add bcrypt to Lambda layer and update SAM template**
  Bundle bcrypt in the shared layer. Wire auth-users Lambda to API Gateway routes. (T2.11, T2.12)

- [x] **Step 1.12 — Test all auth/user endpoints with SAM local**
  Test login, logout, change-password, CRUD users, reset-password via `sam local start-api`. (T2.22–T2.30)

### Phase 2: Unit 2 — Auth & User Management (Frontend)

- [x] **Step 2.1 — Build Login page**
  Login form, API call, store token in localStorage, redirect on success. (T2.13)

- [x] **Step 2.2 — Build auth context/provider and protected routes**
  Auth context storing token + role, `isAuthenticated`, `isAdmin`. Protected route wrapper redirecting to `/login`. (T2.15, T2.16)

- [x] **Step 2.3 — Build Force Change Password page**
  Shown after login when `force_password_change=true`. (T2.14)

- [x] **Step 2.4 — Add logout to Layout header**
  Logout button clears token, redirects to `/login`. (T2.17)

- [x] **Step 2.5 — Build User Settings page (change own password)**
  Change password form. (T2.18)

- [x] **Step 2.6 — Build Admin User List page**
  Table with filter by role/status, edit/delete actions. (T2.19)

- [x] **Step 2.7 — Build Admin Create User and Edit User pages**
  Create user form + edit user form as modals in Admin User List page (folder assignments deferred to Unit 3). (T2.20, T2.21)

- [x] **Step 2.8 — npm run build and verify**
  Build frontend, confirm no errors.

### Phase 3: Unit 3 — Folder Management (Backend)

- [x] **Step 3.1 — Implement folder CRUD handlers**
  `handle_create_folder`, `handle_update_folder` (rename), `handle_delete_folder` (cascade). (T3.1, T3.2, T3.3)

- [x] **Step 3.2 — Implement handle_list_folders**
  Admin: full tree; non-Admin: filtered by assignments with inheritance. (T3.4)

- [x] **Step 3.3 — Implement assignment inheritance utility**
  Walk parent chain to determine folder access. (T3.5)

- [x] **Step 3.4 — Implement assignment handlers**
  `handle_assign_users`, `handle_unassign_user`, `handle_list_assignments`. (T3.6, T3.7, T3.8)

- [x] **Step 3.5 — Update SAM template for folders Lambda**
  Wire folders Lambda to API Gateway routes. (T3.9, already done in Phase 0)

- [x] **Step 3.6 — Test all folder endpoints with SAM local**
  Test create, rename, delete, list, assignments. (T3.15–T3.22)

### Phase 4: Unit 3 — Folder Management (Frontend)

- [x] **Step 4.1 — Build Folder Browser page**
  Tree/list view with expand/collapse, role-based filtering. (T3.10)

- [x] **Step 4.2 — Build Folder Detail page**
  Sub-folders + file placeholder, breadcrumb navigation. (T3.11)

- [x] **Step 4.3 — Build Admin Folder Management page**
  Create, rename, delete folders with confirmation dialog. (T3.12)

- [x] **Step 4.4 — Build Folder Assignments page**
  Assign/unassign users with multi-select (integrated as modal in Admin Folder page). (T3.13)

- [x] **Step 4.5 — Update Admin Edit User page with folder assignment editing**
  (T3.14, accessible from Admin Folder page assignments modal)

- [x] **Step 4.6 — npm run build and verify**

### Phase 5: Unit 4 — File Operations (Backend)

- [x] **Step 5.1 — Implement handle_get_upload_url**
  Validate role + folder access + file size, generate pre-signed PUT URL. (T4.1)

- [x] **Step 5.2 — Implement handle_confirm_upload**
  Record file metadata in DynamoDB. (T4.2)

- [x] **Step 5.3 — Implement handle_get_download_url**
  Validate role + folder access, generate pre-signed GET URL. (T4.3)

- [x] **Step 5.4 — Implement handle_list_files**
  Query files in folder, include sub-folders, respect access rules. (T4.4)

- [x] **Step 5.5 — Implement handle_delete_file**
  Admin: any; Uploader: own only. Delete from S3 + DynamoDB. (T4.5)

- [x] **Step 5.6 — Update SAM template for files Lambda**
  Wire files Lambda to routes, grant S3 permissions, add TTL env vars. (T4.6, T4.7, T4.8, already done in Phase 0)

- [x] **Step 5.7 — Test all file endpoints with SAM local**
  Test upload URL, confirm upload, download URL, list, delete. (T4.16–T4.21)

### Phase 6: Unit 4 — File Operations (Frontend)

- [x] **Step 6.1 — Build file list in folder detail page**
  Columns: name, size, date, uploader. (T4.9)

- [x] **Step 6.2 — Build upload flow**
  File picker, client-side size validation, pre-signed URL, S3 PUT, confirm. (T4.10)

- [x] **Step 6.3 — Build upload progress indicator**
  Percentage bar during S3 PUT via XMLHttpRequest. (T4.11)

- [x] **Step 6.4 — Build download button**
  Visible for Admin + Reader only. (T4.12)

- [x] **Step 6.5 — Build delete button with role-based visibility**
  Admin: all files; Uploader: own only. Confirmation dialog. (T4.13, T4.14, T4.15)

- [x] **Step 6.6 — npm run build and verify**

### Phase 7: Unit 5 — Search & Sort

- [x] **Step 7.1 — Implement handle_search_files (backend)**
  Scan/query with name filter, scope by role + folder access. (T5.1, T5.2, T5.3, T5.4)

- [x] **Step 7.2 — Test search endpoint with SAM local**
  (T5.11–T5.15)

- [x] **Step 7.3 — Build Search Bar and Search Results (frontend)**
  Text input with debounce, results with folder path. (T5.5, T5.6)

- [x] **Step 7.4 — Build sortable column headers (frontend)**
  Client-side sort by name/date/size, ascending/descending toggle, arrow indicators. (T5.7, T5.8, T5.9, T5.10)

- [x] **Step 7.5 — npm run build and verify**

### Phase 8: Final Verification

- [x] **Step 8.1 — Full SAM build and validate**
  `sam build` + `sam validate` for the complete stack.

- [x] **Step 8.2 — End-to-end SAM local test**
  Start API locally, walk through login → create user → create folder → assign user → upload file → search → sort → delete → logout.

- [x] **Step 8.3 — Update TODO.md with post-deployment tasks**
  Document: first deploy steps, CloudWatch log checks, S3 CORS verification, seed Lambda trigger, frontend deployment.

## Deliverables

| Deliverable | Location |
|---|---|
| SAM template | `template.yaml` |
| Shared Lambda layer | `backend/layers/shared/` |
| Auth/Users Lambda | `backend/auth_users/` |
| Folders Lambda | `backend/folders/` |
| Files Lambda | `backend/files/` |
| Seed Lambda | `backend/seed/` |
| Layer verification script | `scripts/verify_layer.sh` |
| React frontend | `frontend/` |
| Integration tests | `tests/integration/` |
| TODO (post-deploy) | `TODO.md` |
| This plan | `.aidlc/app_plan.md` |

## Resolved Questions

1. **AWS Region / S3 bucket prefix**: SAM parameters with default `us-east-1`. AllowedValues: `us-east-1`, `us-east-2`, `us-west-2`.
