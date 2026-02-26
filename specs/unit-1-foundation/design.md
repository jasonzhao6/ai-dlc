# Unit 1: Project Foundation — Design

## Project Structure

```
s3-file-sharing/
├── template.yaml              # SAM template
├── backend/
│   ├── shared/                # Shared utilities across Lambdas
│   │   ├── __init__.py
│   │   ├── db.py              # DynamoDB client, Decimal serializer
│   │   ├── response.py        # Standardized JSON response builder
│   │   └── auth_middleware.py  # Session validation (implemented in Unit 2)
│   ├── auth_users/            # Lambda: auth + user management (Unit 2)
│   │   └── handler.py
│   ├── folders/               # Lambda: folder management (Unit 3)
│   │   └── handler.py
│   ├── files/                 # Lambda: file operations (Unit 4+5)
│   │   └── handler.py
│   └── seed/                  # Lambda: admin account seeding (Unit 2)
│       └── handler.py
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── api/               # API client module
│   │   │   └── client.js
│   │   ├── components/        # Shared UI components
│   │   │   ├── ErrorBanner.jsx
│   │   │   └── Layout.jsx
│   │   ├── pages/             # Route-level pages
│   │   ├── App.jsx
│   │   └── index.jsx
│   └── package.json
├── tests/
│   └── integration/           # HTTPS integration tests per endpoint
└── README.md
```

## DynamoDB Single-Table Design

### Table Definition

- **Table Name**: `FileShareTable`
- **Partition Key**: `PK` (String)
- **Sort Key**: `SK` (String)
- **GSI-1**: `GSI1PK` (String) / `GSI1SK` (String) — for reverse lookups

### Entity Key Patterns

| Entity | PK | SK | GSI1PK | GSI1SK | Attributes |
|---|---|---|---|---|---|
| User | `USER#<username>` | `PROFILE` | `ROLE#<role>` | `USER#<username>` | password_hash, role, status, created_at, force_password_change |
| Session | `SESSION#<token>` | `SESSION` | `USER#<username>` | `SESSION#<token>` | username, role, created_at, ttl |
| Folder | `FOLDER#<folder_id>` | `META` | `PARENT#<parent_id>` | `FOLDER#<folder_id>` | name, parent_id, created_at |
| Assignment | `FOLDER#<folder_id>` | `ASSIGN#<username>` | `USER#<username>` | `ASSIGN#FOLDER#<folder_id>` | assigned_at |
| File | `FOLDER#<folder_id>` | `FILE#<file_id>` | `USER#<username>` | `FILE#<file_id>` | name, size, s3_key, uploaded_by, uploaded_at |

### Access Patterns

| Access Pattern | Query |
|---|---|
| Get user by username | PK=`USER#<username>`, SK=`PROFILE` |
| List users by role | GSI1: GSI1PK=`ROLE#<role>` |
| Get session by token | PK=`SESSION#<token>`, SK=`SESSION` |
| List sessions for user | GSI1: GSI1PK=`USER#<username>`, GSI1SK begins_with `SESSION#` |
| Get folder metadata | PK=`FOLDER#<id>`, SK=`META` |
| List child folders | GSI1: GSI1PK=`PARENT#<parent_id>` |
| List root folders | GSI1: GSI1PK=`PARENT#ROOT` |
| List folder assignments | PK=`FOLDER#<id>`, SK begins_with `ASSIGN#` |
| List folders for user | GSI1: GSI1PK=`USER#<username>`, GSI1SK begins_with `ASSIGN#FOLDER#` |
| List files in folder | PK=`FOLDER#<id>`, SK begins_with `FILE#` |
| List files by uploader | GSI1: GSI1PK=`USER#<username>`, GSI1SK begins_with `FILE#` |

### DynamoDB TTL

- Session records use DynamoDB TTL on a `ttl` attribute (epoch seconds) for automatic expiry.

## S3 Bucket Design

### File Storage Bucket

- **Name**: `file-share-storage-{stage}`
- **Key Format**: `files/<folder_id>/<file_id>/<original_filename>`
- **CORS**: Configured for PUT (upload) and GET (download) from front-end origin
- **Versioning**: Disabled (simplicity)
- **Lifecycle**: None initially

### Static Website Bucket

- **Name**: `file-share-frontend-{stage}`
- **Static Website Hosting**: Enabled
- **Index Document**: `index.html`
- **Error Document**: `index.html` (SPA client-side routing)

## API Gateway Design

### Base URL

`https://<api-id>.execute-api.<region>.amazonaws.com/{stage}`

### Resource Layout (stubs in Unit 1, implemented in later units)

| Method | Path | Lambda | Unit |
|---|---|---|---|
| POST | `/auth/login` | auth-users | 2 |
| POST | `/auth/logout` | auth-users | 2 |
| POST | `/auth/change-password` | auth-users | 2 |
| GET | `/users` | auth-users | 2 |
| POST | `/users` | auth-users | 2 |
| PUT | `/users/{username}` | auth-users | 2 |
| DELETE | `/users/{username}` | auth-users | 2 |
| POST | `/users/{username}/reset-password` | auth-users | 2 |
| GET | `/folders` | folders | 3 |
| POST | `/folders` | folders | 3 |
| PUT | `/folders/{folderId}` | folders | 3 |
| DELETE | `/folders/{folderId}` | folders | 3 |
| GET | `/folders/{folderId}/files` | files | 4 |
| POST | `/files/upload-url` | files | 4 |
| POST | `/files/download-url` | files | 4 |
| DELETE | `/files/{fileId}` | files | 4 |
| GET | `/files/search` | files | 5 |

## Error Handling Pattern

### Backend Response Helper (`shared/response.py`)

```python
import json
from decimal import Decimal

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return int(obj) if obj == int(obj) else float(obj)
        return super().default(obj)

def success(body, status_code=200):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body, cls=DecimalEncoder)
    }

def error(message, status_code=400):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps({"error": message})
    }
```

### Frontend Error Handler

- Global axios/fetch interceptor catches HTTP errors
- 401 → redirect to login
- 403 → "You don't have permission" message
- 4xx → display error message from response body
- 5xx → "Something went wrong, please try again" with retry button
- Network error → "Connection lost" with retry button
