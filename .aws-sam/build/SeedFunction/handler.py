"""Seed Lambda — Creates default Admin account on first deployment.

Can be invoked manually or as a CloudFormation Custom Resource.
Creates an 'admin' user with password 'ChangeMe123!' and force_password_change=True.
"""

import json
import time
import bcrypt

from shared import db
from shared.response import success, error


DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = 'ChangeMe123!'


def lambda_handler(event, context):
    """Handle both direct invocation and CloudFormation Custom Resource."""
    # Check if this is a CloudFormation Custom Resource request
    if 'RequestType' in event:
        return _handle_cfn(event, context)

    # Direct invocation
    return _seed_admin()


def _handle_cfn(event, context):
    """Handle CloudFormation Custom Resource lifecycle events."""
    import urllib.request

    request_type = event.get('RequestType', '')
    response_url = event.get('ResponseURL', '')

    response_data = {}
    status = 'SUCCESS'

    try:
        if request_type == 'Create':
            result = _seed_admin()
            body = json.loads(result['body'])
            response_data = body
        # Update and Delete are no-ops
    except Exception as e:
        status = 'FAILED'
        response_data = {'Error': str(e)}

    # Send response back to CloudFormation
    if response_url:
        cfn_response = {
            'Status': status,
            'Reason': json.dumps(response_data),
            'PhysicalResourceId': f'seed-admin-{DEFAULT_ADMIN_USERNAME}',
            'StackId': event.get('StackId', ''),
            'RequestId': event.get('RequestId', ''),
            'LogicalResourceId': event.get('LogicalResourceId', ''),
            'Data': response_data,
        }
        body = json.dumps(cfn_response).encode('utf-8')
        req = urllib.request.Request(
            response_url,
            data=body,
            headers={'Content-Type': ''},
            method='PUT'
        )
        urllib.request.urlopen(req)

    return response_data


def _seed_admin():
    """Create the default Admin user if it doesn't already exist."""
    # Check if admin already exists
    existing = db.get_item(f'USER#{DEFAULT_ADMIN_USERNAME}', 'PROFILE')
    if existing:
        return success({
            'message': f'Admin user "{DEFAULT_ADMIN_USERNAME}" already exists',
            'created': False,
        })

    # Hash the default password
    password_hash = bcrypt.hashpw(
        DEFAULT_ADMIN_PASSWORD.encode('utf-8'),
        bcrypt.gensalt(12)
    ).decode('utf-8')

    now = int(time.time())
    user_item = {
        'PK': f'USER#{DEFAULT_ADMIN_USERNAME}',
        'SK': 'PROFILE',
        'GSI1PK': 'ROLE#Admin',
        'GSI1SK': f'USER#{DEFAULT_ADMIN_USERNAME}',
        'username': DEFAULT_ADMIN_USERNAME,
        'password_hash': password_hash,
        'role': 'Admin',
        'status': 'active',
        'force_password_change': True,
        'created_at': now,
    }

    db.put_item(user_item)

    return success({
        'message': f'Admin user "{DEFAULT_ADMIN_USERNAME}" created with default password',
        'created': True,
        'username': DEFAULT_ADMIN_USERNAME,
        'default_password': DEFAULT_ADMIN_PASSWORD,
    })
