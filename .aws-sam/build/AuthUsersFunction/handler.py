"""Auth & User Management Lambda handler.

Routes:
  POST /auth/login          - Login with username/password
  POST /auth/logout         - Logout (delete session)
  POST /auth/change-password - Change own password
  GET  /users               - List all users (Admin only)
  POST /users               - Create user (Admin only)
  PUT  /users/{username}    - Update user (Admin only)
  DELETE /users/{username}  - Delete/disable user (Admin only)
  POST /users/{username}/reset-password - Reset password (Admin only)
"""

import json
import secrets
import time
import bcrypt

from shared import db
from shared.response import success, error
from shared.auth_middleware import authenticate, require_auth, require_admin


# Session TTL: 24 hours
SESSION_TTL_SECONDS = 86400


def lambda_handler(event, context):
    """Route requests to the appropriate handler."""
    method = event.get('httpMethod', '')
    resource = event.get('resource', '')

    routes = {
        ('POST', '/auth/login'): handle_login,
        ('POST', '/auth/logout'): _auth(handle_logout),
        ('POST', '/auth/change-password'): _auth(handle_change_password),
        ('GET', '/users'): _admin(handle_list_users),
        ('POST', '/users'): _admin(handle_create_user),
        ('PUT', '/users/{username}'): _admin(handle_update_user),
        ('DELETE', '/users/{username}'): _admin(handle_delete_user),
        ('POST', '/users/{username}/reset-password'): _admin(handle_reset_password),
    }

    handler = routes.get((method, resource))
    if handler:
        return handler(event, context)

    # Handle OPTIONS for CORS preflight
    if method == 'OPTIONS':
        return success({})

    return error('Not found', 404)


def _auth(handler):
    """Wrap handler with authentication check."""
    return require_auth(handler)


def _admin(handler):
    """Wrap handler with authentication + admin check."""
    return require_auth(require_admin(handler))


# ============================================================
# Auth handlers
# ============================================================

def handle_login(event, context):
    """Validate credentials, create session, return token."""
    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return error('Invalid JSON', 400)

    username = body.get('username', '').strip()
    password = body.get('password', '')

    if not username or not password:
        return error('Username and password are required', 400)

    # Get user record
    user = db.get_item(f'USER#{username}', 'PROFILE')
    if not user:
        return error('Invalid credentials', 401)

    # Check user status
    if user.get('status') == 'disabled':
        return error('Invalid credentials', 401)

    # Verify password
    stored_hash = user['password_hash']
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
    if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
        return error('Invalid credentials', 401)

    # Create session
    token = secrets.token_urlsafe(32)
    now = int(time.time())
    session_item = {
        'PK': f'SESSION#{token}',
        'SK': 'SESSION',
        'GSI1PK': f'USER#{username}',
        'GSI1SK': f'SESSION#{token}',
        'username': username,
        'role': user['role'],
        'created_at': now,
        'ttl': now + SESSION_TTL_SECONDS,
    }
    db.put_item(session_item)

    return success({
        'token': token,
        'username': username,
        'role': user['role'],
        'force_password_change': user.get('force_password_change', False),
    })


def handle_logout(event, context):
    """Delete session from DynamoDB."""
    user = event['user']
    token = user['token']
    db.delete_item(f'SESSION#{token}', 'SESSION')
    return success({'message': 'Logged out'})


def handle_change_password(event, context):
    """Change own password."""
    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return error('Invalid JSON', 400)

    user = event['user']
    current_password = body.get('current_password', '')
    new_password = body.get('new_password', '')

    if not current_password or not new_password:
        return error('Current password and new password are required', 400)

    if len(new_password) < 8:
        return error('New password must be at least 8 characters', 400)

    # Get user record to verify current password
    user_record = db.get_item(f'USER#{user["username"]}', 'PROFILE')
    if not user_record:
        return error('User not found', 404)

    stored_hash = user_record['password_hash']
    if isinstance(stored_hash, str):
        stored_hash = stored_hash.encode('utf-8')
    if not bcrypt.checkpw(current_password.encode('utf-8'), stored_hash):
        return error('Current password is incorrect', 400)

    # Hash and update new password
    new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
    db.update_item(
        f'USER#{user["username"]}', 'PROFILE',
        'SET password_hash = :ph, force_password_change = :fpc',
        {':ph': new_hash, ':fpc': False}
    )

    return success({'message': 'Password changed successfully'})


# ============================================================
# User Management handlers
# ============================================================

def handle_create_user(event, context):
    """Create a new user (Admin only)."""
    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return error('Invalid JSON', 400)

    username = body.get('username', '').strip()
    password = body.get('password', '')
    role = body.get('role', '')

    if not username or not password or not role:
        return error('Username, password, and role are required', 400)

    if role not in ('Admin', 'Uploader', 'Reader', 'Viewer'):
        return error('Role must be Admin, Uploader, Reader, or Viewer', 400)

    if len(password) < 8:
        return error('Password must be at least 8 characters', 400)

    # Hash password
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')

    now = int(time.time())
    user_item = {
        'PK': f'USER#{username}',
        'SK': 'PROFILE',
        'GSI1PK': f'ROLE#{role}',
        'GSI1SK': f'USER#{username}',
        'username': username,
        'password_hash': password_hash,
        'role': role,
        'status': 'active',
        'force_password_change': True,
        'created_at': now,
    }

    try:
        db.put_item(user_item, condition_expression='attribute_not_exists(PK)')
    except Exception as e:
        if 'ConditionalCheckFailedException' in str(e):
            return error(f'User "{username}" already exists', 409)
        raise

    return success({'message': f'User "{username}" created', 'username': username}, 201)


def handle_update_user(event, context):
    """Update user role/status (Admin only)."""
    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return error('Invalid JSON', 400)

    target_username = event.get('pathParameters', {}).get('username', '')
    admin_username = event['user']['username']

    # Get current user record
    user_record = db.get_item(f'USER#{target_username}', 'PROFILE')
    if not user_record:
        return error(f'User "{target_username}" not found', 404)

    new_role = body.get('role')
    new_status = body.get('status')

    # Prevent Admin from changing own role
    if target_username == admin_username and new_role and new_role != 'Admin':
        return error('Cannot change your own role away from Admin', 400)

    update_parts = []
    values = {}
    attr_names = {}

    if new_role:
        if new_role not in ('Admin', 'Uploader', 'Reader', 'Viewer'):
            return error('Role must be Admin, Uploader, Reader, or Viewer', 400)
        # 'role' is a DynamoDB reserved word
        update_parts.append('#rl = :r')
        attr_names['#rl'] = 'role'
        values[':r'] = new_role
        # Update GSI1PK for role-based queries
        update_parts.append('GSI1PK = :gsi1pk')
        values[':gsi1pk'] = f'ROLE#{new_role}'

    if new_status:
        if new_status not in ('active', 'disabled'):
            return error('Status must be active or disabled', 400)
        # 'status' is a DynamoDB reserved word
        update_parts.append('#st = :s')
        attr_names['#st'] = 'status'
        values[':s'] = new_status

    if not update_parts:
        return error('No fields to update', 400)

    update_expr = 'SET ' + ', '.join(update_parts)

    kwargs = {
        'Key': {'PK': f'USER#{target_username}', 'SK': 'PROFILE'},
        'UpdateExpression': update_expr,
        'ExpressionAttributeValues': values,
        'ReturnValues': 'ALL_NEW'
    }
    if attr_names:
        kwargs['ExpressionAttributeNames'] = attr_names

    table = db._get_table()
    result = table.update_item(**kwargs)

    # If user was disabled, invalidate their sessions
    if new_status == 'disabled':
        _invalidate_user_sessions(target_username)

    updated = result.get('Attributes', {})
    return success({
        'username': target_username,
        'role': updated.get('role'),
        'status': updated.get('status'),
    })


def handle_delete_user(event, context):
    """Delete or disable a user (Admin only)."""
    target_username = event.get('pathParameters', {}).get('username', '')
    admin_username = event['user']['username']

    if target_username == admin_username:
        return error('Cannot delete your own account', 400)

    # Check user exists
    user_record = db.get_item(f'USER#{target_username}', 'PROFILE')
    if not user_record:
        return error(f'User "{target_username}" not found', 404)

    # Delete user record
    db.delete_item(f'USER#{target_username}', 'PROFILE')

    # Invalidate all sessions
    _invalidate_user_sessions(target_username)

    # Delete all folder assignments for this user
    assignments = db.query(
        f'USER#{target_username}',
        sk_begins_with='ASSIGN#FOLDER#',
        index_name='GSI1'
    )
    if assignments:
        keys_to_delete = []
        for a in assignments:
            keys_to_delete.append({'PK': a['PK'], 'SK': a['SK']})
        db.batch_delete(keys_to_delete)

    return success({'message': f'User "{target_username}" deleted'})


def handle_list_users(event, context):
    """List all users (Admin only)."""
    query_params = event.get('queryStringParameters') or {}
    role_filter = query_params.get('role')
    status_filter = query_params.get('status')

    if role_filter:
        # Query GSI1 for specific role
        items = db.query(f'ROLE#{role_filter}', index_name='GSI1')
    else:
        # Scan for all users (filter by SK=PROFILE)
        from boto3.dynamodb.conditions import Attr
        items = db.scan(filter_expression=Attr('SK').eq('PROFILE'))

    users = []
    for item in items:
        if item.get('SK') != 'PROFILE':
            continue
        if status_filter and item.get('status') != status_filter:
            continue
        users.append({
            'username': item.get('username'),
            'role': item.get('role'),
            'status': item.get('status'),
            'created_at': item.get('created_at'),
        })

    return success({'users': users})


def handle_reset_password(event, context):
    """Reset another user's password (Admin only)."""
    target_username = event.get('pathParameters', {}).get('username', '')

    # Check user exists
    user_record = db.get_item(f'USER#{target_username}', 'PROFILE')
    if not user_record:
        return error(f'User "{target_username}" not found', 404)

    # Generate temp password
    temp_password = secrets.token_urlsafe(12)
    password_hash = bcrypt.hashpw(temp_password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')

    db.update_item(
        f'USER#{target_username}', 'PROFILE',
        'SET password_hash = :ph, force_password_change = :fpc',
        {':ph': password_hash, ':fpc': True}
    )

    return success({
        'message': f'Password reset for "{target_username}"',
        'temporary_password': temp_password,
    })


# ============================================================
# Helper functions
# ============================================================

def _invalidate_user_sessions(username):
    """Delete all sessions for a given user."""
    sessions = db.query(
        f'USER#{username}',
        sk_begins_with='SESSION#',
        index_name='GSI1'
    )
    if sessions:
        keys_to_delete = [{'PK': s['PK'], 'SK': s['SK']} for s in sessions]
        db.batch_delete(keys_to_delete)
