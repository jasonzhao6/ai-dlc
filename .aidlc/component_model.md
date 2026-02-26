# Component Model — S3 File-Sharing System

---

## 1. Entity Components

These are the core domain objects of the system.

### 1.1 User

Represents a person who can access the system.

| Attribute | Type | Description |
|---|---|---|
| username | String (unique) | Primary identifier for the user |
| password_hash | String | Bcrypt-hashed password (never stored in plaintext) |
| role | Enum: Admin, Uploader, Reader, Viewer | Determines permissions across the system |
| status | Enum: active, disabled | Whether the user can log in |
| force_password_change | Boolean | If true, user must set a new password on next login |
| created_at | Timestamp | When the account was created |

**Business Rules:**
- Usernames are globally unique
- Exactly one Admin account is seeded at initial deployment
- Admin cannot change their own role or delete/disable themselves
- A disabled user cannot log in; their active sessions are invalidated
- Deleting a user does not cascade-delete their uploaded files

### 1.2 Session

Represents an active authenticated session.

| Attribute | Type | Description |
|---|---|---|
| token | String (unique) | Cryptographically random session identifier |
| username | String | The user who owns this session |
| role | String | Cached role at time of session creation |
| created_at | Timestamp | When the session was created |
| ttl | Epoch seconds | Expiry time; auto-deleted by DynamoDB TTL |

**Business Rules:**
- Tokens are generated using cryptographically secure randomness
- Sessions expire automatically after a configurable TTL (default 24 hours)
- Logging out deletes the session immediately
- Disabling or deleting a user invalidates all their sessions
- Every API request (except login) must present a valid session token

### 1.3 Folder

Represents a logical container for files, supporting nested hierarchies.

| Attribute | Type | Description |
|---|---|---|
| folder_id | UUID (unique) | Primary identifier |
| name | String | Display name of the folder |
| parent_id | UUID or ROOT | Parent folder ID; ROOT for top-level folders |
| created_at | Timestamp | When the folder was created |

**Business Rules:**
- Folder names must be unique among siblings (same parent)
- Folders can be nested to arbitrary depth
- S3 keys use folder_id (not name), so renaming has no S3 impact
- Deleting a folder cascade-deletes all sub-folders, files (from S3), file metadata, and assignments
- Only Admin can create, rename, or delete folders

### 1.4 File

Represents a file uploaded to the system.

| Attribute | Type | Description |
|---|---|---|
| file_id | UUID (unique) | Primary identifier |
| name | String | Original file name |
| size | Integer (bytes) | File size |
| s3_key | String | S3 object key: `files/<folder_id>/<file_id>/<name>` |
| folder_id | UUID | The folder this file belongs to |
| uploaded_by | String | Username of the uploader |
| uploaded_at | Timestamp | When the file was uploaded |

**Business Rules:**
- Maximum file size is 1GB; enforced on both client and server
- Files are stored in S3; only metadata is in DynamoDB
- Upload and download happen via time-limited pre-signed URLs (not through API Gateway)
- Admin can delete any file
- Uploader can delete only files where uploaded_by matches their username
- Reader and Viewer cannot delete files
- Files survive user deletion (no cascade)

### 1.5 Assignment

Represents the relationship between a User and a Folder, granting access.

| Attribute | Type | Description |
|---|---|---|
| folder_id | UUID | The folder being assigned |
| username | String | The user being granted access |
| assigned_at | Timestamp | When the assignment was created |

**Business Rules:**
- Only Admin can create or remove assignments
- Assigning a user to a folder implicitly grants access to all sub-folders (resolved at runtime by walking the parent chain)
- Assignments are not duplicated per sub-folder — only the explicit assignment is stored
- Removing an assignment immediately revokes access (no re-login needed)
- Files uploaded by an unassigned user remain in the folder after unassignment

---

## 2. Service Components

These encapsulate the business logic that operates on entities.

### 2.1 Authentication Service

**Purpose:** Manages user login, logout, session lifecycle, and password operations.

**Operates on:** User, Session

**Behaviors:**

| Behavior | Description | Stories |
|---|---|---|
| Login | Validate username + password, create Session, return token + role | US-001 |
| Logout | Delete Session by token, clear client state | US-002 |
| Validate Session | Given a token, return the associated user context (username, role) or reject | US-003, US-025 |
| Change Password | Verify current password, hash and store new password | US-004 |
| Reset Password (Admin) | Generate temp password, update user record, set force_password_change | US-005 |
| Seed Admin | On first deployment, create default Admin user with force_password_change=true | US-006 |
| Force Password Change | On login, detect force_password_change flag and require new password before proceeding | US-005, US-006 |

**Collaborates with:**
- **Authorization Service** — Login returns role used by all subsequent authorization checks
- **User Management Service** — Shares User entity; password reset is triggered from user management UI

### 2.2 User Management Service

**Purpose:** Manages the lifecycle of user accounts (create, read, update, delete/disable).

**Operates on:** User, Session (for invalidation), Assignment (for context during creation/update)

**Behaviors:**

| Behavior | Description | Stories |
|---|---|---|
| Create User | Create user with username, temp password, role, and optional folder assignments | US-007 |
| Update User | Change role, add/remove folder assignments; prevent Admin self-role-change | US-008 |
| Disable User | Set status to disabled, invalidate all active sessions | US-009 |
| Delete User | Remove user record, invalidate sessions; files remain | US-009 |
| List Users | Return all users with role, status, folder assignments; support filtering | US-010 |

**Collaborates with:**
- **Authentication Service** — Session invalidation on disable/delete
- **Folder Management Service** — Creating/updating users may include folder assignments
- **Authorization Service** — All operations require Admin role

### 2.3 Authorization Service

**Purpose:** Centralized enforcement of role-based access control and folder-scoped permissions.

**Operates on:** Session, User, Assignment, Folder (parent chain)

**Behaviors:**

| Behavior | Description | Stories |
|---|---|---|
| Authenticate Request | Extract token from request, validate session, return user context | US-025 |
| Require Admin | Reject non-Admin users with 403 | US-025 |
| Check Folder Access | Given a user and folder, walk the parent chain and check if any ancestor is in the user's assignments | US-025 |
| Enforce Upload Permission | Allow only Admin and Uploader (with folder access) | US-018, US-025 |
| Enforce Download Permission | Allow only Admin and Reader (with folder access) | US-019, US-025 |
| Enforce Delete Permission | Admin: any file; Uploader: own files only | US-021, US-022, US-025 |

**Collaborates with:**
- **Authentication Service** — Depends on session validation
- **Folder Management Service** — Uses folder hierarchy for inheritance checks
- All other services use Authorization Service as a gatekeeper

### 2.4 Folder Management Service

**Purpose:** Manages folder hierarchy and user-folder assignments.

**Operates on:** Folder, Assignment, File (cascade delete), File Store (cascade delete)

**Behaviors:**

| Behavior | Description | Stories |
|---|---|---|
| Create Folder | Create top-level folder (parent=ROOT); validate unique name among siblings | US-011 |
| Create Sub-Folder | Create folder under a parent; validate unique name among siblings | US-012 |
| Rename Folder | Update folder name; validate no sibling conflict; S3 unaffected (keys use IDs) | US-013 |
| Delete Folder | Cascade delete: remove sub-folders, file metadata, S3 objects, and assignments recursively | US-014 |
| List Folders (Admin) | Build full folder tree from root | US-015 |
| List Folders (Non-Admin) | Return only folders the user has access to (direct + inherited), with breadcrumb paths | US-015, US-020 |
| Get Folder Path | Walk parent chain to build a breadcrumb path string | US-012, US-020, US-023 |
| Assign Users | Create assignment record linking user to folder | US-016 |
| Unassign Users | Remove assignment record; access revoked immediately | US-017 |
| List Assignments | List all users assigned to a specific folder | US-016 |
| Resolve Accessible Folders | Given a username, return all folder IDs the user can access (direct assignments + all sub-folders) | US-015, US-020, US-023 |

**Collaborates with:**
- **Authorization Service** — All mutation operations require Admin; read operations are filtered by access
- **File Management Service** — Cascade delete removes files from S3
- **User Management Service** — Assignments can be set during user creation/update

### 2.5 File Management Service

**Purpose:** Manages file upload, download, listing, and deletion via pre-signed URLs and metadata.

**Operates on:** File, Folder (for context), File Store (S3), Pre-Signed URL Generator

**Behaviors:**

| Behavior | Description | Stories |
|---|---|---|
| Request Upload URL | Validate role + folder access + file size (<=1GB), generate pre-signed PUT URL with TTL | US-018, US-026, US-027 |
| Confirm Upload | After successful S3 upload, record file metadata in data store | US-018 |
| Request Download URL | Validate role + folder access, generate pre-signed GET URL with TTL | US-019, US-027 |
| List Files | Return files in a folder + sub-folder entries; respect folder access rules | US-020 |
| Delete File (Admin) | Delete any file from S3 and remove metadata | US-021 |
| Delete File (Uploader) | Delete only own files (uploaded_by matches username) from S3 and metadata | US-022 |
| Validate File Size | Enforce 1GB max on both client side and server side before generating URL | US-026 |

**Collaborates with:**
- **Authorization Service** — Upload requires Admin/Uploader + folder access; download requires Admin/Reader + folder access; delete requires ownership check
- **Folder Management Service** — Needs folder context for access checks and file listing
- **Pre-Signed URL Generator** (infrastructure) — Generates S3 URLs
- **File Store** (infrastructure) — S3 operations for delete

### 2.6 Search & Sort Service

**Purpose:** Enables finding and organizing files across the system.

**Operates on:** File, Folder (for path resolution and access filtering)

**Behaviors:**

| Behavior | Description | Stories |
|---|---|---|
| Search Files by Name | Case-insensitive partial match across accessible folders; return results with folder path | US-023 |
| Search Files (Admin) | Scan all files matching the search term | US-023 |
| Search Files (Non-Admin) | Query files only in accessible folders, filter by search term | US-023 |
| Sort Files | Client-side sort by name, date uploaded, or size; ascending/descending toggle | US-024 |

**Collaborates with:**
- **Authorization Service** — Search results are scoped by folder access
- **Folder Management Service** — Resolve accessible folders for non-Admin; get folder path for results
- **File Management Service** — Shares the same file metadata; search extends the file listing capability

---

## 3. Interface Components

### 3.1 API Layer

Each API group maps to a service component and is backed by a consolidated Lambda function.

#### 3.1.1 Auth API

**Backed by:** Authentication Service

| Endpoint | Method | Auth Required | Admin Only | Service Behavior |
|---|---|---|---|---|
| `/auth/login` | POST | No | No | Login |
| `/auth/logout` | POST | Yes | No | Logout |
| `/auth/change-password` | POST | Yes | No | Change Password |

#### 3.1.2 Users API

**Backed by:** User Management Service

| Endpoint | Method | Auth Required | Admin Only | Service Behavior |
|---|---|---|---|---|
| `/users` | GET | Yes | Yes | List Users |
| `/users` | POST | Yes | Yes | Create User |
| `/users/{username}` | PUT | Yes | Yes | Update User |
| `/users/{username}` | DELETE | Yes | Yes | Delete/Disable User |
| `/users/{username}/reset-password` | POST | Yes | Yes | Reset Password |

#### 3.1.3 Folders API

**Backed by:** Folder Management Service

| Endpoint | Method | Auth Required | Admin Only | Service Behavior |
|---|---|---|---|---|
| `/folders` | GET | Yes | No* | List Folders (filtered by role) |
| `/folders` | POST | Yes | Yes | Create Folder / Sub-Folder |
| `/folders/{folderId}` | PUT | Yes | Yes | Rename Folder |
| `/folders/{folderId}` | DELETE | Yes | Yes | Delete Folder (cascade) |
| `/folders/{folderId}/assignments` | GET | Yes | Yes | List Assignments |
| `/folders/{folderId}/assignments` | POST | Yes | Yes | Assign Users |
| `/folders/{folderId}/assignments/{username}` | DELETE | Yes | Yes | Unassign User |

*Non-Admin users receive a filtered folder list based on their assignments.

#### 3.1.4 Files API

**Backed by:** File Management Service, Search & Sort Service

| Endpoint | Method | Auth Required | Role Restriction | Service Behavior |
|---|---|---|---|---|
| `/folders/{folderId}/files` | GET | Yes | Folder access | List Files |
| `/files/upload-url` | POST | Yes | Admin, Uploader (assigned) | Request Upload URL |
| `/files/confirm-upload` | POST | Yes | Admin, Uploader (assigned) | Confirm Upload |
| `/files/download-url` | POST | Yes | Admin, Reader (assigned) | Request Download URL |
| `/files/{fileId}` | DELETE | Yes | Admin (any), Uploader (own) | Delete File |
| `/files/search` | GET | Yes | Folder access | Search Files by Name |

### 3.2 UI Layer

#### 3.2.1 Authentication Pages

| Page | Access | Description | Stories |
|---|---|---|---|
| Login Page | Unauthenticated | Username + password form; redirects to home on success | US-001 |
| Force Change Password Page | Authenticated (flagged) | Required before proceeding when force_password_change=true | US-005, US-006 |

#### 3.2.2 Common Shell

| Component | Access | Description | Stories |
|---|---|---|---|
| App Layout | All authenticated | Header with logout button, sidebar navigation, content area | US-002 |
| Error Banner | All authenticated | Displays error messages; retry button for network errors | US-030 |
| Breadcrumb Navigation | All authenticated | Shows folder path; clickable to navigate up | US-012, US-020 |

#### 3.2.3 Folder & File Browser Pages

| Page | Access | Description | Stories |
|---|---|---|---|
| Folder Browser | All authenticated | Tree/list view of folders; Admin sees all, others see assigned | US-015, US-020 |
| Folder Detail | All authenticated (with access) | Files + sub-folders in a folder; breadcrumb; role-based actions | US-020 |
| Search Bar | All authenticated | Text input with debounce; results with folder path | US-023 |
| Search Results | All authenticated | File results across accessible folders | US-023 |
| Sortable File Table | All authenticated | Column headers toggle sort; arrow indicators | US-024 |
| Upload Flow | Admin, Uploader | File picker, size validation, progress bar, confirm | US-018, US-026 |
| Download Button | Admin, Reader | Per-file action; hidden for Uploader/Viewer | US-019 |
| Delete Button | Admin (all files), Uploader (own) | Per-file action with confirmation dialog | US-021, US-022 |

#### 3.2.4 Admin Pages

| Page | Access | Description | Stories |
|---|---|---|---|
| User List | Admin | Table of users with role/status filter, edit/delete actions | US-010 |
| Create User | Admin | Form: username, temp password, role, folder assignments | US-007 |
| Edit User | Admin | Form: update role, folder assignments | US-008 |
| User Settings | All authenticated | Change own password form | US-004 |
| Folder Management | Admin | Create, rename, delete folders | US-011–US-014 |
| Folder Assignments | Admin | Assign/unassign users to a folder | US-016, US-017 |

---

## 4. Infrastructure Components

These are the underlying platform services that support the business components.

### 4.1 Data Store (DynamoDB)

**Purpose:** Persistent storage for all entity data using a single-table design.

**Used by:** All service components

| Capability | Description |
|---|---|
| Single-Table Storage | All entities (User, Session, Folder, File, Assignment) share one table with PK/SK patterns |
| Global Secondary Index | GSI-1 enables reverse lookups: users by role, sessions by user, child folders by parent, folders by user, files by uploader |
| TTL Auto-Expiry | Session records are automatically deleted after their TTL expires |
| Conditional Writes | Used for uniqueness enforcement (e.g., duplicate username prevention) |
| Batch Operations | Used for cascade delete of folders (sub-folders, files, assignments) |
| Decimal Serialization | All responses convert DynamoDB Decimal types to JSON-safe int/float |

### 4.2 File Store (S3 — Storage Bucket)

**Purpose:** Stores the actual file content (binary objects).

**Used by:** File Management Service, Folder Management Service (cascade delete)

| Capability | Description |
|---|---|
| Object Storage | Files stored at key: `files/<folder_id>/<file_id>/<original_filename>` |
| Pre-Signed PUT URLs | Used for direct client-to-S3 uploads (bypasses API Gateway) |
| Pre-Signed GET URLs | Used for direct S3-to-client downloads (bypasses API Gateway) |
| Object Deletion | Used during file delete and folder cascade delete |
| CORS Configuration | Allows PUT/GET from the front-end origin |

### 4.3 Pre-Signed URL Generator

**Purpose:** Generates time-limited, scoped URLs for secure direct S3 access.

**Used by:** File Management Service

| Capability | Description |
|---|---|
| Generate Upload URL | Pre-signed PUT URL scoped to a specific S3 key; TTL: 15 min (configurable) |
| Generate Download URL | Pre-signed GET URL scoped to a specific S3 key; TTL: 15 min (configurable) |
| Scope Enforcement | Each URL is locked to one specific S3 object key |
| Expiry Enforcement | Expired URLs return S3 AccessDenied error |

### 4.4 API Gateway

**Purpose:** HTTP entry point for all backend API requests; routes to Lambda functions.

**Used by:** All API interface components

| Capability | Description |
|---|---|
| REST API Routing | Maps HTTP method + path to the correct Lambda function |
| CORS | Configured to allow requests from the front-end origin |
| Request Proxying | Passes full request (headers, body, path params) to Lambda |

### 4.5 Static Website Host (S3 — Frontend Bucket)

**Purpose:** Hosts the React SPA as a static website.

**Used by:** UI Layer

| Capability | Description |
|---|---|
| Static File Hosting | Serves built React assets (HTML, JS, CSS) |
| SPA Routing | index.html returned for all paths (client-side routing) |

### 4.6 Logging (CloudWatch)

**Purpose:** Captures Lambda execution logs for debugging and monitoring.

**Used by:** All service components (via Lambda runtime)

| Capability | Description |
|---|---|
| Error Logging | All Lambda errors are logged to CloudWatch |
| Request Tracing | API Gateway request IDs propagated to Lambda logs |

---

## 5. Component Interactions by User Story

Each row traces the full interaction path from UI through to infrastructure.

**Legend:** UI Page → API Endpoint → Service → Entity → Infrastructure

### Authentication & Session Management

| Story | Interaction Path |
|---|---|
| **US-001: Login** | Login Page → `POST /auth/login` → Authentication Service.Login → User (verify password), Session (create) → Data Store |
| **US-002: Logout** | App Layout (logout button) → `POST /auth/logout` → Authentication Service.Logout → Session (delete) → Data Store |
| **US-003: Session Persistence** | App Layout (on load) → Authentication Service.Validate Session → Session (lookup) → Data Store; if invalid → redirect to Login Page |
| **US-004: Change Password** | User Settings Page → `POST /auth/change-password` → Authentication Service.Change Password → User (update password_hash) → Data Store |
| **US-005: Admin Reset Password** | User List Page → `POST /users/{u}/reset-password` → Authentication Service.Reset Password → User (set temp password + force_password_change) → Data Store |
| **US-006: Admin Seeding** | Deployment trigger → Seed Lambda → Authentication Service.Seed Admin → User (create Admin) → Data Store |

### User Management

| Story | Interaction Path |
|---|---|
| **US-007: Create User** | Create User Page → `POST /users` → Authorization Service.Require Admin → User Management Service.Create User → User (create), Assignment (create if folders specified) → Data Store |
| **US-008: Update User** | Edit User Page → `PUT /users/{u}` → Authorization Service.Require Admin → User Management Service.Update User → User (update role), Assignment (add/remove) → Data Store |
| **US-009: Delete/Disable** | User List Page → `DELETE /users/{u}` → Authorization Service.Require Admin → User Management Service.Delete/Disable → User (delete/update status), Session (invalidate all) → Data Store |
| **US-010: List Users** | User List Page → `GET /users` → Authorization Service.Require Admin → User Management Service.List Users → User (query all) → Data Store |

### Folder Management

| Story | Interaction Path |
|---|---|
| **US-011: Create Folder** | Folder Management Page → `POST /folders` → Authorization Service.Require Admin → Folder Management Service.Create Folder → Folder (create, parent=ROOT) → Data Store |
| **US-012: Create Sub-Folder** | Folder Management Page → `POST /folders` (with parent_id) → Authorization Service.Require Admin → Folder Management Service.Create Sub-Folder → Folder (create with parent ref) → Data Store |
| **US-013: Rename Folder** | Folder Management Page → `PUT /folders/{id}` → Authorization Service.Require Admin → Folder Management Service.Rename → Folder (update name) → Data Store |
| **US-014: Delete Folder** | Folder Management Page → `DELETE /folders/{id}` → Authorization Service.Require Admin → Folder Management Service.Delete (cascade) → Folder, File, Assignment (batch delete) → Data Store + File Store (S3 delete) |
| **US-015: List Folders** | Folder Browser → `GET /folders` → Authorization Service.Authenticate → Folder Management Service.List Folders (Admin: full tree / Non-Admin: filtered) → Folder, Assignment → Data Store |
| **US-016: Assign Users** | Folder Assignments Page → `POST /folders/{id}/assignments` → Authorization Service.Require Admin → Folder Management Service.Assign Users → Assignment (create) → Data Store |
| **US-017: Unassign Users** | Folder Assignments Page → `DELETE /folders/{id}/assignments/{u}` → Authorization Service.Require Admin → Folder Management Service.Unassign → Assignment (delete) → Data Store |

### File Operations

| Story | Interaction Path |
|---|---|
| **US-018: Upload** | Folder Detail (Upload Flow) → `POST /files/upload-url` → Authorization Service.Enforce Upload Permission → File Management Service.Request Upload URL → Pre-Signed URL Generator (PUT URL) → *Client uploads directly to File Store (S3)* → `POST /files/confirm-upload` → File Management Service.Confirm Upload → File (create metadata) → Data Store |
| **US-019: Download** | Folder Detail (Download Button) → `POST /files/download-url` → Authorization Service.Enforce Download Permission → File Management Service.Request Download URL → File (get metadata) → Pre-Signed URL Generator (GET URL) → *Client downloads directly from File Store (S3)* |
| **US-020: List Files** | Folder Detail → `GET /folders/{id}/files` → Authorization Service.Check Folder Access → File Management Service.List Files → File (query by folder), Folder (sub-folders) → Data Store |
| **US-021: Admin Delete File** | Folder Detail (Delete Button) → `DELETE /files/{id}` → Authorization Service.Enforce Delete Permission (Admin: any) → File Management Service.Delete File → File (delete metadata) → Data Store + File Store (S3 delete) |
| **US-022: Uploader Delete Own** | Folder Detail (Delete Button) → `DELETE /files/{id}` → Authorization Service.Enforce Delete Permission (uploaded_by check) → File Management Service.Delete File → File (delete metadata) → Data Store + File Store (S3 delete) |

### Search & Sort

| Story | Interaction Path |
|---|---|
| **US-023: Search** | Search Bar → `GET /files/search?q=term` → Authorization Service.Authenticate → Search & Sort Service.Search Files → Folder Management Service.Resolve Accessible Folders → File (query/scan + filter) → Folder Management Service.Get Folder Path → Data Store |
| **US-024: Sort** | Sortable File Table → *(client-side only)* → Sort files in current view by name/date/size, ascending/descending toggle. No backend interaction. |

### Non-Functional / Cross-Cutting

| Story | Interaction Path |
|---|---|
| **US-025: Authorization** | *(Cross-cutting)* Every API request → API Gateway → Authorization Service.Authenticate Request → Session (validate) → Data Store. Role + folder checks applied per endpoint. |
| **US-026: File Size Validation** | Upload Flow (client-side check) + `POST /files/upload-url` → File Management Service.Validate File Size. Rejected before URL generation if > 1GB. |
| **US-027: Pre-Signed URL Security** | `POST /files/upload-url` or `/files/download-url` → File Management Service → Pre-Signed URL Generator (TTL: 15 min, scoped to S3 key) |
| **US-028: Backend Pattern** | *(Architectural)* API Gateway routes → consolidated Lambda functions → Data Store. SAM deployment. |
| **US-029: Static Frontend** | Static Website Host (S3) serves React SPA → browser → API Gateway endpoints |
| **US-030: Error Handling** | All services → standardized JSON error responses → Error Banner (UI); Lambda errors → Logging (CloudWatch) |

---

## 6. Component Interaction Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              UI LAYER (React SPA)                          │
│                                                                             │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌──────────┐ ┌───────────┐  │
│  │ Login Page │ │  Folder &  │ │   Admin    │ │ Search   │ │  Common   │  │
│  │            │ │   File     │ │   Pages    │ │  Bar &   │ │  Shell    │  │
│  │ Force      │ │  Browser   │ │            │ │  Results │ │           │  │
│  │ Change Pwd │ │            │ │ User Mgmt  │ │          │ │ Layout    │  │
│  │            │ │ Upload     │ │ Folder Mgmt│ │ Sortable │ │ Error     │  │
│  │            │ │ Download   │ │ Assignments│ │ Table    │ │ Banner    │  │
│  │            │ │ Delete     │ │ Settings   │ │          │ │ Breadcrumb│  │
│  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘ └────┬─────┘ └───────────┘  │
│        │              │              │             │                        │
└────────┼──────────────┼──────────────┼─────────────┼────────────────────────┘
         │              │              │             │
         ▼              ▼              ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API GATEWAY (REST API)                              │
│                                                                             │
│   /auth/*          /folders/*/files    /users/*       /files/search         │
│   /auth/login      /files/upload-url   /folders/*     /files/download-url   │
│   /auth/logout     /files/confirm      /folders/*/    /files/{id}           │
│   /auth/change-pwd                      assignments                         │
└────────┬──────────────┬──────────────┬─────────────┬────────────────────────┘
         │              │              │             │
         ▼              ▼              ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          SERVICE LAYER (Lambdas)                            │
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────────┐  │
│  │  Authentication   │  │  Folder Mgmt     │  │  File Mgmt Service      │  │
│  │  Service          │  │  Service         │  │                          │  │
│  │                   │  │                  │  │  + Search & Sort Service │  │
│  │  Login            │  │  Create Folder   │  │                          │  │
│  │  Logout           │  │  Create Sub      │  │  Upload URL              │  │
│  │  Validate Session │  │  Rename          │  │  Confirm Upload          │  │
│  │  Change Password  │  │  Delete (cascade)│  │  Download URL            │  │
│  │  Reset Password   │  │  List Folders    │  │  List Files              │  │
│  │  Seed Admin       │  │  Assign Users    │  │  Delete File             │  │
│  │                   │  │  Unassign Users  │  │  Search Files            │  │
│  ├───────────────────┤  │  Get Folder Path │  │  Validate File Size      │  │
│  │  User Mgmt        │  │  Resolve Access  │  │                          │  │
│  │  Service          │  │                  │  │                          │  │
│  │                   │  │                  │  │                          │  │
│  │  Create User      │  │                  │  │                          │  │
│  │  Update User      │  │                  │  │                          │  │
│  │  Delete/Disable   │  │                  │  │                          │  │
│  │  List Users       │  │                  │  │                          │  │
│  └────────┬──────────┘  └────────┬─────────┘  └────────────┬─────────────┘  │
│           │                      │                          │               │
│  ┌────────┴──────────────────────┴──────────────────────────┴────────────┐  │
│  │                    Authorization Service (cross-cutting)              │  │
│  │  Authenticate Request │ Require Admin │ Check Folder Access          │  │
│  │  Enforce Upload Perm  │ Enforce Download Perm │ Enforce Delete Perm  │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└────────┬──────────────┬──────────────┬─────────────┬────────────────────────┘
         │              │              │             │
         ▼              ▼              ▼             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          ENTITY LAYER                                       │
│                                                                             │
│   ┌────────┐  ┌─────────┐  ┌────────┐  ┌──────┐  ┌────────────┐           │
│   │  User  │  │ Session │  │ Folder │  │ File │  │ Assignment │           │
│   └────┬───┘  └────┬────┘  └───┬────┘  └──┬───┘  └─────┬──────┘           │
│        │           │           │          │            │                    │
└────────┼───────────┼───────────┼──────────┼────────────┼────────────────────┘
         │           │           │          │            │
         ▼           ▼           ▼          ▼            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      INFRASTRUCTURE LAYER                                   │
│                                                                             │
│  ┌───────────────────────┐  ┌──────────────┐  ┌─────────────────────────┐  │
│  │  Data Store           │  │  File Store  │  │  Pre-Signed URL         │  │
│  │  (DynamoDB)           │  │  (S3 Storage)│  │  Generator              │  │
│  │                       │  │              │  │                         │  │
│  │  Single-table design  │  │  Object CRUD │  │  Upload URLs (PUT)     │  │
│  │  GSI-1 reverse lookup │  │  CORS config │  │  Download URLs (GET)   │  │
│  │  TTL auto-expiry      │  │              │  │  TTL: 15 min           │  │
│  └───────────────────────┘  └──────────────┘  └─────────────────────────┘  │
│                                                                             │
│  ┌────────────────────────┐  ┌────────────────────────────────────────────┐ │
│  │  Static Website Host   │  │  Logging (CloudWatch)                     │ │
│  │  (S3 Frontend Bucket)  │  │  Error logs, request tracing              │ │
│  └────────────────────────┘  └────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Key Interaction Flows

```
Upload Flow:
  UI → API GW → Auth Service → File Mgmt Service → Pre-Signed URL Gen
  UI → S3 (direct PUT via pre-signed URL)
  UI → API GW → File Mgmt Service → Data Store (confirm metadata)

Download Flow:
  UI → API GW → Auth Service → File Mgmt Service → Data Store (get metadata)
                                                  → Pre-Signed URL Gen
  UI → S3 (direct GET via pre-signed URL)

Search Flow:
  UI → API GW → Auth Service → Search Service → Folder Mgmt Service (resolve access)
                                               → Data Store (query/scan files)
                                               → Folder Mgmt Service (get paths)

Authorization Flow (every request):
  API GW → Auth Service.Validate Session → Data Store (session lookup)
         → Auth Service.Check Role/Folder Access → Data Store (assignment lookup)
```

---

