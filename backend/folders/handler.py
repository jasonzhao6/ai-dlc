"""Folder Management Lambda handler.

Routes:
  GET    /folders                                - List folders (filtered by role)
  POST   /folders                                - Create folder (Admin only)
  PUT    /folders/{folderId}                     - Rename folder (Admin only)
  DELETE /folders/{folderId}                     - Delete folder + cascade (Admin only)
  GET    /folders/{folderId}/assignments          - List assignments (Admin only)
  POST   /folders/{folderId}/assignments          - Assign users (Admin only)
  DELETE /folders/{folderId}/assignments/{username} - Unassign user (Admin only)
"""

import json
import time
import uuid

from shared import db
from shared.response import success, error
from shared.auth_middleware import require_auth, require_admin


def lambda_handler(event, context):
    """Route requests to the appropriate handler."""
    method = event.get('httpMethod', '')
    resource = event.get('resource', '')

    routes = {
        ('GET', '/folders'): _auth(handle_list_folders),
        ('POST', '/folders'): _admin(handle_create_folder),
        ('PUT', '/folders/{folderId}'): _admin(handle_update_folder),
        ('DELETE', '/folders/{folderId}'): _admin(handle_delete_folder),
        ('GET', '/folders/{folderId}/assignments'): _admin(handle_list_assignments),
        ('POST', '/folders/{folderId}/assignments'): _admin(handle_assign_users),
        ('DELETE', '/folders/{folderId}/assignments/{username}'): _admin(handle_unassign_user),
    }

    handler = routes.get((method, resource))
    if handler:
        return handler(event, context)

    if method == 'OPTIONS':
        return success({})

    return error('Not found', 404)


def _auth(handler):
    return require_auth(handler)


def _admin(handler):
    return require_auth(require_admin(handler))


# ============================================================
# Folder CRUD handlers
# ============================================================

def handle_create_folder(event, context):
    """Create a new folder (Admin only)."""
    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return error('Invalid JSON', 400)

    name = body.get('name', '').strip()
    parent_id = body.get('parent_id', 'ROOT')

    if not name:
        return error('Folder name is required', 400)

    # Validate parent exists (if not ROOT)
    if parent_id != 'ROOT':
        parent = db.get_item(f'FOLDER#{parent_id}', 'META')
        if not parent:
            return error('Parent folder not found', 404)

    # Check for duplicate name at same level
    siblings = db.query(f'PARENT#{parent_id}', index_name='GSI1')
    for sibling in siblings:
        if sibling.get('SK') == 'META' and sibling.get('name') == name:
            return error(f'A folder named "{name}" already exists at this level', 409)

    folder_id = str(uuid.uuid4())[:8]
    now = int(time.time())
    folder_item = {
        'PK': f'FOLDER#{folder_id}',
        'SK': 'META',
        'GSI1PK': f'PARENT#{parent_id}',
        'GSI1SK': f'FOLDER#{folder_id}',
        'name': name,
        'parent_id': parent_id,
        'created_at': now,
    }
    db.put_item(folder_item)

    return success({
        'folder_id': folder_id,
        'name': name,
        'parent_id': parent_id,
    }, 201)


def handle_update_folder(event, context):
    """Rename a folder (Admin only)."""
    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return error('Invalid JSON', 400)

    folder_id = event.get('pathParameters', {}).get('folderId', '')
    new_name = body.get('name', '').strip()

    if not new_name:
        return error('Folder name is required', 400)

    # Get current folder
    folder = db.get_item(f'FOLDER#{folder_id}', 'META')
    if not folder:
        return error('Folder not found', 404)

    parent_id = folder.get('parent_id', 'ROOT')

    # Check for sibling name conflict
    siblings = db.query(f'PARENT#{parent_id}', index_name='GSI1')
    for sibling in siblings:
        if (sibling.get('SK') == 'META'
                and sibling.get('name') == new_name
                and sibling.get('PK') != f'FOLDER#{folder_id}'):
            return error(f'A folder named "{new_name}" already exists at this level', 409)

    # Update name ('name' is a DynamoDB reserved word)
    db.update_item(
        f'FOLDER#{folder_id}', 'META',
        'SET #n = :n',
        {':n': new_name},
        expression_attr_names={'#n': 'name'}
    )

    return success({
        'folder_id': folder_id,
        'name': new_name,
        'parent_id': parent_id,
    })


def handle_delete_folder(event, context):
    """Delete a folder with cascade (Admin only)."""
    folder_id = event.get('pathParameters', {}).get('folderId', '')

    folder = db.get_item(f'FOLDER#{folder_id}', 'META')
    if not folder:
        return error('Folder not found', 404)

    _cascade_delete_folder(folder_id)

    return success({'message': f'Folder deleted'})


def handle_list_folders(event, context):
    """List folders. Admin sees all; non-Admin sees only assigned folders."""
    user = event['user']

    if user['role'] == 'Admin':
        folders = _build_full_tree()
    else:
        folders = _build_filtered_tree(user['username'])

    return success({'folders': folders})


# ============================================================
# Assignment handlers
# ============================================================

def handle_assign_users(event, context):
    """Assign one or more users to a folder (Admin only)."""
    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return error('Invalid JSON', 400)

    folder_id = event.get('pathParameters', {}).get('folderId', '')
    usernames = body.get('usernames', [])

    if not usernames:
        return error('At least one username is required', 400)

    # Verify folder exists
    folder = db.get_item(f'FOLDER#{folder_id}', 'META')
    if not folder:
        return error('Folder not found', 404)

    now = int(time.time())
    for username in usernames:
        # Verify user exists
        user = db.get_item(f'USER#{username}', 'PROFILE')
        if not user:
            continue

        assignment_item = {
            'PK': f'FOLDER#{folder_id}',
            'SK': f'ASSIGN#{username}',
            'GSI1PK': f'USER#{username}',
            'GSI1SK': f'ASSIGN#FOLDER#{folder_id}',
            'username': username,
            'folder_id': folder_id,
            'assigned_at': now,
        }
        db.put_item(assignment_item)

    return success({'message': f'Users assigned to folder'})


def handle_unassign_user(event, context):
    """Remove a user's assignment from a folder (Admin only)."""
    folder_id = event.get('pathParameters', {}).get('folderId', '')
    username = event.get('pathParameters', {}).get('username', '')

    # Check assignment exists
    assignment = db.get_item(f'FOLDER#{folder_id}', f'ASSIGN#{username}')
    if not assignment:
        return error('Assignment not found', 404)

    db.delete_item(f'FOLDER#{folder_id}', f'ASSIGN#{username}')

    return success({'message': f'User unassigned from folder'})


def handle_list_assignments(event, context):
    """List users assigned to a folder (Admin only)."""
    folder_id = event.get('pathParameters', {}).get('folderId', '')

    # Verify folder exists
    folder = db.get_item(f'FOLDER#{folder_id}', 'META')
    if not folder:
        return error('Folder not found', 404)

    # Query all ASSIGN# records for this folder
    items = db.query(f'FOLDER#{folder_id}', sk_begins_with='ASSIGN#')
    assignments = []
    for item in items:
        assignments.append({
            'username': item.get('username'),
            'assigned_at': item.get('assigned_at'),
        })

    return success({
        'folder_id': folder_id,
        'folder_name': folder.get('name'),
        'assignments': assignments,
    })


# ============================================================
# Helper functions
# ============================================================

def _cascade_delete_folder(folder_id):
    """Recursively delete a folder and all its contents."""
    keys_to_delete = []

    # 1. Collect file records for this folder
    file_items = db.query(f'FOLDER#{folder_id}', sk_begins_with='FILE#')
    for item in file_items:
        keys_to_delete.append({'PK': item['PK'], 'SK': item['SK']})

    # 2. Collect assignment records
    assign_items = db.query(f'FOLDER#{folder_id}', sk_begins_with='ASSIGN#')
    for item in assign_items:
        keys_to_delete.append({'PK': item['PK'], 'SK': item['SK']})

    # 3. Collect child folders and recurse
    children = db.query(f'PARENT#{folder_id}', index_name='GSI1')
    for child in children:
        if child.get('SK') == 'META':
            child_id = child['PK'].replace('FOLDER#', '')
            _cascade_delete_folder(child_id)

    # 4. Delete the folder META record
    keys_to_delete.append({'PK': f'FOLDER#{folder_id}', 'SK': 'META'})

    # 5. Batch delete all collected records
    if keys_to_delete:
        db.batch_delete(keys_to_delete)


def _build_full_tree():
    """Build the complete folder tree (Admin view)."""
    # Get all root folders
    root_items = db.query('PARENT#ROOT', index_name='GSI1')
    folders = []
    for item in root_items:
        if item.get('SK') != 'META':
            continue
        folder_id = item['PK'].replace('FOLDER#', '')
        folders.append(_build_folder_node(folder_id, item))
    return folders


def _build_folder_node(folder_id, folder_item):
    """Build a folder node with children."""
    node = {
        'folder_id': folder_id,
        'name': folder_item.get('name'),
        'parent_id': folder_item.get('parent_id', 'ROOT'),
        'created_at': folder_item.get('created_at'),
        'children': [],
    }

    # Get children
    children = db.query(f'PARENT#{folder_id}', index_name='GSI1')
    for child in children:
        if child.get('SK') != 'META':
            continue
        child_id = child['PK'].replace('FOLDER#', '')
        node['children'].append(_build_folder_node(child_id, child))

    return node


def _build_filtered_tree(username):
    """Build a folder tree filtered by user assignments (non-Admin view)."""
    # Get user's directly assigned folder IDs
    assignments = db.query(
        f'USER#{username}',
        sk_begins_with='ASSIGN#FOLDER#',
        index_name='GSI1'
    )
    assigned_ids = set()
    for a in assignments:
        parts = a['GSI1SK'].split('#')
        if len(parts) >= 3:
            assigned_ids.add(parts[2])

    if not assigned_ids:
        return []

    # For each assigned folder, include it and all its descendants
    visible_folders = {}
    for fid in assigned_ids:
        _collect_folder_and_descendants(fid, visible_folders)

    # Build tree structure from visible folders
    return _tree_from_flat(visible_folders)


def _collect_folder_and_descendants(folder_id, result):
    """Collect a folder and all its descendants into result dict."""
    if folder_id in result:
        return

    folder = db.get_item(f'FOLDER#{folder_id}', 'META')
    if not folder:
        return

    result[folder_id] = folder

    # Get children
    children = db.query(f'PARENT#{folder_id}', index_name='GSI1')
    for child in children:
        if child.get('SK') != 'META':
            continue
        child_id = child['PK'].replace('FOLDER#', '')
        _collect_folder_and_descendants(child_id, result)


def _tree_from_flat(folder_map):
    """Convert a flat dict of folders into a tree structure."""
    nodes = {}
    for fid, item in folder_map.items():
        nodes[fid] = {
            'folder_id': fid,
            'name': item.get('name'),
            'parent_id': item.get('parent_id', 'ROOT'),
            'created_at': item.get('created_at'),
            'children': [],
        }

    # Link children to parents
    roots = []
    for fid, node in nodes.items():
        parent_id = node['parent_id']
        if parent_id in nodes:
            nodes[parent_id]['children'].append(node)
        else:
            # Parent not in visible set — this is a root for this user
            roots.append(node)

    return roots
