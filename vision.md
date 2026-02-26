# S3 File-Sharing System

## Vision

A web based file sharing system backed by S3.

## Problem

File sharing using S3 is a difficult process because it requires AWS account access which can be hard to manage when working with 3rd parties.

## Solution

A web-based file-sharing system with S3 as the file storage, DynamoDB for session management, user management, and folder structure.

## Technical Architecture

- Amazon DynamoDB for the database
-- make sure to remember that the Decimal type returned from DynamoDB isn't JSON serializable
- Amazon S3 for file storage
- Amazon API Gateway and Python Lambda functions for back-end functionality
- React JS based static site hosted in S3 for the front-end

### State Management

Use DynamoDB for state and session management

## Users & Roles

- personas to include: admin persona, uploader persona, viewer persona, reader persona
- User accounts should be managed within the system with a single admin account created as part of the initial build
- Admin persona has access to everything including creating new users and folders
- Uploader persona can only view and upload to specific folders that are designated during user creation or updating by the admin
- Reader persona can only view and download objects in folders they're assigned to but not upload new ones
- Viewer persona can only view objects in folders they're assigned to but not download or upload

## Usability requirements

- Need the ability for everyone browsing files to be able to search by name and sort the view by alphabetical order for the object names, date uploaded, and size of the object.
- Keep file sizes to a maximum of 1GB and allow upload and download through S3 pre-signed URLs
- All server side functionality except the upload through pre-signed URLs should be done through API Gateway and Lambda functions written in Python

## Backend requirements

- Every lambda function linked to an API Gateway method should be tested before it's considered complete. The test should be an HTTPS call to that method and confirmation of the correct response
- Consolidate all CRUD operations into one Lambda function when applicable, not one CRUD operation per Lambda file
- For Python development and AWS SAM, use the same python version that's installed locally, DO NOT use containers

## Out of Scope

- AWS Cognito or other vendor user management like Okta

## Success Criteria

- Upload and browse files uploaded by other users
- Admin account should be able to create users, folders, and assignments between them