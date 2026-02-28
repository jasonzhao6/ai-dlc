"""File Operations Lambda handler.

Routes:
  GET    /folders/{folderId}/files  - List files in folder
  POST   /files/upload-url          - Get pre-signed upload URL
  POST   /files/confirm-upload      - Confirm upload, record metadata
  POST   /files/download-url        - Get pre-signed download URL
  DELETE /files/{fileId}            - Delete file
  GET    /files/search              - Search files (Unit 5)
"""

import json
import os
import time
import uuid

import boto3

from shared import db
from shared.response import success, error
from shared.auth_middleware import require_auth, require_admin, check_folder_access


STORAGE_BUCKET = os.environ.get('STORAGE_BUCKET', 'file-share-storage-dev')
UPLOAD_URL_TTL = int(os.environ.get('UPLOAD_URL_TTL', '900'))
DOWNLOAD_URL_TTL = int(os.environ.get('DOWNLOAD_URL_TTL', '900'))
MAX_FILE_SIZE = 1 * 1024 * 1024 * 1024  # 1 GB

_s3_client = None


def _get_s3():
    """Lazy-init S3 client."""
    global _s3_client
    if _s3_client is None:
        s3_endpoint = os.environ.get('S3_ENDPOINT')
        if s3_endpoint:
            # Local testing with MinIO
            session = boto3.Session(
                aws_access_key_id=os.environ.get('S3_ACCESS_KEY', 'minioadmin'),
                aws_secret_access_key=os.environ.get('S3_SECRET_KEY', 'minioadmin'),
                region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
            )
            _s3_client = session.client('s3', endpoint_url=s3_endpoint)
        else:
            _s3_client = boto3.client('s3')
    return _s3_client


def lambda_handler(event, context):
    """Route requests to the appropriate handler."""
    method = event.get('httpMethod', '')
    resource = event.get('resource', '')

    routes = {
        ('GET', '/folders/{folderId}/files'): _auth(handle_list_files),
        ('POST', '/files/upload-url'): _auth(handle_get_upload_url),
        ('POST', '/files/confirm-upload'): _auth(handle_confirm_upload),
        ('POST', '/files/download-url'): _auth(handle_get_download_url),
        ('DELETE', '/files/{fileId}'): _auth(handle_delete_file),
        ('GET', '/files/search'): _auth(handle_search_files),
    }

    handler = routes.get((method, resource))
    if handler:
        return handler(event, context)

    if method == 'OPTIONS':
        return success({})

    return error('Not found', 404)


def _auth(handler):
    return require_auth(handler)


# ============================================================
# File handlers
# ============================================================

def handle_list_files(event, context):
    """List files in a folder."""
    user = event['user']
    folder_id = event.get('pathParameters', {}).get('folderId', '')

    # Check folder exists
    folder = db.get_item(f'FOLDER#{folder_id}', 'META')
    if not folder:
        return error('Folder not found', 404)

    # Check access (Admin can see all; others need assignment)
    if user['role'] != 'Admin':
        if not check_folder_access(user['username'], folder_id):
            return error('Forbidden', 403)

    # Query files in this folder
    items = db.query(f'FOLDER#{folder_id}', sk_begins_with='FILE#')
    files = []
    for item in items:
        files.append({
            'file_id': item.get('file_id'),
            'name': item.get('file_name'),
            'size': item.get('file_size'),
            'uploaded_by': item.get('uploaded_by'),
            'uploaded_at': item.get('uploaded_at'),
            'folder_id': folder_id,
        })

    return success({'files': files, 'folder_id': folder_id})


def handle_get_upload_url(event, context):
    """Generate a pre-signed S3 PUT URL for file upload."""
    user = event['user']

    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return error('Invalid JSON', 400)

    folder_id = body.get('folder_id', '')
    file_name = body.get('file_name', '').strip()
    file_size = body.get('file_size', 0)

    if not folder_id or not file_name:
        return error('folder_id and file_name are required', 400)

    # Validate file size
    if file_size > MAX_FILE_SIZE:
        return error('File size exceeds maximum of 1 GB', 400)

    # Check role — only Admin and Uploader can upload
    if user['role'] not in ('Admin', 'Uploader'):
        return error('Forbidden', 403)

    # Check folder access
    folder = db.get_item(f'FOLDER#{folder_id}', 'META')
    if not folder:
        return error('Folder not found', 404)

    if user['role'] != 'Admin':
        if not check_folder_access(user['username'], folder_id):
            return error('Forbidden', 403)

    # Generate file ID and S3 key
    file_id = str(uuid.uuid4())[:8]
    s3_key = f'files/{folder_id}/{file_id}/{file_name}'

    # Generate pre-signed URL
    s3 = _get_s3()
    try:
        upload_url = s3.generate_presigned_url(
            'put_object',
            Params={
                'Bucket': STORAGE_BUCKET,
                'Key': s3_key,
                'ContentType': 'application/octet-stream',
            },
            ExpiresIn=UPLOAD_URL_TTL,
        )
    except Exception as e:
        return error(f'Failed to generate upload URL: {str(e)}', 500)

    return success({
        'upload_url': upload_url,
        'file_id': file_id,
        's3_key': s3_key,
    })


def handle_confirm_upload(event, context):
    """Record file metadata in DynamoDB after successful S3 upload."""
    user = event['user']

    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return error('Invalid JSON', 400)

    file_id = body.get('file_id', '')
    folder_id = body.get('folder_id', '')
    file_name = body.get('file_name', '').strip()
    file_size = body.get('file_size', 0)
    s3_key = body.get('s3_key', '')

    if not file_id or not folder_id or not file_name or not s3_key:
        return error('file_id, folder_id, file_name, and s3_key are required', 400)

    # Record file metadata
    now = int(time.time())
    file_item = {
        'PK': f'FOLDER#{folder_id}',
        'SK': f'FILE#{file_id}',
        'GSI1PK': f'FILE#{file_id}',
        'GSI1SK': f'FOLDER#{folder_id}',
        'file_id': file_id,
        'folder_id': folder_id,
        'file_name': file_name,
        'file_size': file_size,
        's3_key': s3_key,
        'uploaded_by': user['username'],
        'uploaded_at': now,
    }
    db.put_item(file_item)

    return success({
        'file_id': file_id,
        'message': 'Upload confirmed',
    })


def handle_get_download_url(event, context):
    """Generate a pre-signed S3 GET URL for file download."""
    user = event['user']

    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return error('Invalid JSON', 400)

    file_id = body.get('file_id', '')
    folder_id = body.get('folder_id', '')

    if not file_id or not folder_id:
        return error('file_id and folder_id are required', 400)

    # Check role — only Admin and Reader can download
    if user['role'] not in ('Admin', 'Reader'):
        return error('Forbidden', 403)

    # Get file metadata
    file_record = db.get_item(f'FOLDER#{folder_id}', f'FILE#{file_id}')
    if not file_record:
        return error('File not found', 404)

    # Check folder access
    if user['role'] != 'Admin':
        if not check_folder_access(user['username'], folder_id):
            return error('Forbidden', 403)

    # Generate pre-signed URL
    s3 = _get_s3()
    try:
        download_url = s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': STORAGE_BUCKET,
                'Key': file_record['s3_key'],
            },
            ExpiresIn=DOWNLOAD_URL_TTL,
        )
    except Exception as e:
        return error(f'Failed to generate download URL: {str(e)}', 500)

    return success({
        'download_url': download_url,
        'file_name': file_record.get('file_name'),
    })


def handle_delete_file(event, context):
    """Delete a file from S3 and DynamoDB."""
    user = event['user']

    file_id = event.get('pathParameters', {}).get('fileId', '')

    # Need folder_id from query params since file PK includes it
    query_params = event.get('queryStringParameters') or {}
    folder_id = query_params.get('folder_id', '')

    if not folder_id:
        return error('folder_id query parameter is required', 400)

    # Get file metadata
    file_record = db.get_item(f'FOLDER#{folder_id}', f'FILE#{file_id}')
    if not file_record:
        return error('File not found', 404)

    # Authorization check
    if user['role'] == 'Admin':
        pass  # Admin can delete any file
    elif user['role'] == 'Uploader' and file_record.get('uploaded_by') == user['username']:
        pass  # Uploader can delete own files
    else:
        return error('Forbidden', 403)

    # Delete from S3
    try:
        s3 = _get_s3()
        s3.delete_object(Bucket=STORAGE_BUCKET, Key=file_record['s3_key'])
    except Exception:
        pass  # Best effort S3 delete

    # Delete metadata from DynamoDB
    db.delete_item(f'FOLDER#{folder_id}', f'FILE#{file_id}')

    return success({'message': 'File deleted'})


def handle_search_files(event, context):
    """Search files by name, scoped by user's folder access."""
    user = event['user']

    query_params = event.get('queryStringParameters') or {}
    query = query_params.get('q', '').strip()

    if not query:
        return error('Search query (q) is required', 400)

    query_lower = query.lower()

    if user['role'] == 'Admin':
        # Admin: search all files via scan
        from boto3.dynamodb.conditions import Attr
        all_items = db.scan(
            filter_expression=Attr('SK').begins_with('FILE#')
        )
    else:
        # Non-admin: only search files in accessible folders
        assignments = db.query(
            f'USER#{user["username"]}',
            sk_begins_with='ASSIGN#FOLDER#',
            index_name='GSI1'
        )
        accessible_ids = set()
        for a in assignments:
            parts = a['GSI1SK'].split('#')
            if len(parts) >= 3:
                fid = parts[2]
                _collect_folder_ids(fid, accessible_ids)

        if not accessible_ids:
            return success({'files': [], 'query': query})

        # Query files from each accessible folder
        all_items = []
        for fid in accessible_ids:
            items = db.query(f'FOLDER#{fid}', sk_begins_with='FILE#')
            all_items.extend(items)

    # Filter by name (case-insensitive partial match)
    results = []
    for item in all_items:
        file_name = item.get('file_name', '')
        if query_lower in file_name.lower():
            folder_id = item.get('folder_id', '')
            results.append({
                'file_id': item.get('file_id'),
                'name': file_name,
                'size': item.get('file_size'),
                'uploaded_by': item.get('uploaded_by'),
                'uploaded_at': item.get('uploaded_at'),
                'folder_id': folder_id,
                'folder_path': _get_folder_path(folder_id),
            })

    return success({'files': results, 'query': query})


def _collect_folder_ids(folder_id, result_set):
    """Collect a folder ID and all its descendant IDs."""
    if folder_id in result_set:
        return
    result_set.add(folder_id)
    children = db.query(f'PARENT#{folder_id}', index_name='GSI1')
    for child in children:
        if child.get('SK') == 'META':
            child_id = child['PK'].replace('FOLDER#', '')
            _collect_folder_ids(child_id, result_set)


def _get_folder_path(folder_id):
    """Build a folder path string by walking up the parent chain."""
    parts = []
    current_id = folder_id
    visited = set()
    while current_id and current_id != 'ROOT' and current_id not in visited:
        visited.add(current_id)
        folder = db.get_item(f'FOLDER#{current_id}', 'META')
        if not folder:
            break
        parts.insert(0, folder.get('name', current_id))
        current_id = folder.get('parent_id')
    return '/' + '/'.join(parts) if parts else '/'
