# Unit 2: Auth, Sessions & User Management — Tasks

## Backend Tasks

- [ ] **T2.1**: Implement `shared/auth_middleware.py` — `authenticate()`, `require_auth`, `require_admin` decorators
- [ ] **T2.2**: Implement `handle_login` — validate credentials, create session, return token
- [ ] **T2.3**: Implement `handle_logout` — delete session from DynamoDB
- [ ] **T2.4**: Implement `handle_change_password` — verify current password, hash new password, update record
- [ ] **T2.5**: Implement `handle_reset_password` — generate temp password, set force_password_change flag
- [ ] **T2.6**: Implement `handle_create_user` — create user with role, reject duplicates
- [ ] **T2.7**: Implement `handle_update_user` — update role/status, prevent Admin self-role-change
- [ ] **T2.8**: Implement `handle_delete_user` — delete user record + invalidate sessions, prevent self-delete
- [ ] **T2.9**: Implement `handle_list_users` — query/scan with optional role/status filter
- [ ] **T2.10**: Implement seed Lambda — create default Admin account as CloudFormation Custom Resource
- [ ] **T2.11**: Add bcrypt Lambda layer or bundle bcrypt in deployment package
- [ ] **T2.12**: Update SAM template: wire `auth-users` Lambda to API Gateway routes, add seed Lambda

## Frontend Tasks

- [ ] **T2.13**: Build Login page — form, API call, store token in localStorage, redirect
- [ ] **T2.14**: Build Force Change Password page — shown when `force_password_change=true`
- [ ] **T2.15**: Build auth context/provider — store token + role, provide `isAuthenticated`, `isAdmin`
- [ ] **T2.16**: Build protected route wrapper — redirect to `/login` if unauthenticated
- [ ] **T2.17**: Add logout button to Layout header — clear token, redirect to `/login`
- [ ] **T2.18**: Build User Settings page — change own password form
- [ ] **T2.19**: Build Admin User List page — table with filter by role/status, edit/delete actions
- [ ] **T2.20**: Build Admin Create User page — form with username, temp password, role picker
- [ ] **T2.21**: Build Admin Edit User page — update role, folder assignment display (assignment editing deferred to Unit 3)

## Integration Test Tasks

- [ ] **T2.22**: Test POST `/auth/login` — valid credentials → 200 + token; invalid → 401
- [ ] **T2.23**: Test POST `/auth/logout` — valid token → 200; reuse token → 401
- [ ] **T2.24**: Test POST `/auth/change-password` — correct old password → 200; wrong → 400
- [ ] **T2.25**: Test POST `/users` — Admin creates user → 201; duplicate → 409; non-Admin → 403
- [ ] **T2.26**: Test PUT `/users/{username}` — Admin updates role → 200; self-role-change → 400
- [ ] **T2.27**: Test DELETE `/users/{username}` — Admin deletes user → 200; self-delete → 400; non-Admin → 403
- [ ] **T2.28**: Test GET `/users` — Admin → 200 + list; non-Admin → 403
- [ ] **T2.29**: Test POST `/users/{username}/reset-password` — Admin → 200 + temp password; non-Admin → 403
- [ ] **T2.30**: Test session expiry — wait for TTL, verify token returns 401
