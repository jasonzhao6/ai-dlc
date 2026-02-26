"""Integration tests for file operations against SAM local API.

Note: S3 operations (actual upload/download) can't be tested locally without
a real or mock S3. We test the API logic, DynamoDB operations, and authorization.
"""
import json
import sys
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:3000"

passed = 0
failed = 0


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
    # Setup: login, create users and folder with assignments
    _, data = request('POST', '/auth/login', {
        'username': 'admin', 'password': 'ChangeMe123!'
    })
    admin_token = data['token']

    # Create users with different roles
    for user_info in [
        {'username': 'uploader1', 'password': 'TestPass88', 'role': 'Uploader'},
        {'username': 'reader1', 'password': 'TestPass88', 'role': 'Reader'},
        {'username': 'viewer1', 'password': 'TestPass88', 'role': 'Viewer'},
    ]:
        request('POST', '/users', user_info, token=admin_token)

    # Login all users
    tokens = {}
    for uname in ['uploader1', 'reader1', 'viewer1']:
        _, d = request('POST', '/auth/login', {'username': uname, 'password': 'TestPass88'})
        tokens[uname] = d['token']

    # Create folder and assign users
    _, folder_data = request('POST', '/folders', {'name': 'TestFolder'}, token=admin_token)
    folder_id = folder_data['folder_id']

    request('POST', f'/folders/{folder_id}/assignments', {
        'usernames': ['uploader1', 'reader1', 'viewer1']
    }, token=admin_token)

    # Create unassigned folder
    _, folder2_data = request('POST', '/folders', {'name': 'UnassignedFolder'}, token=admin_token)
    unassigned_folder_id = folder2_data['folder_id']

    # ============================================================
    # T4.16: Upload URL
    # ============================================================
    print("\n=== T4.16: POST /files/upload-url ===")

    # Admin gets upload URL
    status, body = request('POST', '/files/upload-url', {
        'folder_id': folder_id, 'file_name': 'test.pdf', 'file_size': 1024
    }, token=admin_token)
    test("Admin gets upload URL returns 200", status == 200, f"got {status}: {body}")
    test("Returns upload_url", 'upload_url' in body)
    test("Returns file_id", 'file_id' in body)
    admin_file_id = body.get('file_id')
    admin_s3_key = body.get('s3_key')

    # Uploader (assigned) gets upload URL
    status, body = request('POST', '/files/upload-url', {
        'folder_id': folder_id, 'file_name': 'uploader_file.txt', 'file_size': 512
    }, token=tokens['uploader1'])
    test("Assigned Uploader gets URL returns 200", status == 200, f"got {status}")
    uploader_file_id = body.get('file_id')
    uploader_s3_key = body.get('s3_key')

    # Uploader (unassigned folder) forbidden
    status, body = request('POST', '/files/upload-url', {
        'folder_id': unassigned_folder_id, 'file_name': 'test.txt', 'file_size': 100
    }, token=tokens['uploader1'])
    test("Unassigned Uploader returns 403", status == 403, f"got {status}")

    # Reader cannot upload
    status, body = request('POST', '/files/upload-url', {
        'folder_id': folder_id, 'file_name': 'test.txt', 'file_size': 100
    }, token=tokens['reader1'])
    test("Reader upload returns 403", status == 403, f"got {status}")

    # Viewer cannot upload
    status, body = request('POST', '/files/upload-url', {
        'folder_id': folder_id, 'file_name': 'test.txt', 'file_size': 100
    }, token=tokens['viewer1'])
    test("Viewer upload returns 403", status == 403, f"got {status}")

    # File too large
    status, body = request('POST', '/files/upload-url', {
        'folder_id': folder_id, 'file_name': 'big.bin', 'file_size': 2 * 1024 * 1024 * 1024
    }, token=admin_token)
    test("File > 1GB returns 400", status == 400, f"got {status}")

    # ============================================================
    # T4.17: Confirm upload (simulating after S3 PUT)
    # ============================================================
    print("\n=== T4.17: POST /files/confirm-upload ===")

    # Admin confirms upload
    status, body = request('POST', '/files/confirm-upload', {
        'file_id': admin_file_id, 'folder_id': folder_id,
        'file_name': 'test.pdf', 'file_size': 1024,
        's3_key': admin_s3_key,
    }, token=admin_token)
    test("Admin confirm upload returns 200", status == 200, f"got {status}: {body}")

    # Uploader confirms upload
    status, body = request('POST', '/files/confirm-upload', {
        'file_id': uploader_file_id, 'folder_id': folder_id,
        'file_name': 'uploader_file.txt', 'file_size': 512,
        's3_key': uploader_s3_key,
    }, token=tokens['uploader1'])
    test("Uploader confirm upload returns 200", status == 200, f"got {status}")

    # ============================================================
    # T4.19: List files
    # ============================================================
    print("\n=== T4.19: GET /folders/{folderId}/files ===")

    status, body = request('GET', f'/folders/{folder_id}/files', token=admin_token)
    test("Admin list files returns 200", status == 200, f"got {status}")
    files = body.get('files', [])
    test("Two files in folder", len(files) == 2, f"got {len(files)}")

    # Assigned reader can list
    status, body = request('GET', f'/folders/{folder_id}/files', token=tokens['reader1'])
    test("Assigned reader list files returns 200", status == 200, f"got {status}")
    test("Reader sees files", len(body.get('files', [])) == 2)

    # Unassigned user cannot list unassigned folder
    status, body = request('GET', f'/folders/{unassigned_folder_id}/files', token=tokens['uploader1'])
    test("Unassigned user list returns 403", status == 403, f"got {status}")

    # ============================================================
    # T4.18: Download URL
    # ============================================================
    print("\n=== T4.18: POST /files/download-url ===")

    # Admin gets download URL
    status, body = request('POST', '/files/download-url', {
        'file_id': admin_file_id, 'folder_id': folder_id
    }, token=admin_token)
    test("Admin gets download URL returns 200", status == 200, f"got {status}")
    test("Returns download_url", 'download_url' in body)

    # Reader (assigned) gets download URL
    status, body = request('POST', '/files/download-url', {
        'file_id': admin_file_id, 'folder_id': folder_id
    }, token=tokens['reader1'])
    test("Assigned Reader gets URL returns 200", status == 200, f"got {status}")

    # Uploader cannot download
    status, body = request('POST', '/files/download-url', {
        'file_id': admin_file_id, 'folder_id': folder_id
    }, token=tokens['uploader1'])
    test("Uploader download returns 403", status == 403, f"got {status}")

    # Viewer cannot download
    status, body = request('POST', '/files/download-url', {
        'file_id': admin_file_id, 'folder_id': folder_id
    }, token=tokens['viewer1'])
    test("Viewer download returns 403", status == 403, f"got {status}")

    # ============================================================
    # T4.20: Delete file
    # ============================================================
    print("\n=== T4.20: DELETE /files/{fileId} ===")

    # Reader cannot delete
    status, body = request('DELETE', f'/files/{uploader_file_id}?folder_id={folder_id}',
                           token=tokens['reader1'])
    test("Reader delete returns 403", status == 403, f"got {status}")

    # Uploader cannot delete other's file
    status, body = request('DELETE', f'/files/{admin_file_id}?folder_id={folder_id}',
                           token=tokens['uploader1'])
    test("Uploader delete other's file returns 403", status == 403, f"got {status}")

    # Uploader deletes own file
    status, body = request('DELETE', f'/files/{uploader_file_id}?folder_id={folder_id}',
                           token=tokens['uploader1'])
    test("Uploader deletes own file returns 200", status == 200, f"got {status}")

    # Admin deletes any file
    status, body = request('DELETE', f'/files/{admin_file_id}?folder_id={folder_id}',
                           token=admin_token)
    test("Admin deletes file returns 200", status == 200, f"got {status}")

    # Delete non-existent file
    status, body = request('DELETE', f'/files/nonexistent?folder_id={folder_id}',
                           token=admin_token)
    test("Delete non-existent returns 404", status == 404, f"got {status}")

    # Verify files deleted
    status, body = request('GET', f'/folders/{folder_id}/files', token=admin_token)
    test("Files list empty after deletions", len(body.get('files', [])) == 0,
         f"got {len(body.get('files', []))}")

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
