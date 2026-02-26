# Component Model Plan — S3 File-Sharing System

## Objective

Design a business-level component model that identifies all components, their attributes, behaviors, and interactions needed to implement all 30 user stories. No code — this is a logical/business architecture.

## Approach

The component model will cover three layers:
1. **Entity Components** — The core domain objects (User, Session, Folder, File, Assignment)
2. **Service Components** — Business logic that operates on entities (AuthService, UserService, FolderService, FileService, SearchService, AuthorizationService)
3. **Interface Components** — How users and external systems interact (API endpoints, UI pages, infrastructure integrations)

Each component will define:
- **Attributes**: Data it owns or manages
- **Behaviors**: Operations it performs
- **Interactions**: Which other components it collaborates with, and for which user stories

## Plan Steps

- [x] **Step 1 — Define Entity Components**
  Document the 5 core domain entities (User, Session, Folder, File, Assignment) with their attributes and business rules.

- [x] **Step 2 — Define Service Components**
  Document the 6 service components with their behaviors, which entities they operate on, and business rules they enforce.
  - Authentication Service (US-001–US-006)
  - User Management Service (US-005, US-007–US-010)
  - Authorization Service (US-025)
  - Folder Management Service (US-011–US-017)
  - File Management Service (US-018–US-022, US-026, US-027)
  - Search & Sort Service (US-023, US-024)

- [x] **Step 3 — Define Interface Components**
  Document the API layer (endpoint groups) and UI layer (pages/views) that expose service behaviors to users.
  - API interface: route groups mapped to services
  - UI interface: pages mapped to personas and user stories

- [x] **Step 4 — Define Infrastructure Components**
  Document the infrastructure components (Data Store, File Store, Pre-Signed URL Generator) and how services depend on them.

- [x] **Step 5 — Map Component Interactions per User Story**
  For each of the 30 user stories, trace the interaction path: UI → API → Service → Entity → Infrastructure. This ensures full coverage.

- [x] **Step 6 — Create Component Interaction Diagram**
  A high-level diagram showing how all components relate to each other.

- [x] **Step 7 — Self-review for completeness**
  Verify every user story is covered by at least one interaction path. Flag any gaps.

- [x] **Step 8 — Present for review**
  Share the completed component model for feedback.

## Deliverables

| Deliverable | Location |
|---|---|
| Component Model Plan (this file) | `.aidlc/component_model_plan.md` |
| Component Model | `.aidlc/component_model.md` |
