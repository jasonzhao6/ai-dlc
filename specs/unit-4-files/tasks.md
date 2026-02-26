# Unit 4: File Operations — Tasks

## Backend Tasks

- [x] **T4.1**: Implement `handle_get_upload_url` — validate role + folder access + file size, generate pre-signed PUT URL
- [x] **T4.2**: Implement `handle_confirm_upload` — record file metadata in DynamoDB after successful S3 upload
- [x] **T4.3**: Implement `handle_get_download_url` — validate role + folder access, generate pre-signed GET URL
- [x] **T4.4**: Implement `handle_list_files` — query files in folder, include sub-folders, respect role-based access
- [x] **T4.5**: Implement `handle_delete_file` — Admin deletes any, Uploader deletes own, delete from S3 + DynamoDB
- [x] **T4.6**: Configure S3 bucket CORS for pre-signed URL PUT/GET from front-end origin (done in template.yaml)
- [x] **T4.7**: Add environment variables for `UPLOAD_URL_TTL` and `DOWNLOAD_URL_TTL` in SAM template
- [x] **T4.8**: Update SAM template: wire `files` Lambda to API Gateway routes, grant S3 read/write permissions

## Frontend Tasks

- [x] **T4.9**: Build file list component in folder detail page — columns: name, size, date, uploader
- [x] **T4.10**: Build upload flow — file picker, client-side size validation (<1GB), request pre-signed URL, PUT to S3, confirm upload
- [x] **T4.11**: Build upload progress indicator — show percentage during S3 PUT (using XMLHttpRequest)
- [x] **T4.12**: Build download button — request pre-signed URL, trigger browser download; visible for Admin + Reader only
- [x] **T4.13**: Build delete button — Admin sees on all files, Uploader sees on own files only; confirmation dialog
- [x] **T4.14**: Add breadcrumb navigation to folder detail page
- [x] **T4.15**: Conditionally show/hide upload, download, delete actions based on user role

## Integration Test Tasks

- [x] **T4.16**: Test POST `/files/upload-url` — Admin → 200 + URL; Uploader (assigned) → 200; Uploader (unassigned) → 403; Reader → 403; file > 1GB → 400
- [x] **T4.17**: Test full upload flow — get URL → confirm upload → verify file in DynamoDB (S3 PUT skipped in local)
- [x] **T4.18**: Test POST `/files/download-url` — Admin → 200 + URL; Reader (assigned) → 200; Uploader → 403; Viewer → 403
- [x] **T4.19**: Test GET `/folders/{folderId}/files` — returns files for authorized users; 403 for unauthorized
- [x] **T4.20**: Test DELETE `/files/{fileId}` — Admin deletes any → 200; Uploader deletes own → 200; Uploader deletes other's → 403; Reader → 403
- [ ] **T4.21**: Test pre-signed URL expiry — requires real S3 (post-deployment)
