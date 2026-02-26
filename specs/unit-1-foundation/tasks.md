# Unit 1: Project Foundation — Tasks

## Backend Tasks

- [ ] **T1.1**: Initialize SAM project with `template.yaml`
- [ ] **T1.2**: Define DynamoDB `FileShareTable` in SAM template (PK, SK, GSI-1, TTL)
- [ ] **T1.3**: Define S3 file storage bucket with CORS config in SAM template
- [ ] **T1.4**: Define S3 static website bucket in SAM template
- [ ] **T1.5**: Define API Gateway REST API resource in SAM template with CORS
- [ ] **T1.6**: Create `backend/shared/db.py` — DynamoDB client with Decimal-safe serializer
- [ ] **T1.7**: Create `backend/shared/response.py` — success/error response helpers
- [ ] **T1.8**: Create placeholder Lambda handlers (`auth_users`, `folders`, `files`) returning 501 Not Implemented
- [ ] **T1.9**: Wire placeholder Lambdas to API Gateway routes in SAM template
- [ ] **T1.10**: Deploy SAM stack and verify API Gateway returns 501 for all endpoints

## Frontend Tasks

- [ ] **T1.11**: Initialize React project (Vite or CRA)
- [ ] **T1.12**: Set up routing (React Router): login page, app shell with sidebar/header
- [ ] **T1.13**: Create `api/client.js` — axios/fetch wrapper configured with API Gateway base URL
- [ ] **T1.14**: Create `ErrorBanner.jsx` — reusable error display component
- [ ] **T1.15**: Create `Layout.jsx` — responsive app shell (header, sidebar placeholder, content area)
- [ ] **T1.16**: Set up global error interceptor (401 → login, network error → retry)
- [ ] **T1.17**: Build and deploy front-end to S3 static website bucket
- [ ] **T1.18**: Verify front-end loads and can reach API Gateway (expect 501 responses)

## Integration Test Tasks

- [ ] **T1.19**: Set up integration test framework (e.g., pytest + requests)
- [ ] **T1.20**: Write smoke test: HTTPS call to each API Gateway stub, assert 501 response
