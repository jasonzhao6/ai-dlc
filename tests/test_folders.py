"""Integration tests for folder management endpoints against SAM local API."""
import json
import sys
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:3000"

passed = 0
failed = 0
admin_token = None
uploader_token = None


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
    global admin_token, uploader_token

    # Setup: login as admin, create an uploader user
    _, data = request('POST', '/auth/login', {
        'username': 'admin', 'password': 'ChangeMe123!'
    })
    admin_token = data['token']

    request('POST', '/users', {
        'username': 'uploader1', 'password': 'TestPass88', 'role': 'Uploader'
    }, token=admin_token)

    _, data = request('POST', '/auth/login', {
        'username': 'uploader1', 'password': 'TestPass88'
    })
    uploader_token = data['token']

    # ============================================================
    # T3.15: Create folder
    # ============================================================
    print("\n=== T3.15: POST /folders ===")

    status, body = request('POST', '/folders', {'name': 'Project Alpha'}, token=admin_token)
    test("Admin creates folder returns 201", status == 201, f"got {status}: {body}")
    test("Returns folder_id", 'folder_id' in body, f"body: {body}")
    folder_a_id = body.get('folder_id')

    # Duplicate name at same level
    status, body = request('POST', '/folders', {'name': 'Project Alpha'}, token=admin_token)
    test("Duplicate name returns 409", status == 409, f"got {status}")

    # Non-admin cannot create
    status, body = request('POST', '/folders', {'name': 'Hacker'}, token=uploader_token)
    test("Non-admin create returns 403", status == 403, f"got {status}")

    # Missing name
    status, body = request('POST', '/folders', {'name': ''}, token=admin_token)
    test("Empty name returns 400", status == 400, f"got {status}")

    # Create second folder
    status, body = request('POST', '/folders', {'name': 'Project Beta'}, token=admin_token)
    test("Create second folder returns 201", status == 201, f"got {status}")
    folder_b_id = body.get('folder_id')

    # ============================================================
    # T3.16: Create sub-folder
    # ============================================================
    print("\n=== T3.16: POST /folders with parent_id ===")

    status, body = request('POST', '/folders', {
        'name': 'Sub-A1', 'parent_id': folder_a_id
    }, token=admin_token)
    test("Create sub-folder returns 201", status == 201, f"got {status}: {body}")
    sub_a1_id = body.get('folder_id')

    status, body = request('POST', '/folders', {
        'name': 'Sub-A2', 'parent_id': folder_a_id
    }, token=admin_token)
    test("Create another sub-folder returns 201", status == 201, f"got {status}")
    sub_a2_id = body.get('folder_id')

    # Invalid parent
    status, body = request('POST', '/folders', {
        'name': 'Bad', 'parent_id': 'nonexistent'
    }, token=admin_token)
    test("Invalid parent returns 404", status == 404, f"got {status}")

    # Duplicate name at sub-level
    status, body = request('POST', '/folders', {
        'name': 'Sub-A1', 'parent_id': folder_a_id
    }, token=admin_token)
    test("Duplicate sub-folder name returns 409", status == 409, f"got {status}")

    # Same name at different level is OK
    status, body = request('POST', '/folders', {
        'name': 'Sub-A1', 'parent_id': folder_b_id
    }, token=admin_token)
    test("Same name different parent returns 201", status == 201, f"got {status}")

    # ============================================================
    # T3.17: Rename folder
    # ============================================================
    print("\n=== T3.17: PUT /folders/{folderId} ===")

    status, body = request('PUT', f'/folders/{sub_a2_id}', {'name': 'Sub-A2-Renamed'}, token=admin_token)
    test("Rename folder returns 200", status == 200, f"got {status}: {body}")
    test("Name updated", body.get('name') == 'Sub-A2-Renamed')

    # Name conflict
    status, body = request('PUT', f'/folders/{sub_a2_id}', {'name': 'Sub-A1'}, token=admin_token)
    test("Rename to conflict returns 409", status == 409, f"got {status}")

    # Non-existent folder
    status, body = request('PUT', '/folders/nonexistent', {'name': 'X'}, token=admin_token)
    test("Rename non-existent returns 404", status == 404, f"got {status}")

    # ============================================================
    # T3.19: List folders
    # ============================================================
    print("\n=== T3.19: GET /folders ===")

    status, body = request('GET', '/folders', token=admin_token)
    test("Admin list folders returns 200", status == 200, f"got {status}")
    folders = body.get('folders', [])
    test("Admin sees root folders", len(folders) >= 2, f"got {len(folders)} folders")
    folder_names = [f['name'] for f in folders]
    test("List includes Project Alpha", 'Project Alpha' in folder_names, f"names: {folder_names}")

    # Check sub-folders
    alpha = next((f for f in folders if f['name'] == 'Project Alpha'), None)
    test("Project Alpha has children", alpha is not None and len(alpha.get('children', [])) >= 2,
         f"children: {alpha.get('children', []) if alpha else 'N/A'}")

    # Unassigned user sees nothing
    status, body = request('GET', '/folders', token=uploader_token)
    test("Unassigned user sees no folders", len(body.get('folders', [])) == 0,
         f"got {len(body.get('folders', []))} folders")

    # ============================================================
    # T3.20: Assign users
    # ============================================================
    print("\n=== T3.20: POST /folders/{folderId}/assignments ===")

    status, body = request('POST', f'/folders/{folder_a_id}/assignments', {
        'usernames': ['uploader1']
    }, token=admin_token)
    test("Assign user returns 200", status == 200, f"got {status}: {body}")

    # Non-admin cannot assign
    status, body = request('POST', f'/folders/{folder_a_id}/assignments', {
        'usernames': ['uploader1']
    }, token=uploader_token)
    test("Non-admin assign returns 403", status == 403, f"got {status}")

    # ============================================================
    # T3.22: Assignment inheritance
    # ============================================================
    print("\n=== T3.22: Assignment inheritance ===")

    # Uploader assigned to folder_a should see folder_a + sub-folders
    status, body = request('GET', '/folders', token=uploader_token)
    test("Assigned user sees folders", len(body.get('folders', [])) >= 1,
         f"got {len(body.get('folders', []))} folders")

    # Check that sub-folders are visible
    user_folders = body.get('folders', [])
    alpha_user = next((f for f in user_folders if f['name'] == 'Project Alpha'), None)
    test("User sees Project Alpha", alpha_user is not None)
    if alpha_user:
        test("User sees sub-folders via inheritance",
             len(alpha_user.get('children', [])) >= 2,
             f"children: {[c['name'] for c in alpha_user.get('children', [])]}")

    # User should NOT see Project Beta (not assigned)
    beta_user = next((f for f in user_folders if f['name'] == 'Project Beta'), None)
    test("User does not see unassigned folder", beta_user is None,
         f"found: {beta_user}")

    # ============================================================
    # T3.21: List and unassign
    # ============================================================
    print("\n=== T3.21: Assignments list and unassign ===")

    status, body = request('GET', f'/folders/{folder_a_id}/assignments', token=admin_token)
    test("List assignments returns 200", status == 200, f"got {status}")
    assignments = body.get('assignments', [])
    test("Assignment exists", len(assignments) >= 1, f"got {len(assignments)}")
    test("Correct username", assignments[0].get('username') == 'uploader1' if assignments else False)

    # Unassign
    status, body = request('DELETE', f'/folders/{folder_a_id}/assignments/uploader1', token=admin_token)
    test("Unassign returns 200", status == 200, f"got {status}")

    # Verify access revoked
    status, body = request('GET', '/folders', token=uploader_token)
    test("After unassign user sees no folders", len(body.get('folders', [])) == 0,
         f"got {len(body.get('folders', []))} folders")

    # ============================================================
    # T3.18: Delete folder (cascade)
    # ============================================================
    print("\n=== T3.18: DELETE /folders/{folderId} ===")

    # Delete folder with sub-folders (cascade)
    status, body = request('DELETE', f'/folders/{folder_a_id}', token=admin_token)
    test("Delete folder with children returns 200", status == 200, f"got {status}")

    # Verify sub-folders deleted
    status, body = request('GET', '/folders', token=admin_token)
    folder_names = [f['name'] for f in body.get('folders', [])]
    test("Deleted folder removed from list", 'Project Alpha' not in folder_names, f"names: {folder_names}")

    # Delete non-existent
    status, body = request('DELETE', f'/folders/{folder_a_id}', token=admin_token)
    test("Delete non-existent returns 404", status == 404, f"got {status}")

    # Non-admin cannot delete
    status, body = request('DELETE', f'/folders/{folder_b_id}', token=uploader_token)
    test("Non-admin delete returns 403", status == 403, f"got {status}")

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
