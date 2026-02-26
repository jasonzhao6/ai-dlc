# Unit 2: Auth, Sessions & User Management — Requirements

## Dependencies

- **Depends on**: Unit 1 (DynamoDB table, API Gateway, SAM template, shared utilities)

## Stories Covered

| Story | Title | Summary |
|---|---|---|
| US-001 | User Login | Login with username/password, create session in DynamoDB |
| US-002 | User Logout | Terminate session, delete from DynamoDB |
| US-003 | Session Persistence | Session persists across page refreshes via DynamoDB validation |
| US-004 | Change Own Password | Authenticated user changes their password |
| US-005 | Admin Reset User Password | Admin generates temp password for another user |
| US-006 | Initial Admin Account Seeding | Default admin created on first deployment |
| US-007 | Create User | Admin creates user with role and folder assignments |
| US-008 | Update User | Admin updates user role and folder assignments |
| US-009 | Delete/Disable User | Admin disables or deletes a user, invalidates sessions |
| US-010 | List Users | Admin views all users with filtering |
| US-025 | Role-Based Authorization | Session validation + role enforcement on every API request |

## Functional Requirements

### FR-1: Authentication (US-001, US-002, US-003)
- Login: validate credentials against DynamoDB, return session token
- Logout: delete session record from DynamoDB
- Session validation: every API request must include a session token; validate against DynamoDB
- Sessions expire via DynamoDB TTL (configurable, default 24 hours)
- Invalid/expired tokens return 401 Unauthorized

### FR-2: Password Management (US-004, US-005, US-006)
- Change password: requires current password + new password, updates DynamoDB
- Admin reset: generates temp password, sets `force_password_change=true`
- First-login password change: if `force_password_change=true`, user must set new password before proceeding
- Password hashing: use bcrypt or equivalent
- Minimum password length: 8 characters

### FR-3: Admin Account Seeding (US-006)
- On first deployment, a seed Lambda creates a default Admin account
- Default credentials documented in deployment guide
- Admin is forced to change password on first login

### FR-4: User CRUD (US-007, US-008, US-009, US-010)
- Create: username, temp password, role (Uploader/Reader/Viewer), optional folder assignments
- Update: change role, add/remove folder assignments; cannot change own role away from Admin
- Delete: remove user record + invalidate sessions; cannot delete self; files remain
- Disable: set status to disabled, invalidate sessions; cannot disable self
- List: return all users with role, status, folder assignments; supports filtering by role/status

### FR-5: Authorization Middleware (US-025)
- Centralized function in `shared/auth_middleware.py`
- Validates session token from request header
- Extracts user role and username
- Admin-only endpoints reject non-Admin users with 403
- Folder-scoped operations check user-folder assignments

## Non-Functional Requirements

- Passwords must never be stored in plaintext
- Session tokens must be cryptographically random (e.g., uuid4 or secrets.token_urlsafe)
- Error messages must not reveal whether username or password was wrong
- All auth endpoints must be rate-limit-safe (no sensitive info in error responses)
