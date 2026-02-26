# Deployment Plan — S3 File-Sharing System to AWS us-west-2

## Overview

Deploy the full S3 File-Sharing System to AWS us-west-2:
- **Frontend**: React SPA hosted on a private S3 bucket served via CloudFront with Origin Access Control (OAC)
- **Backend**: SAM stack (API Gateway + Lambda + DynamoDB + S3 storage bucket)

## Deliverables

| Deliverable | Location |
|---|---|
| CloudFormation template (S3 + CloudFront) | `infra/frontend-hosting.yaml` |
| Deployed CloudFormation stack | `s3-file-share-workshop` (us-west-2) |
| Deployed SAM backend stack | `aws-workshop-aidlc` (us-west-2) |
| AWS Account | `740481921028` |
| Frontend `.env.production` | `frontend/.env.production` |
| Live React app | `https://<dist-id>.cloudfront.net/` |
| Live API | `https://<api-id>.execute-api.us-west-2.amazonaws.com/dev` |

## Clarifications (Resolved)

1. **AWS credentials**: Confirmed working. Account `740481921028`, role `mq02-scratch-1215-dev-scratch-dev`.
2. **SAM backend stage**: `dev` (confirmed).
3. **SAM backend stack name**: `aws-workshop-aidlc` (confirmed).

---

## Step 1: Prerequisites

- [x] **1.1** Verify AWS CLI credentials work for us-west-2 — Account `507800882222`, role `team-transaction-engine-dev`
- [x] **1.2** Verify SAM CLI is installed — v1.154.0

## Step 2: Create CloudFormation Template for React App Hosting (Task Step 1)

- [x] **2.1** Create `infra/frontend-hosting.yaml` with:
  - **Parameters**: `BucketPrefix` (random string, generated at deploy time)
  - **S3 Bucket**: `${BucketPrefix}-react-app-bucket-s3-file-share-workshop`
    - Private: `PublicAccessBlockConfiguration` all blocked
    - Encryption: SSE-S3
    - No static website hosting (CloudFront handles serving)
  - **CloudFront Origin Access Control (OAC)**: Type `s3`, signing behavior `always`, protocol `sigv4`
  - **CloudFront Distribution**:
    - S3 origin using OAC (not deprecated OAI)
    - `DefaultRootObject: index.html`
    - Custom error responses: 403 → `/index.html` (200), 404 → `/index.html` (200) — required for SPA client-side routing
    - `ViewerProtocolPolicy: redirect-to-https`
    - Default cache behavior with `CachingOptimized` managed policy
  - **S3 Bucket Policy**: Allow `s3:GetObject` from CloudFront distribution via `aws:SourceArn` condition
  - **Outputs**: `BucketName`, `DistributionId`, `CloudFrontURL`

## Step 3: Deploy Frontend CloudFormation Stack (Task Step 2)

- [x] **3.1** Validate the template — passed
- [x] **3.2** Generate a random prefix: `b47a7ff4`
- [x] **3.3** Deploy stack — `s3-file-share-workshop` created successfully
- [x] **3.4** Stack creation completed: `CREATE_COMPLETE`
- [x] **3.5** Stack outputs captured:
  - **BucketName**: `b47a7ff4-react-app-bucket-s3-file-share-workshop`
  - **DistributionId**: `E3K5HOLTFI84UV`
  - **CloudFrontURL**: `https://d2khmiaqum7d67.cloudfront.net`

## Step 4: Deploy SAM Backend — Server-Side Components (Task Step 3)

- [ ] **4.1** Run `sam build` from project root
- [ ] **4.2** Deploy SAM stack to us-west-2:
  ```
  sam deploy \
    --stack-name aws-workshop-aidlc \
    --region us-west-2 \
    --resolve-s3 \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides Stage=dev AWSRegionParam=us-west-2 \
    --no-confirm-changeset
  ```
- [ ] **4.3** Capture API Gateway URL from SAM stack outputs
- [ ] **4.4** Invoke seed Lambda to create default admin account:
  ```
  aws lambda invoke --function-name <seed-function-name> --region us-west-2 /tmp/seed-output.json
  ```
- [ ] **4.5** Test API health: `curl <API_URL>/auth/login`

## Step 5: Configure, Build, and Deploy React App (Task Step 3)

- [ ] **5.1** Create `frontend/.env.production` with `VITE_API_URL=<API Gateway URL from Step 4.3>`
- [ ] **5.2** Build the React app: `cd frontend && npm run build`
- [ ] **5.3** Upload build artifacts to S3:
  ```
  aws s3 sync frontend/dist/ s3://<bucket-name>/ --region us-west-2 --delete
  ```
- [ ] **5.4** Create CloudFront cache invalidation:
  ```
  aws cloudfront create-invalidation --distribution-id <dist-id> --paths "/*"
  ```
- [ ] **5.5** Verify the app loads: `curl -s -o /dev/null -w "%{http_code}" https://<cloudfront-url>/`
- [ ] **5.6** Verify the full CloudFront URL in output for manual browser testing

## Architecture Notes

- The existing SAM `template.yaml` creates its own `FrontendBucket` with public website hosting. We will **not use it** — instead, we use the new CloudFront+OAC setup which is more secure (private bucket, no public access).
- CORS in both API Gateway and Lambda responses currently use `Access-Control-Allow-Origin: *`. This works for deployment but should be tightened to the CloudFront domain for production hardening (documented in TODO.md).
- The React app serves at the root path `/` — no `basename` change is needed for BrowserRouter since CloudFront serves from the root.
- CloudFront custom error responses (403/404 → `/index.html` with HTTP 200) handle SPA client-side routing.
