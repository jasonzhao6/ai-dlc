"""Authorization middleware — session validation and role enforcement."""

import json
from shared import db
from shared.response import error


def _extract_token(event):
    """Extract Bearer token from Authorization header."""
    headers = event.get('headers') or {}
    # API Gateway may lowercase header names
    auth = headers.get('Authorization') or headers.get('authorization') or ''
    if auth.startswith('Bearer '):
        return auth[7:]
    return None


def authenticate(event):
    """Validate session token, return user context or None.

    Returns dict: {"username": str, "role": str} or None if invalid.
    """
    token = _extract_token(event)
    if not token:
        return None
    session = db.get_item(f'SESSION#{token}', 'SESSION')
    if not session:
        return None
    return {
        'username': session['username'],
        'role': session['role'],
        'token': token
    }


def require_auth(handler):
    """Decorator: rejects unauthenticated requests with 401."""
    def wrapper(event, context):
        user = authenticate(event)
        if not user:
            return error('Unauthorized', 401)
        event['user'] = user
        return handler(event, context)
    return wrapper


def require_admin(handler):
    """Decorator: rejects non-Admin requests with 403. Must be used after require_auth."""
    def wrapper(event, context):
        user = event.get('user')
        if not user or user['role'] != 'Admin':
            return error('Forbidden', 403)
        return handler(event, context)
    return wrapper


def check_folder_access(username, folder_id):
    """Check if a user has access to a folder (direct or via parent inheritance).

    Returns True if the user is assigned to the folder or any of its ancestors.
    """
    # Get user's directly assigned folder IDs
    assignments = db.query(
        f'USER#{username}',
        sk_begins_with='ASSIGN#FOLDER#',
        index_name='GSI1'
    )
    assigned_folder_ids = set()
    for a in assignments:
        # GSI1SK format: ASSIGN#FOLDER#<folder_id>
        parts = a['GSI1SK'].split('#')
        if len(parts) >= 3:
            assigned_folder_ids.add(parts[2])

    if not assigned_folder_ids:
        return False

    # Walk up the parent chain from the target folder
    current_id = folder_id
    visited = set()
    while current_id and current_id != 'ROOT' and current_id not in visited:
        if current_id in assigned_folder_ids:
            return True
        visited.add(current_id)
        folder = db.get_item(f'FOLDER#{current_id}', 'META')
        if not folder:
            break
        current_id = folder.get('parent_id')

    return False
