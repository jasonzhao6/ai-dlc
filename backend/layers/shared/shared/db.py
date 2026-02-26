"""DynamoDB client with Decimal-safe serialization."""

import os
import boto3
from boto3.dynamodb.conditions import Key, Attr
from decimal import Decimal
import json


TABLE_NAME = os.environ.get('TABLE_NAME', 'FileShareTable-dev')

_dynamodb = None
_table = None


def _get_table():
    """Lazy-init DynamoDB table resource."""
    global _dynamodb, _table
    if _table is None:
        endpoint_url = os.environ.get('DYNAMODB_ENDPOINT')
        if endpoint_url:
            # Local DynamoDB: use a fresh Session with dummy credentials
            # to avoid SAM local's injected session token
            session = boto3.Session(
                aws_access_key_id='dummy',
                aws_secret_access_key='dummy',
                region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
            )
            _dynamodb = session.resource('dynamodb', endpoint_url=endpoint_url)
        else:
            _dynamodb = boto3.resource('dynamodb')
        _table = _dynamodb.Table(TABLE_NAME)
    return _table


class DecimalEncoder(json.JSONEncoder):
    """JSON encoder that handles DynamoDB Decimal types."""
    def default(self, obj):
        if isinstance(obj, Decimal):
            if obj % 1 == 0:
                return int(obj)
            return float(obj)
        return super().default(obj)


def to_json(obj):
    """Serialize object to JSON string, handling Decimals."""
    return json.dumps(obj, cls=DecimalEncoder)


def put_item(item, condition_expression=None):
    """Put an item into the table."""
    table = _get_table()
    kwargs = {'Item': item}
    if condition_expression:
        kwargs['ConditionExpression'] = condition_expression
    return table.put_item(**kwargs)


def get_item(pk, sk):
    """Get a single item by PK and SK."""
    table = _get_table()
    response = table.get_item(Key={'PK': pk, 'SK': sk})
    return response.get('Item')


def delete_item(pk, sk):
    """Delete a single item by PK and SK."""
    table = _get_table()
    return table.delete_item(Key={'PK': pk, 'SK': sk})


def update_item(pk, sk, update_expression, expression_values,
                condition_expression=None, expression_attr_names=None):
    """Update an item with an update expression."""
    table = _get_table()
    kwargs = {
        'Key': {'PK': pk, 'SK': sk},
        'UpdateExpression': update_expression,
        'ExpressionAttributeValues': expression_values,
        'ReturnValues': 'ALL_NEW'
    }
    if condition_expression:
        kwargs['ConditionExpression'] = condition_expression
    if expression_attr_names:
        kwargs['ExpressionAttributeNames'] = expression_attr_names
    return table.update_item(**kwargs)


def query(pk, sk_begins_with=None, index_name=None, filter_expression=None):
    """Query items by PK and optional SK prefix."""
    table = _get_table()
    key_condition = Key('PK').eq(pk)
    if index_name:
        key_condition = Key('GSI1PK').eq(pk)
        if sk_begins_with:
            key_condition = key_condition & Key('GSI1SK').begins_with(sk_begins_with)
    elif sk_begins_with:
        key_condition = key_condition & Key('SK').begins_with(sk_begins_with)

    kwargs = {'KeyConditionExpression': key_condition}
    if index_name:
        kwargs['IndexName'] = index_name
    if filter_expression:
        kwargs['FilterExpression'] = filter_expression

    items = []
    while True:
        response = table.query(**kwargs)
        items.extend(response.get('Items', []))
        if 'LastEvaluatedKey' not in response:
            break
        kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
    return items


def scan(filter_expression=None):
    """Scan the entire table with an optional filter."""
    table = _get_table()
    kwargs = {}
    if filter_expression:
        kwargs['FilterExpression'] = filter_expression
    items = []
    while True:
        response = table.scan(**kwargs)
        items.extend(response.get('Items', []))
        if 'LastEvaluatedKey' not in response:
            break
        kwargs['ExclusiveStartKey'] = response['LastEvaluatedKey']
    return items


def batch_delete(keys):
    """Batch delete items. Keys is a list of {'PK': ..., 'SK': ...} dicts."""
    table = _get_table()
    with table.batch_writer() as batch:
        for key in keys:
            batch.delete_item(Key=key)
