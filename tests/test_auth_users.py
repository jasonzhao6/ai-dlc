"""Integration tests for auth/user endpoints against SAM local API."""
import json
import sys
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:3000"

passed = 0
failed = 0
admin_token = None


def request(method, path, body=None, token=None):
    """Make an HTTP request and return (status_code, response_body_dict)."""
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode('utf-8') if body else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header('Content-Type', 'application/json')
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    try:
        resp = urllib.request.urlopen(req)
        return resp.status, json.loads(resp.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        body_str = e.read().decode('utf-8')
        try:
            return e.code, json.loads(body_str)
        except json.JSONDecodeError:
            return e.code, {'raw': body_str}


def test(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name} {detail}")


def main():
    global admin_token

    # ============================================================
    # T2.22: Login tests
    # ============================================================
    print("\n=== T2.22: POST /auth/login ===")

    # Valid credentials
    status, body = request('POST', '/auth/login', {
        'username': 'admin', 'password': 'ChangeMe123!'
    })
    test("Valid login returns 200", status == 200, f"got {status}")
    test("Valid login returns token", 'token' in body, f"body: {body}")
    test("Valid login returns username", body.get('username') == 'admin')
    test("Valid login returns role", body.get('role') == 'Admin')
    test("Valid login returns force_password_change", body.get('force_password_change') is True)
    admin_token = body.get('token')

    # Invalid password
    status, body = request('POST', '/auth/login', {
        'username': 'admin', 'password': 'wrongpassword'
    })
    test("Invalid password returns 401", status == 401, f"got {status}")

    # Missing fields
    status, body = request('POST', '/auth/login', {'username': 'admin'})
    test("Missing password returns 400", status == 400, f"got {status}")

    # Non-existent user
    status, body = request('POST', '/auth/login', {
        'username': 'nouser', 'password': 'anything'
    })
    test("Non-existent user returns 401", status == 401, f"got {status}")

    # ============================================================
    # T2.25: Create User (Admin only)
    # ============================================================
    print("\n=== T2.25: POST /users ===")

    # Admin creates user
    status, body = request('POST', '/users', {
        'username': 'uploader1', 'password': 'TestPass88', 'role': 'Uploader'
    }, token=admin_token)
    test("Admin creates user returns 201", status == 201, f"got {status}: {body}")

    # Duplicate user
    status, body = request('POST', '/users', {
        'username': 'uploader1', 'password': 'TestPass88', 'role': 'Uploader'
    }, token=admin_token)
    test("Duplicate user returns 409", status == 409, f"got {status}")

    # Invalid role
    status, body = request('POST', '/users', {
        'username': 'baduser', 'password': 'TestPass88', 'role': 'SuperAdmin'
    }, token=admin_token)
    test("Invalid role returns 400", status == 400, f"got {status}")

    # Short password
    status, body = request('POST', '/users', {
        'username': 'shortpw', 'password': 'short', 'role': 'Viewer'
    }, token=admin_token)
    test("Short password returns 400", status == 400, f"got {status}")

    # Create more users for testing
    request('POST', '/users', {
        'username': 'reader1', 'password': 'TestPass88', 'role': 'Reader'
    }, token=admin_token)
    request('POST', '/users', {
        'username': 'viewer1', 'password': 'TestPass88', 'role': 'Viewer'
    }, token=admin_token)

    # Non-admin cannot create user
    _, login_body = request('POST', '/auth/login', {
        'username': 'uploader1', 'password': 'TestPass88'
    })
    uploader_token = login_body.get('token')

    status, body = request('POST', '/users', {
        'username': 'hacker', 'password': 'TestPass88', 'role': 'Viewer'
    }, token=uploader_token)
    test("Non-admin create user returns 403", status == 403, f"got {status}")

    # No auth
    status, body = request('POST', '/users', {
        'username': 'noauth', 'password': 'TestPass88', 'role': 'Viewer'
    })
    test("Unauthenticated create returns 401", status == 401, f"got {status}")

    # ============================================================
    # T2.28: List Users (Admin only)
    # ============================================================
    print("\n=== T2.28: GET /users ===")

    status, body = request('GET', '/users', token=admin_token)
    test("Admin list users returns 200", status == 200, f"got {status}")
    users = body.get('users', [])
    test("List includes created users", len(users) >= 4, f"got {len(users)} users")
    usernames = [u['username'] for u in users]
    test("List includes admin", 'admin' in usernames)
    test("List includes uploader1", 'uploader1' in usernames)

    # Non-admin cannot list
    status, body = request('GET', '/users', token=uploader_token)
    test("Non-admin list returns 403", status == 403, f"got {status}")

    # ============================================================
    # T2.26: Update User (Admin only)
    # ============================================================
    print("\n=== T2.26: PUT /users/{username} ===")

    # Update role
    status, body = request('PUT', '/users/viewer1', {
        'role': 'Reader'
    }, token=admin_token)
    test("Admin updates role returns 200", status == 200, f"got {status}")
    test("Updated role is Reader", body.get('role') == 'Reader', f"got {body}")

    # Update status to disabled
    status, body = request('PUT', '/users/reader1', {
        'status': 'disabled'
    }, token=admin_token)
    test("Admin disables user returns 200", status == 200, f"got {status}")
    test("Status is disabled", body.get('status') == 'disabled')

    # Disabled user cannot login
    status, body = request('POST', '/auth/login', {
        'username': 'reader1', 'password': 'TestPass88'
    })
    test("Disabled user login returns 401", status == 401, f"got {status}")

    # Re-enable
    status, body = request('PUT', '/users/reader1', {
        'status': 'active'
    }, token=admin_token)
    test("Re-enable user returns 200", status == 200, f"got {status}")

    # Prevent self-role-change
    status, body = request('PUT', '/users/admin', {
        'role': 'Viewer'
    }, token=admin_token)
    test("Self role change returns 400", status == 400, f"got {status}")

    # Non-existent user
    status, body = request('PUT', '/users/nouser', {
        'role': 'Viewer'
    }, token=admin_token)
    test("Update non-existent user returns 404", status == 404, f"got {status}")

    # ============================================================
    # T2.29: Reset Password (Admin only)
    # ============================================================
    print("\n=== T2.29: POST /users/{username}/reset-password ===")

    status, body = request('POST', '/users/uploader1/reset-password',
                           token=admin_token)
    test("Admin resets password returns 200", status == 200, f"got {status}")
    test("Returns temporary password", 'temporary_password' in body, f"body: {body}")
    temp_password = body.get('temporary_password')

    # Login with temp password
    status, body = request('POST', '/auth/login', {
        'username': 'uploader1', 'password': temp_password
    })
    test("Login with temp password returns 200", status == 200, f"got {status}")
    test("Force password change is true", body.get('force_password_change') is True)
    uploader_token = body.get('token')

    # Non-existent user
    status, body = request('POST', '/users/nouser/reset-password',
                           token=admin_token)
    test("Reset for non-existent returns 404", status == 404, f"got {status}")

    # Non-admin cannot reset
    status, body = request('POST', '/users/admin/reset-password',
                           token=uploader_token)
    test("Non-admin reset returns 403", status == 403, f"got {status}")

    # ============================================================
    # T2.24: Change Password
    # ============================================================
    print("\n=== T2.24: POST /auth/change-password ===")

    status, body = request('POST', '/auth/change-password', {
        'current_password': temp_password,
        'new_password': 'NewSecurePass99'
    }, token=uploader_token)
    test("Change password returns 200", status == 200, f"got {status}")

    # Login with new password
    status, body = request('POST', '/auth/login', {
        'username': 'uploader1', 'password': 'NewSecurePass99'
    })
    test("Login with new password returns 200", status == 200, f"got {status}")
    test("Force password change is now false", body.get('force_password_change') is False)
    uploader_token = body.get('token')

    # Wrong current password
    status, body = request('POST', '/auth/change-password', {
        'current_password': 'WrongOld',
        'new_password': 'AnotherPass99'
    }, token=uploader_token)
    test("Wrong current password returns 400", status == 400, f"got {status}")

    # Short new password
    status, body = request('POST', '/auth/change-password', {
        'current_password': 'NewSecurePass99',
        'new_password': 'short'
    }, token=uploader_token)
    test("Short new password returns 400", status == 400, f"got {status}")

    # ============================================================
    # T2.23: Logout
    # ============================================================
    print("\n=== T2.23: POST /auth/logout ===")

    status, body = request('POST', '/auth/logout', token=uploader_token)
    test("Logout returns 200", status == 200, f"got {status}")

    # Reuse token after logout
    status, body = request('GET', '/users', token=uploader_token)
    test("Reuse token after logout returns 401", status == 401, f"got {status}")

    # ============================================================
    # T2.27: Delete User (Admin only)
    # ============================================================
    print("\n=== T2.27: DELETE /users/{username} ===")

    # Admin deletes user
    status, body = request('DELETE', '/users/viewer1', token=admin_token)
    test("Admin deletes user returns 200", status == 200, f"got {status}")

    # Verify deleted user cannot login
    status, body = request('POST', '/auth/login', {
        'username': 'viewer1', 'password': 'TestPass88'
    })
    test("Deleted user login returns 401", status == 401, f"got {status}")

    # Prevent self-delete
    status, body = request('DELETE', '/users/admin', token=admin_token)
    test("Self-delete returns 400", status == 400, f"got {status}")

    # Delete non-existent user
    status, body = request('DELETE', '/users/nouser', token=admin_token)
    test("Delete non-existent returns 404", status == 404, f"got {status}")

    # ============================================================
    # Summary
    # ============================================================
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    if failed > 0:
        sys.exit(1)
    print("All tests passed.")


if __name__ == '__main__':
    main()
