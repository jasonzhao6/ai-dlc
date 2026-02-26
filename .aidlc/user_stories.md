# User Stories — S3 File-Sharing System

## Personas

| Persona | Description |
|---|---|
| **Admin** | Full system access. Manages users, folders, folder assignments, and all file operations. A single admin account is seeded at initial build. |
| **Uploader** | Can view and upload files to assigned folders. Can delete their own uploaded files. Cannot download. |
| **Reader** | Can view and download files from assigned folders. Cannot upload or delete. |
| **Viewer** | Can view (list/browse) files in assigned folders only. Cannot download, upload, or delete. |

## Permissions Matrix

| Action | Admin | Uploader | Reader | Viewer |
|---|---|---|---|---|
| **Users** | | | | |
| Create user | Yes | - | - | - |
| Update user | Yes | - | - | - |
| Delete/disable user | Yes | - | - | - |
| List users | Yes | - | - | - |
| **Folders** | | | | |
| Create folder / sub-folder | Yes | - | - | - |
| Rename folder | Yes | - | - | - |
| Delete folder | Yes | - | - | - |
| List all folders | Yes | - | - | - |
| Browse assigned folders | Yes | Assigned only | Assigned only | Assigned only |
| Navigate folder hierarchy | Yes | Assigned only | Assigned only | Assigned only |
| Assign users to folders | Yes | - | - | - |
| **Files** | | | | |
| Upload file (pre-signed URL) | Yes | Assigned folders | - | - |
| Download file (pre-signed URL) | Yes | - | Assigned folders | - |
| View/list files | Yes | Assigned folders | Assigned folders | Assigned folders |
| Delete any file | Yes | - | - | - |
| Delete own uploaded file | Yes | Yes | - | - |
| **Search & Sort** | | | | |
| Search files by name | Yes | Assigned folders | Assigned folders | Assigned folders |
| Sort by name/date/size | Yes | Assigned folders | Assigned folders | Assigned folders |
| **Authentication** | | | | |
| Login | Yes | Yes | Yes | Yes |
| Logout | Yes | Yes | Yes | Yes |
| Change own password | Yes | Yes | Yes | Yes |
| Reset other user's password | Yes | - | - | - |

---

## Authentication & Session Management

### US-001: User Login
**As a** user (any persona),
**I want to** log in with my username and password,
**So that** I can access the file-sharing system according to my role.

**Acceptance Criteria:**
- [ ] AC1: System presents a login form with username and password fields
- [ ] AC2: On valid credentials, a session is created in DynamoDB and the user is redirected to their home view
- [ ] AC3: On invalid credentials, an error message is displayed without revealing which field was wrong
- [ ] AC4: Session token is stored client-side and sent with subsequent API requests
- [ ] AC5: Login API is exposed via API Gateway backed by a Python Lambda function

### US-002: User Logout
**As a** user (any persona),
**I want to** log out of the system,
**So that** my session is terminated and no one else can use it.

**Acceptance Criteria:**
- [ ] AC1: A logout action is available from any page in the application
- [ ] AC2: On logout, the session record is deleted from DynamoDB
- [ ] AC3: The client-side session token is cleared
- [ ] AC4: After logout, any API call with the old token returns 401 Unauthorized

### US-003: Session Persistence
**As a** user (any persona),
**I want** my session to persist across page refreshes,
**So that** I don't have to log in again every time I reload the page.

**Acceptance Criteria:**
- [ ] AC1: Session token is persisted in browser storage (e.g., localStorage)
- [ ] AC2: On page load, the app validates the stored token against DynamoDB
- [ ] AC3: If the session is valid, the user is taken to their home view
- [ ] AC4: If the session is expired or invalid, the user is redirected to the login page
- [ ] AC5: Sessions have a configurable TTL in DynamoDB

### US-004: Change Own Password
**As a** user (any persona),
**I want to** change my own password,
**So that** I can keep my account secure.

**Acceptance Criteria:**
- [ ] AC1: A change-password form is accessible from the user's profile/settings
- [ ] AC2: User must provide current password and new password (with confirmation)
- [ ] AC3: New password must meet minimum length/complexity requirements
- [ ] AC4: On success, the password is updated and the user remains logged in
- [ ] AC5: On failure (e.g., wrong current password), an appropriate error is shown

### US-005: Admin Reset User Password
**As an** Admin,
**I want to** reset another user's password,
**So that** I can help users who are locked out of their accounts.

**Acceptance Criteria:**
- [ ] AC1: Admin can select a user and trigger a password reset from the user management view
- [ ] AC2: A temporary password is generated and displayed to the Admin
- [ ] AC3: The target user's password is updated in DynamoDB
- [ ] AC4: On next login with the temporary password, the user is prompted to set a new password
- [ ] AC5: Only Admin persona can perform this action; other roles receive 403 Forbidden

### US-006: Initial Admin Account Seeding
**As a** system deployer,
**I want** a default Admin account to be created during initial system setup,
**So that** there is an admin who can configure the system from the start.

**Acceptance Criteria:**
- [ ] AC1: On first deployment, a single Admin account is created with a known default username and password
- [ ] AC2: The default credentials are documented in the deployment guide
- [ ] AC3: The Admin is prompted to change the default password on first login
- [ ] AC4: No other accounts exist after initial setup

---

## Admin: User Management

### US-007: Create User
**As an** Admin,
**I want to** create a new user account with a specific role and folder assignments,
**So that** new people can access the system with appropriate permissions.

**Acceptance Criteria:**
- [ ] AC1: Admin can specify username, temporary password, role (Uploader/Reader/Viewer), and folder assignments
- [ ] AC2: User record is created in DynamoDB with the specified attributes
- [ ] AC3: Duplicate usernames are rejected with a clear error message
- [ ] AC4: The new user can log in immediately with the provided credentials
- [ ] AC5: The new user is prompted to change their temporary password on first login
- [ ] AC6: Only Admin persona can perform this action; other roles receive 403 Forbidden

### US-008: Update User
**As an** Admin,
**I want to** update an existing user's role and folder assignments,
**So that** I can adjust their access as needs change.

**Acceptance Criteria:**
- [ ] AC1: Admin can change a user's role (Uploader/Reader/Viewer)
- [ ] AC2: Admin can add or remove folder assignments for the user
- [ ] AC3: Changes take effect on the user's next API request (no re-login required)
- [ ] AC4: Admin cannot change their own role away from Admin (prevent lockout)
- [ ] AC5: Updated user record is persisted in DynamoDB

### US-009: Delete/Disable User
**As an** Admin,
**I want to** disable or delete a user account,
**So that** former users can no longer access the system.

**Acceptance Criteria:**
- [ ] AC1: Admin can disable a user account, which prevents login but retains the record
- [ ] AC2: Admin can permanently delete a user account and its data from DynamoDB
- [ ] AC3: Active sessions for the disabled/deleted user are immediately invalidated
- [ ] AC4: Admin cannot delete or disable their own account
- [ ] AC5: Files uploaded by the deleted user remain in the system (they are not cascade-deleted)

### US-010: List Users
**As an** Admin,
**I want to** view a list of all user accounts,
**So that** I can manage the user base.

**Acceptance Criteria:**
- [ ] AC1: Admin sees a table of all users with columns: username, role, status (active/disabled), folder assignments
- [ ] AC2: The list supports filtering by role and status
- [ ] AC3: From this list, Admin can navigate to update or delete a user
- [ ] AC4: Only Admin persona can access this view; other roles receive 403 Forbidden

---

## Admin: Folder Management

### US-011: Create Folder
**As an** Admin,
**I want to** create a new top-level folder,
**So that** I can organize files into logical groupings.

**Acceptance Criteria:**
- [ ] AC1: Admin can specify a folder name
- [ ] AC2: Folder metadata is stored in DynamoDB (name, parent=null, created date)
- [ ] AC3: Duplicate folder names at the same level are rejected with an error
- [ ] AC4: The folder appears in the folder listing immediately after creation
- [ ] AC5: Only Admin persona can create folders; other roles receive 403 Forbidden

### US-012: Create Sub-Folder
**As an** Admin,
**I want to** create a sub-folder inside an existing folder,
**So that** I can organize files in a nested hierarchy.

**Acceptance Criteria:**
- [ ] AC1: Admin can create a folder within any existing folder
- [ ] AC2: Sub-folder metadata includes a reference to its parent folder ID in DynamoDB
- [ ] AC3: Duplicate folder names within the same parent are rejected
- [ ] AC4: There is no hard limit on nesting depth, but the UI displays the full path (breadcrumb)
- [ ] AC5: Sub-folders inherit no automatic user assignments — assignments are explicit

### US-013: Rename Folder
**As an** Admin,
**I want to** rename an existing folder,
**So that** I can correct or update folder names as needed.

**Acceptance Criteria:**
- [ ] AC1: Admin can rename any folder from the folder management view
- [ ] AC2: The new name must not conflict with sibling folders at the same level
- [ ] AC3: Renaming a folder does not affect its contents or sub-folders
- [ ] AC4: The S3 key prefix is updated accordingly (or the system uses DynamoDB IDs, not names, for S3 paths)
- [ ] AC5: User assignments to the folder are preserved after rename

### US-014: Delete Folder
**As an** Admin,
**I want to** delete a folder,
**So that** I can remove folders that are no longer needed.

**Acceptance Criteria:**
- [ ] AC1: Admin can delete a folder from the folder management view
- [ ] AC2: If the folder contains files or sub-folders, Admin is warned and must confirm deletion
- [ ] AC3: On confirmed deletion, all files within the folder (and sub-folders) are deleted from S3
- [ ] AC4: All sub-folder records and file metadata are removed from DynamoDB
- [ ] AC5: User assignments to the deleted folder are cleaned up

### US-015: List and Browse Folders
**As an** Admin,
**I want to** see all folders in a hierarchical view,
**So that** I can manage the folder structure.

**Acceptance Criteria:**
- [ ] AC1: Admin sees all folders displayed in a tree or nested list
- [ ] AC2: Each folder shows its name, number of files, and number of assigned users
- [ ] AC3: Admin can expand/collapse folder hierarchies
- [ ] AC4: Admin can click into a folder to view its contents (files and sub-folders)

### US-016: Assign Users to Folders
**As an** Admin,
**I want to** assign one or more users to a folder,
**So that** those users can access the folder according to their role.

**Acceptance Criteria:**
- [ ] AC1: Admin can select a folder and assign users to it
- [ ] AC2: Admin can assign multiple users to a folder at once
- [ ] AC3: Assigning a user to a parent folder grants access to all its sub-folders
- [ ] AC4: Assignments are stored in DynamoDB and take effect immediately
- [ ] AC5: Admin can view which users are currently assigned to a folder

### US-017: Unassign Users from Folders
**As an** Admin,
**I want to** remove a user's assignment from a folder,
**So that** they can no longer access that folder.

**Acceptance Criteria:**
- [ ] AC1: Admin can remove one or more users from a folder's assignment list
- [ ] AC2: Unassigned users immediately lose access to the folder and its sub-folders
- [ ] AC3: Files uploaded by the unassigned user remain in the folder
- [ ] AC4: The change is reflected in the user's next API request without re-login

---

## File Operations

### US-018: Upload File
**As an** Admin or Uploader,
**I want to** upload a file to a folder I have access to,
**So that** the file is stored and available to other authorized users.

**Acceptance Criteria:**
- [ ] AC1: User selects a folder and chooses a file to upload
- [ ] AC2: The system generates an S3 pre-signed URL for upload via a Lambda function
- [ ] AC3: The file is uploaded directly to S3 using the pre-signed URL (not through API Gateway)
- [ ] AC4: Files up to 1GB are accepted; files exceeding 1GB are rejected with an error before upload begins
- [ ] AC5: File metadata (name, size, upload date, uploader username, folder ID) is stored in DynamoDB
- [ ] AC6: Uploader can only upload to their assigned folders; unauthorized attempts return 403 Forbidden
- [ ] AC7: Upload progress is shown in the UI

### US-019: Download File
**As an** Admin or Reader,
**I want to** download a file from a folder I have access to,
**So that** I can use the file locally.

**Acceptance Criteria:**
- [ ] AC1: User selects a file and clicks download
- [ ] AC2: The system generates an S3 pre-signed URL for download via a Lambda function
- [ ] AC3: The file is downloaded directly from S3 using the pre-signed URL
- [ ] AC4: Reader can only download from their assigned folders; unauthorized attempts return 403 Forbidden
- [ ] AC5: Uploader and Viewer personas cannot download; the download action is hidden or disabled for them

### US-020: View/List Files in a Folder
**As a** user (any persona with folder access),
**I want to** view the list of files in a folder,
**So that** I can see what files are available.

**Acceptance Criteria:**
- [ ] AC1: Navigating into a folder displays a list of files and sub-folders
- [ ] AC2: Each file entry shows: file name, file size, upload date, uploader name
- [ ] AC3: Each sub-folder entry shows: folder name, file count
- [ ] AC4: Users only see folders they are assigned to (except Admin who sees all)
- [ ] AC5: Breadcrumb navigation shows the current folder path and allows navigating up

### US-021: Admin Delete Any File
**As an** Admin,
**I want to** delete any file in the system,
**So that** I can remove inappropriate or unnecessary files.

**Acceptance Criteria:**
- [ ] AC1: Admin can select one or more files and delete them
- [ ] AC2: A confirmation prompt is shown before deletion
- [ ] AC3: On confirmation, the file is deleted from S3 and its metadata is removed from DynamoDB
- [ ] AC4: Only Admin persona can delete files they did not upload; other roles receive 403 Forbidden

### US-022: Uploader Delete Own File
**As an** Uploader,
**I want to** delete a file that I uploaded,
**So that** I can remove files I uploaded by mistake or that are no longer needed.

**Acceptance Criteria:**
- [ ] AC1: Uploader sees a delete action only on files they uploaded
- [ ] AC2: A confirmation prompt is shown before deletion
- [ ] AC3: On confirmation, the file is deleted from S3 and its metadata is removed from DynamoDB
- [ ] AC4: Uploader cannot delete files uploaded by other users; the delete action is hidden for those files

---

## Search & Sort

### US-023: Search Files by Name
**As a** user (any persona with folder access),
**I want to** search for files by name within the folders I have access to,
**So that** I can quickly find a specific file.

**Acceptance Criteria:**
- [ ] AC1: A search input is available on the file browsing view
- [ ] AC2: Search is case-insensitive and supports partial name matches
- [ ] AC3: Results are scoped to the user's assigned folders only (Admin sees all)
- [ ] AC4: Search results display the same columns as the file list (name, size, date, uploader)
- [ ] AC5: Each result shows the folder path so the user knows where the file is located

### US-024: Sort Files
**As a** user (any persona with folder access),
**I want to** sort the file list by name, date uploaded, or file size,
**So that** I can organize the view to find what I need.

**Acceptance Criteria:**
- [ ] AC1: Clickable column headers for Name, Date Uploaded, and Size toggle sorting
- [ ] AC2: Each column supports ascending and descending sort
- [ ] AC3: A visual indicator (arrow) shows the current sort column and direction
- [ ] AC4: Default sort order is alphabetical by name (ascending)
- [ ] AC5: Sort state persists while navigating within the same folder

---

## Non-Functional / Cross-Cutting

### US-025: Role-Based Authorization Enforcement
**As a** system,
**I want to** enforce role-based access on every API request,
**So that** users can only perform actions permitted by their role and folder assignments.

**Acceptance Criteria:**
- [ ] AC1: Every API Gateway endpoint validates the session token and extracts the user's role
- [ ] AC2: Folder-scoped operations verify the user is assigned to the target folder
- [ ] AC3: Unauthorized requests return 403 Forbidden with no sensitive information leaked
- [ ] AC4: Admin-only endpoints (user management, folder management) reject non-Admin users
- [ ] AC5: Authorization logic is centralized (shared across Lambda functions, not duplicated)

### US-026: File Size Validation
**As a** system,
**I want to** enforce a maximum file size of 1GB,
**So that** excessively large files don't consume storage or degrade performance.

**Acceptance Criteria:**
- [ ] AC1: The front-end validates file size before requesting a pre-signed URL and rejects files over 1GB
- [ ] AC2: The Lambda that generates pre-signed URLs also validates the declared file size
- [ ] AC3: A clear error message is shown to the user when a file exceeds the limit

### US-027: Pre-Signed URL Security
**As a** system,
**I want** pre-signed URLs to have a short expiry time,
**So that** URLs cannot be shared or reused beyond their intended window.

**Acceptance Criteria:**
- [ ] AC1: Upload pre-signed URLs expire after a configurable TTL (default: 15 minutes)
- [ ] AC2: Download pre-signed URLs expire after a configurable TTL (default: 15 minutes)
- [ ] AC3: Expired URLs return an appropriate S3 error
- [ ] AC4: Each pre-signed URL is scoped to the specific S3 object key

### US-028: API Gateway + Lambda Backend Pattern
**As a** developer,
**I want** all server-side functionality (except pre-signed URL uploads) to be implemented as API Gateway + Python Lambda functions,
**So that** the architecture follows the defined technical stack.

**Acceptance Criteria:**
- [ ] AC1: Each API resource (auth, users, folders, files) is backed by a consolidated Lambda function handling CRUD operations
- [ ] AC2: Lambda functions are written in Python using the locally installed Python version
- [ ] AC3: AWS SAM is used for deployment without containers
- [ ] AC4: Every API Gateway endpoint has an integration test (HTTPS call with response validation)
- [ ] AC5: DynamoDB Decimal values are properly serialized to JSON (not using default Decimal type)

### US-029: Static Front-End Hosting
**As a** user,
**I want** the web application to be a React JS static site hosted on S3,
**So that** it loads quickly and is easy to deploy.

**Acceptance Criteria:**
- [ ] AC1: The front-end is a React JS single-page application
- [ ] AC2: Built assets are deployed to an S3 bucket configured for static website hosting
- [ ] AC3: The front-end communicates with the backend exclusively via API Gateway endpoints
- [ ] AC4: The UI is responsive and works on desktop browsers

### US-030: Error Handling
**As a** user,
**I want** clear and helpful error messages when something goes wrong,
**So that** I understand what happened and what to do next.

**Acceptance Criteria:**
- [ ] AC1: API errors return consistent JSON format: `{ "error": "<message>" }` with appropriate HTTP status codes
- [ ] AC2: The front-end displays user-friendly error messages (not raw technical errors)
- [ ] AC3: Network errors (timeouts, connection failures) show a retry option
- [ ] AC4: Lambda functions log errors to CloudWatch for debugging

---

