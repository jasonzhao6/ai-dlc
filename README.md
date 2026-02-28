# FileShare

A web-based file-sharing system backed by S3, with role-based access control and DynamoDB for state management.

## Architecture

- **Frontend**: React (Vite) single-page app
- **Backend**: Python Lambda functions behind API Gateway (AWS SAM)
- **Database**: DynamoDB (single-table design)
- **Storage**: S3 with pre-signed URLs for upload/download

## Prerequisites

- Docker
- AWS SAM CLI (`sam`)
- AWS CLI (`aws`)
- Python 3.12
- Node.js + npm
- Python packages: `pip install bcrypt boto3`

## Running Locally

### 1. Create the Docker network (first time only)

```bash
docker network create sam-network
```

### 2. Start DynamoDB Local

```bash
docker run -d --name dynamodb-local --network sam-network -p 8000:8000 amazon/dynamodb-local
```

### 3. Build and start the backend

```bash
sam build
sam local start-api --docker-network sam-network --env-vars tests/local-env.json --warm-containers EAGER
```

### 4. Seed the admin user (in a second terminal)

```bash
python3 tests/seed_admin.py
```

### 5. Start the frontend (in a third terminal)

```bash
cd frontend
npm install   # first time only
npm run dev
```

### 6. Open the app

Go to http://localhost:5173 and log in:
- **Username:** `admin`
- **Password:** `ChangeMe123!`

## Running Tests

The e2e test suite requires DynamoDB Local running on port 8000. The script handles everything else (starting SAM API, seeding, cleanup):

```bash
bash tests/run_e2e.sh
```

This runs all 4 test suites (119 tests total):
- `test_auth_users.py` — login, logout, user CRUD, password management
- `test_folders.py` — folder CRUD, sub-folders, assignments, inheritance
- `test_files.py` — upload/download URLs, file listing, deletion, authorization
- `test_search.py` — search across folders, scoped results, partial/case-insensitive matching

## User Roles

| Role | Browse | Upload | Download | Admin |
|------|--------|--------|----------|-------|
| Admin | All folders | Yes | Yes | Yes |
| Uploader | Assigned folders | Yes | No | No |
| Reader | Assigned folders | No | Yes | No |
| Viewer | Assigned folders | No | No | No |
