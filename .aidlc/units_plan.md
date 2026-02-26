# Units Plan — S3 File-Sharing System

## Objective

Group the 30 user stories into independently buildable, cohesive units ordered by dependency. Each unit maps to a spec folder under `specs/` containing requirements, design, and tasks.

## Proposed Units

Based on dependency analysis and the consolidated Lambda pattern (vision.md: one Lambda per API resource), I propose **5 units**:

| Order | Unit | Stories | Lambda | Depends On |
|---|---|---|---|---|
| 1 | Project Foundation | US-028, US-029, US-030 | N/A (scaffolding) | — |
| 2 | Auth, Sessions & User Management | US-001–US-010, US-025 | `auth-users` | Unit 1 |
| 3 | Folder Management | US-011–US-017 | `folders` | Unit 2 |
| 4 | File Operations | US-018–US-022, US-026, US-027 | `files` | Unit 3 |
| 5 | Search & Sort | US-023, US-024 | extends `files` | Unit 4 |

### Rationale

- **Unit 1** sets up the SAM project, DynamoDB tables, S3 buckets, API Gateway, React skeleton, and error handling patterns. Everything depends on this.
- **Unit 2** combines Auth + User Management because they share the same DynamoDB users table and are tightly coupled (login needs users, user CRUD needs auth). Authorization middleware (US-025) lives here since all subsequent units depend on it.
- **Unit 3** is folder CRUD + user-folder assignments. Depends on Unit 2 because assignments reference users.
- **Unit 4** is file upload/download/delete + pre-signed URL security + file size validation. Depends on Unit 3 because files live in folders.
- **Unit 5** adds search and sort on top of the file browsing built in Unit 4.

> **Resolved**: Auth + User Management kept as one unit. 5 units confirmed.

## Plan Steps

### Phase 1: Spec Structure Setup

- [x] **Step 1 — Create spec directory structure**
  Create `specs/` with sub-folders for each unit:
  ```
  specs/
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

### Phase 2: Write Specs (per unit)

- [x] **Step 2 — Write Unit 1: Project Foundation specs**
  - `requirements.md`: US-028, US-029, US-030 with traceability
  - `design.md`: SAM template structure, DynamoDB table schemas, S3 bucket config, API Gateway resource layout, React project structure, error handling pattern
  - `tasks.md`: Actionable dev tasks with checkboxes
  > **Resolved**: Single-table DynamoDB design.

- [x] **Step 3 — Write Unit 2: Auth, Sessions & User Management specs**
  - `requirements.md`: US-001–US-010, US-025 with traceability
  - `design.md`: Auth Lambda handler structure, session token format, password hashing, authorization middleware, API routes, React pages (login, user list, user form)
  - `tasks.md`: Actionable dev tasks with checkboxes

- [x] **Step 4 — Write Unit 3: Folder Management specs**
  - `requirements.md`: US-011–US-017 with traceability
  - `design.md`: Folder Lambda handler, nested folder data model, assignment model, folder hierarchy traversal, API routes, React pages (folder tree, assignment UI)
  - `tasks.md`: Actionable dev tasks with checkboxes

- [x] **Step 5 — Write Unit 4: File Operations specs**
  - `requirements.md`: US-018–US-022, US-026, US-027 with traceability
  - `design.md`: Files Lambda handler, pre-signed URL generation, S3 key structure, file metadata model, upload/download flow, API routes, React pages (file browser, upload UI)
  - `tasks.md`: Actionable dev tasks with checkboxes

- [x] **Step 6 — Write Unit 5: Search & Sort specs**
  - `requirements.md`: US-023, US-024 with traceability
  - `design.md`: Search query approach (DynamoDB scan/filter vs. GSI), sort implementation (client-side vs. server-side), API changes, React component updates
  - `tasks.md`: Actionable dev tasks with checkboxes

### Phase 3: Cross-Unit Summary

- [x] **Step 7 — Write unit dependency map and build order summary**
  Create `specs/README.md` with unit overview, dependency diagram, and story-to-unit traceability matrix.

- [x] **Step 8 — Present specs for review**
  Share completed specs for your feedback.

## Deliverables

| Deliverable | Location |
|---|---|
| Units Plan (this file) | `.aidlc/units_plan.md` |
| Unit 1 Specs | `specs/unit-1-foundation/` |
| Unit 2 Specs | `specs/unit-2-auth-users/` |
| Unit 3 Specs | `specs/unit-3-folders/` |
| Unit 4 Specs | `specs/unit-4-files/` |
| Unit 5 Specs | `specs/unit-5-search-sort/` |
| Specs Overview | `specs/README.md` |

## Resolved Questions

1. **Unit grouping**: Keep Auth + User Management as one unit.
2. **Unit count**: 5 units confirmed.
3. **DynamoDB design**: Single-table design.
