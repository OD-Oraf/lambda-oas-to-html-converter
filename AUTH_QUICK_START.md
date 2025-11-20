# Authentication Quick Start - MuleSoft Anypoint

## 🚀 Quick Setup (5 minutes)

### 1. Create Secret in AWS Secrets Manager

```bash
cd /Users/od/Documents/lambda-layers/lambda
./setup-secret.sh
```

Enter your MuleSoft Anypoint credentials when prompted:
- Client ID from your MuleSoft Connected App
- Client Secret from your MuleSoft Connected App

### 2. Update Lambda Execution Role

```bash
./UPDATE_ROLE.sh
```

This adds Secrets Manager permissions to your Lambda role.

### 3. Deploy Lambda

```bash
./deploy.sh
```

This includes the new `auth.py` module.

### 4. Test

**Without authentication:**
```bash
aws s3 cp ../urls.txt s3://your-bucket/urls.txt
```

**With authentication:**
```json
{
  "s3_bucket": "your-bucket",
  "use_auth": true
}
```

```bash
aws lambda invoke \
  --function-name lambda-layers-demo \
  --payload '{"s3_bucket":"your-bucket","use_auth":true}' \
  --cli-binary-format raw-in-base64-out \
  response.json
```

---

## 📋 MuleSoft Anypoint Details

### Token Endpoint
```
https://anypoint.mulesoft.com/accounts/api/v2/oauth2/token
```

### Request Format
```json
{
  "grant_type": "client_credentials",
  "client_id": "your_client_id",
  "client_secret": "your_client_secret"
}
```

### Example curl
```bash
curl --location 'https://anypoint.mulesoft.com/accounts/api/v2/oauth2/token' \
  --header 'Content-Type: application/json' \
  --data '{
    "grant_type": "client_credentials",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
  }'
```

### Response
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

---

## 🔐 Getting MuleSoft Credentials

### 1. Access Anypoint Platform
Go to https://anypoint.mulesoft.com

### 2. Create Connected App
- Navigate to **Access Management** > **Connected Apps**
- Click **Create App**
- Select **App acts on its own behalf (client credentials)**
- Configure scopes (e.g., "View Organization", "Exchange Viewer")
- Save

### 3. Get Credentials
- **Client ID**: Shown in app details
- **Client Secret**: Shown once when created (save it!)

---

## 💡 Usage Examples

### Lambda Event (Basic)
```json
{
  "s3_bucket": "my-bucket",
  "use_auth": true
}
```
- Reads `urls.txt` from S3
- Uses MuleSoft Anypoint authentication
- Uploads HTML to `html/` folder

### Lambda Event (Custom Token URL)
```json
{
  "s3_bucket": "my-bucket",
  "use_auth": true,
  "token_url": "https://custom-oauth.com/token"
}
```

### Local Python
```python
from fetcher import fetch_oas_from_url

# Set environment variables first:
# export CLIENT_ID="..."
# export CLIENT_SECRET="..."

result = fetch_oas_from_url(
    url="https://anypoint.mulesoft.com/exchange/api/v2/assets/org/asset/...",
    use_auth=True
)
```

---

## ✅ Checklist

- [ ] Create MuleSoft Connected App
- [ ] Get Client ID and Client Secret
- [ ] Run `./setup-secret.sh` to create AWS secret
- [ ] Run `./UPDATE_ROLE.sh` to add permissions
- [ ] Run `./deploy.sh` to deploy Lambda
- [ ] Test with `use_auth: true` in event

---

## 🐛 Common Issues

### "Secret not found"
```bash
# Check if secret exists
aws secretsmanager describe-secret --secret-id token_cred
```

### "Access Denied to Secrets Manager"
```bash
# Update Lambda role
cd /Users/od/Documents/lambda-layers/lambda
./UPDATE_ROLE.sh
```

### "Invalid credentials"
```bash
# Test credentials manually
curl --location 'https://anypoint.mulesoft.com/accounts/api/v2/oauth2/token' \
  --header 'Content-Type: application/json' \
  --data '{
    "grant_type": "client_credentials",
    "client_id": "YOUR_CLIENT_ID",
    "client_secret": "YOUR_CLIENT_SECRET"
  }'
```

---

## 📖 Full Documentation

See [AUTHENTICATION.md](AUTHENTICATION.md) for complete details.

---

## 🎯 Summary

**Default behavior:** 
- Token URL: `https://anypoint.mulesoft.com/accounts/api/v2/oauth2/token`
- Credentials: AWS Secrets Manager (`token_cred`)
- Format: JSON body (not form data)

**Enable authentication:**
```json
{"use_auth": true}
```

**That's it!** The Lambda handles everything else automatically.
