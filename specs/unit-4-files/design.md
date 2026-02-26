# Unit 4: File Operations — Design

## Lambda: `files`

Single consolidated Lambda handling all file operation routes.

### Handler Routing

```python
# backend/files/handler.py

def lambda_handler(event, context):
    method = event["httpMethod"]
    path = event["resource"]

    routes = {
        ("GET", "/folders/{folderId}/files"): handle_list_files,
        ("POST", "/files/upload-url"): handle_get_upload_url,
        ("POST", "/files/download-url"): handle_get_download_url,
        ("POST", "/files/confirm-upload"): handle_confirm_upload,
        ("DELETE", "/files/{fileId}"): handle_delete_file,
    }

    handler = routes.get((method, path))
    if not handler:
        return error("Not found", 404)
    return handler(event, context)
```

### API Routes

| Method | Path | Auth | Role Restriction | Handler |
|---|---|---|---|---|
| GET | `/folders/{folderId}/files` | Yes | Any with folder access | `handle_list_files` |
| POST | `/files/upload-url` | Yes | Admin, Uploader (assigned) | `handle_get_upload_url` |
| POST | `/files/confirm-upload` | Yes | Admin, Uploader (assigned) | `handle_confirm_upload` |
| POST | `/files/download-url` | Yes | Admin, Reader (assigned) | `handle_get_download_url` |
| DELETE | `/files/{fileId}` | Yes | Admin (any), Uploader (own) | `handle_delete_file` |

### Upload Flow

```
Client                    API Gateway     Lambda                  S3              DynamoDB
  |                          |               |                     |                 |
  | 1. Validate file size    |               |                     |                 |
  |    (client-side, <1GB)   |               |                     |                 |
  |                          |               |                     |                 |
  | 2. POST /files/upload-url|               |                     |                 |
  |    {folderId, fileName,  |               |                     |                 |
  |     fileSize}            |               |                     |                 |
  |------------------------->|-------------->|                     |                 |
  |                          |               | 3. Verify role +    |                 |
  |                          |               |    folder access    |                 |
  |                          |               | 4. Validate size    |                 |
  |                          |               |    <= 1GB           |                 |
  |                          |               | 5. Generate file_id |                 |
  |                          |               |    (uuid4)          |                 |
  |                          |               | 6. Generate         |                 |
  |                          |               |    pre-signed PUT -->|                 |
  |                          |               |    URL (15 min TTL) |                 |
  |<-------------------------|<--------------|                     |                 |
  | {upload_url, file_id}    |               |                     |                 |
  |                          |               |                     |                 |
  | 7. PUT file directly ----|---------------|-------------------->|                 |
  |    to S3 via pre-signed  |               |                     |                 |
  |    URL                   |               |                     |                 |
  |                          |               |                     |                 |
  | 8. POST /files/confirm-  |               |                     |                 |
  |    upload {file_id,      |               |                     |                 |
  |    folderId, fileName,   |               |                     |                 |
  |    fileSize}             |               |                     |                 |
  |------------------------->|-------------->|                     |                 |
  |                          |               | 9. Write file       |                 |
  |                          |               |    metadata --------|---------------->|
  |<-------------------------|<------------- | 200 OK              |                 |
```

### Download Flow

```
Client                    API Gateway     Lambda                  S3
  |                          |               |                     |
  | POST /files/download-url |               |                     |
  | {fileId}                 |               |                     |
  |------------------------->|-------------->|                     |
  |                          |               | 1. Get file metadata|
  |                          |               |    from DynamoDB    |
  |                          |               | 2. Verify role +   |
  |                          |               |    folder access   |
  |                          |               | 3. Generate        |
  |                          |               |    pre-signed GET->|
  |                          |               |    URL (15 min)    |
  |<-------------------------|<--------------|                     |
  | {download_url}           |               |                     |
  |                          |               |                     |
  | GET file directly -------|---------------|-------------------->|
  | from S3 via pre-signed   |               |                     |
  | URL                      |               |                     |
```

### Delete Flow

```python
def handle_delete_file(event, context):
    user = event["user"]
    file_id = event["pathParameters"]["fileId"]

    # Get file metadata from DynamoDB (need to find it by file_id)
    # Query GSI1: GSI1PK=USER#<any>, GSI1SK=FILE#<file_id> — or store file_id → folder_id mapping
    file_record = get_file_by_id(file_id)

    if not file_record:
        return error("File not found", 404)

    # Authorization check
    if user["role"] == "Admin":
        pass  # Admin can delete any file
    elif user["role"] == "Uploader" and file_record["uploaded_by"] == user["username"]:
        pass  # Uploader can delete own files
    else:
        return error("Forbidden", 403)

    # Delete from S3
    s3.delete_object(Bucket=BUCKET, Key=file_record["s3_key"])

    # Delete metadata from DynamoDB
    db.delete_item(PK=f"FOLDER#{file_record['folder_id']}", SK=f"FILE#{file_id}")

    return success({"message": "File deleted"})
```

### DynamoDB Operations

| Operation | Key Pattern | Notes |
|---|---|---|
| List files in folder | PK=`FOLDER#<id>`, SK begins_with `FILE#` | Returns file metadata |
| Record file upload | PK=`FOLDER#<id>`, SK=`FILE#<file_id>` | name, size, s3_key, uploaded_by, uploaded_at |
| Get file by ID | PK=`FOLDER#<folder_id>`, SK=`FILE#<file_id>` | Need folder_id; or add GSI for file_id lookup |
| Delete file metadata | PK=`FOLDER#<id>`, SK=`FILE#<file_id>` | After S3 delete |

### File ID Lookup Design Decision

Since files are stored under `PK=FOLDER#<id>`, looking up a file by `file_id` alone requires knowing the `folder_id`. Options:

**Chosen approach**: The delete and download APIs accept `fileId` in the path. The client always has the `folder_id` from the current browsing context, so the request body includes `folderId` as well. This avoids needing an extra GSI for file lookups.

### S3 Key Structure

```
files/<folder_id>/<file_id>/<original_filename>
```

- `folder_id`: UUID of the folder
- `file_id`: UUID generated at upload time
- `original_filename`: preserved for download (Content-Disposition)

### Pre-Signed URL Configuration

| Parameter | Upload | Download |
|---|---|---|
| Method | PUT | GET |
| TTL | 15 minutes (env: `UPLOAD_URL_TTL`) | 15 minutes (env: `DOWNLOAD_URL_TTL`) |
| Scope | Specific S3 key | Specific S3 key |
| Content-Length | Set max via `Conditions` | N/A |

### React Pages & Components

| Component | Route/Location | Description |
|---|---|---|
| File List | `/folders/:folderId` (update) | List files + sub-folders in folder detail page |
| Upload Button | In folder detail page | File picker, size validation, progress bar |
| Download Button | Per file row | Visible for Admin + Reader only |
| Delete Button | Per file row | Admin: all files; Uploader: own files only |
| Upload Progress | Modal/inline | Shows upload percentage during S3 PUT |
