"""Create test JSON files for SAM local testing."""
import json

# Login request
with open('/tmp/login.json', 'w') as f:
    json.dump({'username': 'admin', 'password': 'ChangeMe123!'}, f)

print("Created /tmp/login.json")
