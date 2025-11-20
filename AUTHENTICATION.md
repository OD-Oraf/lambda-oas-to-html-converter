# Authentication Setup Guide

## Overview

The OAS converter supports OAuth 2.0 bearer token authentication for fetching OAS files from protected APIs.

**Features:**
- Automatic token generation using client credentials
- Secrets Manager integration for Lambda (secure credential storage)
- Environment variables for local development
- Optional authentication (only enabled when needed)

---

## Architecture

### Lambda (Production)
```
Lambda → Secrets Manager (token_cred) → OAuth Token Endpoint → Protected API
```

### Local (Development)
```
Local Script → Environment Variables → OAuth Token Endpoint → Protected API
```

---

## Setup

### 1. Create Secret in AWS Secrets Manager

```bash
aws secretsmanager create-secret \
  --name token_cred \
  --description "OAuth credentials for OAS API" \
  --secret-string '{"client_id":"YOUR_CLIENT_ID","client_secret":"YOUR_CLIENT_SECRET"}'
```

**Secret Format:**
```json
{
  "client_id": "your_client_id_here",
  "client_secret": "your_client_secret_here"
}
```

### 2. Update Lambda Execution Role

Add Secrets Manager permission to your Lambda execution role:

```json
{
  "Sid": "AccessSecretsManager",
  "Effect": "Allow",
  "Action": [
    "secretsmanager:GetSecretValue"
  ],
  "Resource": [
    "arn:aws:secretsmanager:us-east-1:ACCOUNT_ID:secret:token_cred*"
  ]
}
```

Apply the updated role:
```bash
cd /Users/od/Documents/lambda-layers/lambda
./UPDATE_ROLE.sh
```

### 3. Deploy Updated Lambda

```bash
cd /Users/od/Documents/lambda-layers/lambda
./deploy.sh
```

---

## Usage

### Lambda Invocation with Authentication

**Manual Invocation (MuleSoft Anypoint):**
```json
{
  "s3_bucket": "my-bucket",
  "urls_file": "urls.txt",
  "use_auth": true
}
```

**Parameters:**
- `use_auth` (boolean): Enable bearer token authentication
- `token_url` (string, optional): OAuth token endpoint URL
  - Defaults to: `https://anypoint.mulesoft.com/accounts/api/v2/oauth2/token`
  - Only specify if using a different OAuth provider

**Invoke:**
```bash
aws lambda invoke \
  --function-name lambda-layers-demo \
  --payload '{"s3_bucket":"my-bucket","use_auth":true}' \
  --cli-binary-format raw-in-base64-out \
  response.json
```

**With custom token URL:**
```bash
aws lambda invoke \
  --function-name lambda-layers-demo \
  --payload '{"s3_bucket":"my-bucket","use_auth":true,"token_url":"https://custom-auth.com/token"}' \
  --cli-binary-format raw-in-base64-out \
  response.json
```

### Local Development

**Set environment variables:**
```bash
export CLIENT_ID="your_client_id"
export CLIENT_SECRET="your_client_secret"
# TOKEN_URL is optional - defaults to MuleSoft Anypoint
```

**Run with authentication (MuleSoft Anypoint - default):**
```python
from fetcher import fetch_oas_from_url

result = fetch_oas_from_url(
    url="https://anypoint.mulesoft.com/exchange/api/v2/assets/...",
    use_auth=True
)
```

**With custom token URL:**
```python
result = fetch_oas_from_url(
    url="https://api.example.com/openapi.json",
    use_auth=True,
    token_url="https://custom-auth.com/oauth/token"
)
```

**Batch processing:**
```python
from fetcher import fetch_all_from_urls_file

result = fetch_all_from_urls_file(
    urls_file="urls.txt",
    use_auth=True  # Uses MuleSoft Anypoint by default
)
```

---

## Authentication Flow

### 1. Generate Token (MuleSoft Anypoint)

```bash
POST https://anypoint.mulesoft.com/accounts/api/v2/oauth2/token
Content-Type: application/json

{
  "grant_type": "client_credentials",
  "client_id": "YOUR_CLIENT_ID",
  "client_secret": "YOUR_CLIENT_SECRET"
}
```

**Equivalent curl command:**
```bash
curl --location 'https://anypoint.mulesoft.com/accounts/api/v2/oauth2/token' \
  --header 'Content-Type: application/json' \
  --data '{
    "grant_type": "client_credentials",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
  }'
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### 2. Fetch OAS with Token

```
GET https://anypoint.mulesoft.com/exchange/api/v2/assets/...
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Testing

### Test Authentication Module

```bash
cd /Users/od/Documents/lambda-layers

# Set credentials
export CLIENT_ID="your_client_id"
export CLIENT_SECRET="your_client_secret"
# TOKEN_URL is optional - defaults to MuleSoft Anypoint

# Test auth module
./venv/bin/python3 auth.py
```

Expected output:
```
🔐 Fetching credentials from environment variables
  ✓ Retrieved credentials from environment variables

✓ Credentials retrieved:
  Client ID: abcd123...
  Client Secret: xyz789...

Testing token generation...
🔑 Generating bearer token...
Token URL: https://anypoint.mulesoft.com/accounts/api/v2/oauth2/token
  ✓ Token generated successfully
  Expires in: 3600 seconds

✓ Token generated:
  Token: eyJhbGciOiJSUzI1NiIs...
  Expires in: 3600 seconds
```

### Test Fetcher with Auth

```bash
./venv/bin/python3 << 'EOF'
from fetcher import fetch_oas_from_url

result = fetch_oas_from_url(
    url="https://anypoint.mulesoft.com/exchange/api/v2/assets/YOUR_ORG/YOUR_ASSET/...",
    use_auth=True
)

if result['success']:
    print(f"✓ Fetched: {result['filename']}")
    print(f"  Size: {result['size']} bytes")
else:
    print(f"✗ Failed: {result['error']}")
EOF
```

---

## Secrets Manager Management

### View Secret

```bash
aws secretsmanager get-secret-value \
  --secret-id token_cred \
  --query SecretString \
  --output text | jq
```

### Update Secret

```bash
aws secretsmanager update-secret \
  --secret-id token_cred \
  --secret-string '{"client_id":"NEW_ID","client_secret":"NEW_SECRET"}'
```

### Delete Secret

```bash
aws secretsmanager delete-secret \
  --secret-id token_cred \
  --recovery-window-in-days 30
```

---

## Troubleshooting

### "Secret not found"

**Problem:** Lambda can't find the secret in Secrets Manager.

**Solution:**
```bash
# Verify secret exists
aws secretsmanager describe-secret --secret-id token_cred

# Check Lambda role has permission
aws iam get-role-policy --role-name lambda-layers-demo-role --policy-name lambda-s3-access
```

### "Access Denied to Secrets Manager"

**Problem:** Lambda execution role missing Secrets Manager permission.

**Solution:**
```bash
cd /Users/od/Documents/lambda-layers/lambda
./UPDATE_ROLE.sh
```

### "Token generation failed"

**Problem:** Invalid credentials or token URL.

**Solution:**
1. Verify credentials in Secrets Manager
2. Test token endpoint manually with MuleSoft:
```bash
curl --location 'https://anypoint.mulesoft.com/accounts/api/v2/oauth2/token' \
  --header 'Content-Type: application/json' \
  --data '{
    "grant_type": "client_credentials",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
  }'
```

Expected response:
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### "Authentication requested but auth module not available"

**Problem:** `auth.py` not included in Lambda package.

**Solution:**
```bash
cd /Users/od/Documents/lambda-layers/lambda
./deploy.sh  # This now includes auth.py
```

---

## Security Best Practices

### ✅ DO:
- Store credentials in Secrets Manager (Lambda)
- Use environment variables for local development
- Rotate credentials regularly
- Use IAM roles for Lambda
- Set minimum required permissions

### ❌ DON'T:
- Hardcode credentials in code
- Commit credentials to git
- Share credentials in plain text
- Use same credentials for dev and prod
- Log full credentials or tokens

---

## Cost Considerations

**Secrets Manager:**
- $0.40 per secret per month
- $0.05 per 10,000 API calls

**Typical usage:** 
- 1 secret = $0.40/month
- 10,000 Lambda invocations = $0.05
- **Total: ~$0.45/month** for authentication

---

## Files

| File | Purpose |
|------|---------|
| `auth.py` | Authentication module with token generation |
| `fetcher.py` | Updated with auth support |
| `lambda/lambda_function.py` | Updated Lambda handler with auth |
| `lambda/execution-role.json` | IAM policy with Secrets Manager access |
| `lambda/deploy.sh` | Updated to include auth.py |

---

## Summary

**Setup once:**
1. Create secret in Secrets Manager
2. Update Lambda execution role
3. Deploy Lambda

**Use authentication:**
- Set `use_auth: true` in Lambda event
- Provide `token_url` parameter
- Lambda automatically fetches credentials and generates tokens

**No authentication:**
- Omit `use_auth` or set to `false`
- Works exactly as before (public URLs)

**Best for:**
- Protected/internal APIs
- APIs requiring OAuth 2.0
- Enterprise environments
- Secure credential management
