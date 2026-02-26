# S3 File-Sharing System — Specs Overview

## Units & Build Order

```
Unit 1: Foundation ──> Unit 2: Auth & Users ──> Unit 3: Folders ──> Unit 4: Files ──> Unit 5: Search & Sort
   (scaffolding)        (auth, sessions,         (folder CRUD,       (upload,          (search by name,
                         user CRUD,               nesting,            download,          sort by column)
                         authorization)           assignments)        delete)
```

## Unit Summary

| Unit | Name | Stories | Tasks | Depends On |
|---|---|---|---|---|
| 1 | Project Foundation | US-028, US-029, US-030 | T1.1–T1.20 | — |
| 2 | Auth, Sessions & User Management | US-001–US-010, US-025 | T2.1–T2.30 | Unit 1 |
| 3 | Folder Management | US-011–US-017 | T3.1–T3.22 | Unit 2 |
| 4 | File Operations | US-018–US-022, US-026, US-027 | T4.1–T4.21 | Unit 3 |
| 5 | Search & Sort | US-023, US-024 | T5.1–T5.15 | Unit 4 |

## Story-to-Unit Traceability

| Story | Title | Unit |
|---|---|---|
| US-001 | User Login | 2 |
| US-002 | User Logout | 2 |
| US-003 | Session Persistence | 2 |
| US-004 | Change Own Password | 2 |
| US-005 | Admin Reset User Password | 2 |
| US-006 | Initial Admin Account Seeding | 2 |
| US-007 | Create User | 2 |
| US-008 | Update User | 2 |
| US-009 | Delete/Disable User | 2 |
| US-010 | List Users | 2 |
| US-011 | Create Folder | 3 |
| US-012 | Create Sub-Folder | 3 |
| US-013 | Rename Folder | 3 |
| US-014 | Delete Folder | 3 |
| US-015 | List and Browse Folders | 3 |
| US-016 | Assign Users to Folders | 3 |
| US-017 | Unassign Users from Folders | 3 |
| US-018 | Upload File | 4 |
| US-019 | Download File | 4 |
| US-020 | View/List Files in a Folder | 4 |
| US-021 | Admin Delete Any File | 4 |
| US-022 | Uploader Delete Own File | 4 |
| US-023 | Search Files by Name | 5 |
| US-024 | Sort Files | 5 |
| US-025 | Role-Based Authorization | 2 |
| US-026 | File Size Validation | 4 |
| US-027 | Pre-Signed URL Security | 4 |
| US-028 | API Gateway + Lambda Backend | 1 |
| US-029 | Static Front-End Hosting | 1 |
| US-030 | Error Handling | 1 |

## Architecture Summary

### Backend
- **Runtime**: Python Lambda (local Python version, no containers)
- **Deployment**: AWS SAM
- **API**: API Gateway REST API
- **Database**: DynamoDB single-table design
- **Storage**: S3 (files + front-end hosting)

### Frontend
- **Framework**: React JS (SPA)
- **Hosting**: S3 static website
- **Communication**: API Gateway endpoints + S3 pre-signed URLs

### Lambda Consolidation

| Lambda | API Resource | Unit |
|---|---|---|
| `auth-users` | `/auth/*`, `/users/*` | 2 |
| `folders` | `/folders/*` | 3 |
| `files` | `/files/*`, `/folders/{id}/files` | 4, 5 |
| `seed` | CloudFormation Custom Resource | 2 |

### DynamoDB Single-Table Entity Map

| Entity | PK | SK |
|---|---|---|
| User | `USER#<username>` | `PROFILE` |
| Session | `SESSION#<token>` | `SESSION` |
| Folder | `FOLDER#<folder_id>` | `META` |
| Assignment | `FOLDER#<folder_id>` | `ASSIGN#<username>` |
| File | `FOLDER#<folder_id>` | `FILE#<file_id>` |

## Spec Locations

```
specs/
├── README.md                          (this file)
├── unit-1-foundation/
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
├── unit-2-auth-users/
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
├── unit-3-folders/
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
├── unit-4-files/
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
└── unit-5-search-sort/
    ├── requirements.md
    ├── design.md
    └── tasks.md
```
