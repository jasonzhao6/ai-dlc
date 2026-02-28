"""Seed admin user directly into DynamoDB Local for testing."""
import time
import bcrypt
import boto3

ENDPOINT = "http://localhost:8000"
REGION = "us-east-1"
TABLE_NAME = "FileShareTable-dev"

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url=ENDPOINT,
    region_name=REGION,
    aws_access_key_id="dummy",
    aws_secret_access_key="dummy",
)
table = dynamodb.Table(TABLE_NAME)

password_hash = bcrypt.hashpw(
    "ChangeMe123!".encode("utf-8"), bcrypt.gensalt(12)
).decode("utf-8")

table.put_item(
    Item={
        "PK": "USER#admin",
        "SK": "PROFILE",
        "GSI1PK": "ROLE#Admin",
        "GSI1SK": "USER#admin",
        "username": "admin",
        "password_hash": password_hash,
        "role": "Admin",
        "status": "active",
        "force_password_change": True,
        "created_at": int(time.time()),
    }
)

print('"created": true')
