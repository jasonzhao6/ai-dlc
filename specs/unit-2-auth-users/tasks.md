# Unit 2: Auth, Sessions & User Management — Tasks

## Backend Tasks

- [x] **T2.1**: Implement `shared/auth_middleware.py` — `authenticate()`, `require_auth`, `require_admin` decorators
- [x] **T2.2**: Implement `handle_login` — validate credentials, create session, return token
- [x] **T2.3**: Implement `handle_logout` — delete session from DynamoDB
- [x] **T2.4**: Implement `handle_change_password` — verify current password, hash new password, update record
- [x] **T2.5**: Implement `handle_reset_password` — generate temp password, set force_password_change flag
- [x] **T2.6**: Implement `handle_create_user` — create user with role, reject duplicates
- [x] **T2.7**: Implement `handle_update_user` — update role/status, prevent Admin self-role-change
- [x] **T2.8**: Implement `handle_delete_user` — delete user record + invalidate sessions, prevent self-delete
- [x] **T2.9**: Implement `handle_list_users` — query/scan with optional role/status filter
- [x] **T2.10**: Implement seed Lambda — create default Admin account as CloudFormation Custom Resource
- [x] **T2.11**: Add bcrypt Lambda layer or bundle bcrypt in deployment package
- [x] **T2.12**: Update SAM template: wire `auth-users` Lambda to API Gateway routes, add seed Lambda

## Frontend Tasks

- [x] **T2.13**: Build Login page — form, API call, store token in localStorage, redirect
- [x] **T2.14**: Build Force Change Password page — shown when `force_password_change=true`
- [x] **T2.15**: Build auth context/provider — store token + role, provide `isAuthenticated`, `isAdmin`
- [x] **T2.16**: Build protected route wrapper — redirect to `/login` if unauthenticated
- [x] **T2.17**: Add logout button to Layout header — clear token, redirect to `/login`
- [x] **T2.18**: Build User Settings page — change own password form
- [x] **T2.19**: Build Admin User List page — table with filter by role/status, edit/delete actions
- [x] **T2.20**: Build Admin Create User page — form with username, temp password, role picker (integrated as modal in User List)
- [x] **T2.21**: Build Admin Edit User page — update role, folder assignment display (integrated as modal in User List, assignment editing deferred to Unit 3)

## Integration Test Tasks

- [x] **T2.22**: Test POST `/auth/login` — valid credentials → 200 + token; invalid → 401
- [x] **T2.23**: Test POST `/auth/logout` — valid token → 200; reuse token → 401
- [x] **T2.24**: Test POST `/auth/change-password` — correct old password → 200; wrong → 400
- [x] **T2.25**: Test POST `/users` — Admin creates user → 201; duplicate → 409; non-Admin → 403
- [x] **T2.26**: Test PUT `/users/{username}` — Admin updates role → 200; self-role-change → 400
- [x] **T2.27**: Test DELETE `/users/{username}` — Admin deletes user → 200; self-delete → 400; non-Admin → 403
- [x] **T2.28**: Test GET `/users` — Admin → 200 + list; non-Admin → 403
- [x] **T2.29**: Test POST `/users/{username}/reset-password` — Admin → 200 + temp password; non-Admin → 403
- [ ] **T2.30**: Test session expiry — wait for TTL, verify token returns 401
