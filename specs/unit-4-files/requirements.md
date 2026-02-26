# Unit 4: File Operations — Requirements

## Dependencies

- **Depends on**: Unit 3 (folders must exist for files to live in, assignment checks)

## Stories Covered

| Story | Title | Summary |
|---|---|---|
| US-018 | Upload File | Upload via S3 pre-signed URL, max 1GB, metadata in DynamoDB |
| US-019 | Download File | Download via S3 pre-signed URL, Admin + Reader only |
| US-020 | View/List Files in a Folder | List files + sub-folders with metadata |
| US-021 | Admin Delete Any File | Admin can delete any file |
| US-022 | Uploader Delete Own File | Uploader can delete only their own files |
| US-026 | File Size Validation | Enforce 1GB max on front-end and back-end |
| US-027 | Pre-Signed URL Security | Short-lived, scoped pre-signed URLs |

## Functional Requirements

### FR-1: File Upload (US-018, US-026, US-027)
- User requests a pre-signed upload URL from Lambda
- Lambda validates: user has upload permission for the folder, file size <= 1GB
- Lambda generates S3 pre-signed PUT URL (TTL: 15 min, configurable)
- Client uploads directly to S3 using the pre-signed URL
- After upload, Lambda records file metadata in DynamoDB
- Allowed roles: Admin (any folder), Uploader (assigned folders only)
- Front-end validates file size before requesting URL

### FR-2: File Download (US-019, US-027)
- User requests a pre-signed download URL from Lambda
- Lambda validates: user has download permission for the folder
- Lambda generates S3 pre-signed GET URL (TTL: 15 min, configurable)
- Client downloads directly from S3
- Allowed roles: Admin (any file), Reader (assigned folders only)
- Uploader and Viewer cannot download; download action hidden in UI

### FR-3: File Listing (US-020)
- List files in a folder: query DynamoDB PK=`FOLDER#<id>`, SK begins_with `FILE#`
- Each file shows: name, size, upload date, uploader name
- Sub-folders shown alongside files
- Breadcrumb navigation for folder path
- All personas with folder access can list files

### FR-4: File Deletion (US-021, US-022)
- Admin can delete any file: delete from S3 + remove metadata from DynamoDB
- Uploader can delete only files where `uploaded_by` matches their username
- Confirmation prompt in UI before deletion
- Reader and Viewer cannot delete; delete action hidden in UI

### FR-5: Pre-Signed URL Security (US-027)
- Upload URLs: 15-minute TTL (configurable via environment variable)
- Download URLs: 15-minute TTL (configurable via environment variable)
- Each URL scoped to the specific S3 object key
- Expired URLs return S3 AccessDenied error

## Non-Functional Requirements

- Pre-signed URLs must not be logged or cached server-side
- File upload does not go through API Gateway (direct S3)
- File metadata must be recorded in DynamoDB after successful upload
- S3 key format: `files/<folder_id>/<file_id>/<original_filename>`
