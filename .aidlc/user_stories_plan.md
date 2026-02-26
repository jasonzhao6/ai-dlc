# User Stories Plan — S3 File-Sharing System

## Objective

Create well-defined user stories based on the high-level requirements in `vision.md` for an S3-backed web-based file-sharing system. The stories will serve as the development contract.

## Identified Personas (from vision.md)

1. **Admin** — Full access: manage users, folders, assignments, and all file operations
2. **Uploader** — View and upload files to assigned folders only
3. **Reader** — View and download files from assigned folders only
4. **Viewer** — View files in assigned folders only (no download, no upload)

## Plan Steps

### Phase 1: Analysis & Story Drafting

- [x] **Step 1 — Define persona descriptions and permissions matrix**
  Write a concise permissions matrix (CRUD per resource per persona) to ensure stories are consistent and complete.

- [x] **Step 2 — Draft Authentication & Session Management stories**
  Covers: login, logout, session persistence via DynamoDB, password reset/change-password.
  > **Resolved**: Password reset / change-password is in scope.

- [x] **Step 3 — Draft Admin: User Management stories**
  Covers: create user, update user (including folder assignments), delete/disable user, list users, initial admin account seeding.

- [x] **Step 4 — Draft Admin: Folder Management stories**
  Covers: create folder, create sub-folder, rename folder, delete folder, list folders, navigate folder hierarchy, assign/unassign users to folders.
  > **Resolved**: Folders support nesting (sub-folders).

- [x] **Step 5 — Draft File Operations stories**
  Covers: upload file (via S3 pre-signed URL, max 1GB), download file (via S3 pre-signed URL), view/list files in a folder, delete file.
  > **Resolved**: Admin can delete any file. Uploader can delete their own files only.

- [x] **Step 6 — Draft Search & Sort stories**
  Covers: search files by name, sort by name/date uploaded/size. Applicable to all personas who can browse.

- [x] **Step 7 — Draft Non-Functional / Cross-Cutting stories**
  Covers: authorization enforcement per role, error handling, file size validation (1GB limit), API Gateway + Lambda backend pattern, pre-signed URL expiry.

### Phase 2: Review & Refinement

- [x] **Step 8 — Compile all stories into `.aidlc/user_stories.md`**
  Assemble all drafted stories into a single deliverable file with consistent formatting.

- [x] **Step 9 — Self-review for completeness**
  Cross-check every requirement in `vision.md` against the stories to ensure full traceability. Flag any gaps.

- [ ] **Step 10 — Present stories for your review**
  Share the completed user stories for your feedback. Incorporate any requested changes.

## Deliverables

| Deliverable | Location |
|---|---|
| User Stories Plan (this file) | `.aidlc/user_stories_plan.md` |
| User Stories | `.aidlc/user_stories.md` |

## Story Format

Each story will follow this template:

```
### US-XXX: <Title>
**As a** <persona>,
**I want to** <action>,
**So that** <benefit>.

**Acceptance Criteria:**
- [ ] AC1: ...
- [ ] AC2: ...
```

## Resolved Questions

1. **Password reset**: In scope — include password reset / change-password flow.
2. **Folder nesting**: Support nesting (sub-folders).
3. **File deletion**: Admin can delete any file. Uploader can delete their own files only.
