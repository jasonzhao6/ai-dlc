"""Integration tests for file search against SAM local API."""
import json
import sys
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:3000"
passed = 0
failed = 0


def request(method, path, body=None, token=None):
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
    # Setup: login, create users, folders, files
    _, data = request('POST', '/auth/login', {'username': 'admin', 'password': 'ChangeMe123!'})
    admin_token = data['token']

    request('POST', '/users', {'username': 'user1', 'password': 'TestPass88', 'role': 'Uploader'}, token=admin_token)
    _, d = request('POST', '/auth/login', {'username': 'user1', 'password': 'TestPass88'})
    user_token = d['token']

    # Create folders
    _, f1 = request('POST', '/folders', {'name': 'Reports'}, token=admin_token)
    folder1_id = f1['folder_id']
    _, f2 = request('POST', '/folders', {'name': 'Private'}, token=admin_token)
    folder2_id = f2['folder_id']

    # Assign user1 to Reports only
    request('POST', f'/folders/{folder1_id}/assignments', {'usernames': ['user1']}, token=admin_token)

    # Upload files to both folders (simulated via confirm-upload)
    for file_info in [
        {'file_id': 'f001', 'folder_id': folder1_id, 'file_name': 'quarterly_report.pdf', 'file_size': 1024, 's3_key': 'files/f1/f001/quarterly_report.pdf'},
        {'file_id': 'f002', 'folder_id': folder1_id, 'file_name': 'annual_report.xlsx', 'file_size': 2048, 's3_key': 'files/f1/f002/annual_report.xlsx'},
        {'file_id': 'f003', 'folder_id': folder1_id, 'file_name': 'budget_2024.csv', 'file_size': 512, 's3_key': 'files/f1/f003/budget_2024.csv'},
        {'file_id': 'f004', 'folder_id': folder2_id, 'file_name': 'secret_report.pdf', 'file_size': 4096, 's3_key': 'files/f2/f004/secret_report.pdf'},
        {'file_id': 'f005', 'folder_id': folder2_id, 'file_name': 'notes.txt', 'file_size': 256, 's3_key': 'files/f2/f005/notes.txt'},
    ]:
        request('POST', '/files/confirm-upload', file_info, token=admin_token)

    # ============================================================
    # T5.11: Admin search across all folders
    # ============================================================
    print("\n=== T5.11: Admin search ===")

    status, body = request('GET', '/files/search?q=report', token=admin_token)
    test("Admin search returns 200", status == 200, f"got {status}")
    files = body.get('files', [])
    test("Admin finds all 'report' files (3)", len(files) == 3, f"got {len(files)}: {[f['name'] for f in files]}")

    # ============================================================
    # T5.12: Non-admin search (scoped to assignments)
    # ============================================================
    print("\n=== T5.12: Non-admin search ===")

    status, body = request('GET', '/files/search?q=report', token=user_token)
    test("User search returns 200", status == 200, f"got {status}")
    files = body.get('files', [])
    test("User finds only assigned 'report' files (2)", len(files) == 2,
         f"got {len(files)}: {[f['name'] for f in files]}")
    # Should NOT see secret_report.pdf
    names = [f['name'] for f in files]
    test("User does not see secret_report", 'secret_report.pdf' not in names, f"names: {names}")

    # ============================================================
    # T5.13: Empty query
    # ============================================================
    print("\n=== T5.13: Empty query ===")

    status, body = request('GET', '/files/search?q=', token=admin_token)
    test("Empty query returns 400", status == 400, f"got {status}")

    status, body = request('GET', '/files/search', token=admin_token)
    test("Missing query returns 400", status == 400, f"got {status}")

    # ============================================================
    # T5.14: Case-insensitive search
    # ============================================================
    print("\n=== T5.14: Case-insensitive ===")

    status, body = request('GET', '/files/search?q=REPORT', token=admin_token)
    test("Uppercase search returns 200", status == 200, f"got {status}")
    test("Case-insensitive match", len(body.get('files', [])) == 3,
         f"got {len(body.get('files', []))}")

    # ============================================================
    # T5.15: Partial match
    # ============================================================
    print("\n=== T5.15: Partial match ===")

    status, body = request('GET', '/files/search?q=rep', token=admin_token)
    test("Partial match returns 200", status == 200, f"got {status}")
    test("Partial 'rep' matches report files", len(body.get('files', [])) == 3,
         f"got {len(body.get('files', []))}")

    status, body = request('GET', '/files/search?q=budget', token=admin_token)
    test("Search 'budget' matches 1", len(body.get('files', [])) == 1,
         f"got {len(body.get('files', []))}")

    # Check folder path is returned
    status, body = request('GET', '/files/search?q=quarterly', token=admin_token)
    files = body.get('files', [])
    test("Search result includes folder_path", files and 'folder_path' in files[0],
         f"fields: {list(files[0].keys()) if files else 'empty'}")
    if files:
        test("Folder path includes folder name", 'Reports' in files[0].get('folder_path', ''),
             f"path: {files[0].get('folder_path')}")

    # ============================================================
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    if failed > 0:
        sys.exit(1)
    print("All tests passed.")


if __name__ == '__main__':
    main()
