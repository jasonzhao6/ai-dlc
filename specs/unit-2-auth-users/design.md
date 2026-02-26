# Unit 2: Auth, Sessions & User Management — Design

## Lambda: `auth-users`

Single consolidated Lambda handling all auth and user management routes.

### Handler Routing

```python
# backend/auth_users/handler.py

def lambda_handler(event, context):
    method = event["httpMethod"]
    path = event["resource"]

    routes = {
        ("POST", "/auth/login"): handle_login,
        ("POST", "/auth/logout"): handle_logout,
        ("POST", "/auth/change-password"): handle_change_password,
        ("GET", "/users"): handle_list_users,
        ("POST", "/users"): handle_create_user,
        ("PUT", "/users/{username}"): handle_update_user,
        ("DELETE", "/users/{username}"): handle_delete_user,
        ("POST", "/users/{username}/reset-password"): handle_reset_password,
    }

    handler = routes.get((method, path))
    if not handler:
        return error("Not found", 404)
    return handler(event, context)
```

### Authentication Flow

```
Client                    API Gateway              Lambda                  DynamoDB
  |--- POST /auth/login --->|--- invoke --->|                               |
  |                          |               |--- GetItem USER#username ---->|
  |                          |               |<-- user record ---------------|
  |                          |               |    verify password hash       |
  |                          |               |--- PutItem SESSION#token ---->|
  |                          |<-- 200 + token|                               |
  |<-- { token, role } ------|               |                               |
```

### Session Token Format

- Generated via `secrets.token_urlsafe(32)` — 43-character URL-safe string
- Stored in DynamoDB: `PK=SESSION#<token>`, `SK=SESSION`
- Attributes: `username`, `role`, `created_at`, `ttl` (epoch seconds)
- Client stores token in `localStorage` and sends as `Authorization: Bearer <token>` header

### Password Hashing

- Library: `bcrypt` (included as Lambda layer or bundled)
- Hash on create/change, verify on login
- Salt rounds: 12 (default)

### Authorization Middleware

```python
# backend/shared/auth_middleware.py

def authenticate(event):
    """Validate session token, return user context or None."""
    token = extract_token(event)  # from Authorization header
    if not token:
        return None
    session = db.get_item(PK=f"SESSION#{token}", SK="SESSION")
    if not session:
        return None
    return {"username": session["username"], "role": session["role"]}

def require_auth(handler):
    """Decorator: rejects unauthenticated requests with 401."""
    def wrapper(event, context):
        user = authenticate(event)
        if not user:
            return error("Unauthorized", 401)
        event["user"] = user
        return handler(event, context)
    return wrapper

def require_admin(handler):
    """Decorator: rejects non-Admin requests with 403."""
    def wrapper(event, context):
        user = event.get("user")
        if not user or user["role"] != "Admin":
            return error("Forbidden", 403)
        return handler(event, context)
    return wrapper
```

### API Routes

| Method | Path | Auth | Admin | Handler |
|---|---|---|---|---|
| POST | `/auth/login` | No | No | `handle_login` |
| POST | `/auth/logout` | Yes | No | `handle_logout` |
| POST | `/auth/change-password` | Yes | No | `handle_change_password` |
| GET | `/users` | Yes | Yes | `handle_list_users` |
| POST | `/users` | Yes | Yes | `handle_create_user` |
| PUT | `/users/{username}` | Yes | Yes | `handle_update_user` |
| DELETE | `/users/{username}` | Yes | Yes | `handle_delete_user` |
| POST | `/users/{username}/reset-password` | Yes | Yes | `handle_reset_password` |

### DynamoDB Operations

| Operation | Key Pattern | Notes |
|---|---|---|
| Login: get user | PK=`USER#<username>`, SK=`PROFILE` | Verify password hash |
| Login: create session | PK=`SESSION#<token>`, SK=`SESSION` | Set TTL |
| Logout: delete session | PK=`SESSION#<token>`, SK=`SESSION` | |
| Change password | PK=`USER#<username>`, SK=`PROFILE` | Update password_hash |
| Reset password | PK=`USER#<username>`, SK=`PROFILE` | Set force_password_change=true |
| Create user | PK=`USER#<username>`, SK=`PROFILE` | ConditionExpression: attribute_not_exists |
| Update user | PK=`USER#<username>`, SK=`PROFILE` | Update role, status |
| Delete user | PK=`USER#<username>`, SK=`PROFILE` | Also query+delete sessions via GSI1 |
| Disable user | PK=`USER#<username>`, SK=`PROFILE` | Set status=disabled, delete sessions |
| List users | GSI1: GSI1PK=`ROLE#<role>` or Scan | Filter by role/status |

### React Pages

| Page | Route | Description |
|---|---|---|
| Login | `/login` | Username + password form, redirects to home on success |
| Force Change Password | `/change-password` | Shown after login when `force_password_change=true` |
| User Settings | `/settings` | Change own password form |
| User List (Admin) | `/admin/users` | Table of all users with filter, edit, delete actions |
| Create User (Admin) | `/admin/users/new` | Form: username, temp password, role, folder assignments |
| Edit User (Admin) | `/admin/users/:username` | Form: update role, folder assignments |

### Seed Lambda

- Triggered as a CloudFormation Custom Resource on stack creation
- Creates Admin user: `PK=USER#admin`, `SK=PROFILE`
- Default password: `ChangeMe123!` (documented in README)
- Sets `force_password_change=true`
