# Post-Deployment TODO

## First Deployment Steps
- [ ] Run `sam deploy --guided` to deploy the full stack
- [ ] Note the API Gateway URL from stack outputs
- [ ] Update `frontend/.env.production` with the API URL (`VITE_API_URL`)
- [ ] Rebuild frontend: `npm run build`
- [ ] Upload frontend build to S3 frontend bucket: `aws s3 sync dist/ s3://<frontend-bucket>/`
- [ ] Invoke seed Lambda to create default Admin account
- [ ] Test login with default credentials (admin / ChangeMe123!)
- [ ] Change default admin password on first login

## Post-Deploy Verification
- [ ] Check CloudWatch Logs for each Lambda function (look for errors)
- [ ] Verify S3 CORS configuration allows uploads/downloads from frontend URL
- [ ] Test file upload with pre-signed URL (check S3 bucket for object)
- [ ] Test file download with pre-signed URL
- [ ] Verify DynamoDB TTL is enabled on the table (session auto-expiry)

## Deferred Tests (Require Real AWS)
- [ ] T2.30: Session TTL auto-expiry — verify DynamoDB TTL deletes expired sessions
- [ ] T4.21: Pre-signed URL expiry — verify URLs become invalid after TTL

## CloudFront / Frontend Hosting
- [ ] Set up CloudFront distribution for the frontend S3 bucket
- [ ] Configure CloudFront to redirect all paths to index.html (SPA routing)
- [ ] Add custom domain with ACM certificate (optional)

## Production Hardening
- [ ] Enable DynamoDB TTL attribute (`ttl`) on the table
- [ ] Set CORS AllowedOrigins to actual frontend domain (replace `*`)
- [ ] Review and tighten IAM permissions for Lambda roles
- [ ] Enable CloudWatch alarms for Lambda errors and DynamoDB throttling
- [ ] Consider enabling DynamoDB point-in-time recovery
- [ ] Enable S3 versioning on the storage bucket (optional)

## Known Issues / Failed Actions
(Track any actions that failed during development and need to be retried after deployment)

