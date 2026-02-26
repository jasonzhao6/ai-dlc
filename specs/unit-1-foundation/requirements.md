# Unit 1: Project Foundation — Requirements

## Stories Covered

| Story | Title | Summary |
|---|---|---|
| US-028 | API Gateway + Lambda Backend Pattern | Consolidated Python Lambdas per API resource, SAM without containers, integration tests, DynamoDB Decimal handling |
| US-029 | Static Front-End Hosting | React JS SPA hosted on S3, communicates via API Gateway |
| US-030 | Error Handling | Consistent JSON error format, user-friendly messages, CloudWatch logging |

## Functional Requirements

### FR-1: SAM Project Scaffold (US-028)
- AWS SAM template defining all infrastructure resources
- Python Lambda functions using the locally installed Python version
- SAM deployment configured without containers (`--use-container` must NOT be used)

### FR-2: DynamoDB Single-Table (US-028)
- One DynamoDB table for all entities (users, sessions, folders, files, assignments)
- Partition key (PK) and sort key (SK) design supporting all access patterns
- Global Secondary Indexes (GSIs) as needed for query patterns
- Decimal-safe JSON serialization in all Lambda responses

### FR-3: S3 Buckets (US-028, US-029)
- File storage bucket for uploaded files
- Static website hosting bucket for the React front-end
- Appropriate bucket policies and CORS configuration

### FR-4: API Gateway (US-028)
- REST API with resource stubs for: `/auth`, `/users`, `/folders`, `/files`
- CORS enabled for the front-end origin
- Each resource will be backed by a consolidated Lambda (one Lambda per resource)

### FR-5: React Project Skeleton (US-029)
- React JS project initialized (e.g., Create React App or Vite)
- Routing scaffold (login page, main app shell)
- API client module configured to call API Gateway endpoints
- Responsive layout for desktop browsers

### FR-6: Error Handling Pattern (US-030)
- Backend: All API errors return `{ "error": "<message>" }` with appropriate HTTP status codes
- Backend: Lambda functions log errors to CloudWatch
- Frontend: Global error handler displays user-friendly messages
- Frontend: Network errors show a retry option

## Non-Functional Requirements

- All infrastructure defined as code (SAM template)
- No hardcoded credentials or secrets in code
- CORS configured to allow only the front-end origin
