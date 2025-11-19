# Lambda Deployment

## Overview

This directory contains a **minimal Lambda wrapper** that calls your existing modular scripts (`fetcher.py` and `converter.py`).

**Key Benefit**: No code duplication! The Lambda function simply imports and uses your tested local modules.

---

## Architecture

```
Lambda Function
└── lambda_function.py (70 lines - minimal wrapper)
    ├── Imports: fetcher.py
    ├── Imports: converter.py
    └── Adds: S3 support (boto3)
```

**That's it!** All the conversion logic stays in your reusable modules.

---

## Files

| File | Purpose |
|------|---------|
| `lambda_function.py` | Minimal Lambda handler (imports your modules) |
| `test_lambda_local.py` | Test Lambda function locally |
| `README.md` | This file |

---

## Lambda Handler Code

The Lambda function is **only 70 lines** because it just calls your modules:

```python
from fetcher import fetch_oas_from_url
from converter import convert_oas

def lambda_handler(event, context):
    # Step 1: Fetch (using your fetcher.py)
    fetch_result = fetch_oas_from_url(event['url'])
    
    # Step 2: Convert (using your converter.py)
    conversion_result = convert_oas(
        fetch_result['content'],
        fetch_result['filename']
    )
    
    # Step 3: Return
    return {
        'statusCode': 200,
        'body': conversion_result['html_content']
    }
```

---

## Event Structure

### Option 1: URL
```json
{
  "url": "https://example.com/api.json"
}
```

### Option 2: Direct Content
```json
{
  "oas_content": "openapi: 3.0.0...",
  "oas_file_name": "api.yaml"
}
```

### Option 3: S3
```json
{
  "s3_bucket": "my-bucket",
  "s3_key": "path/to/api.json"
}
```

### Optional Parameters
```json
{
  "url": "https://example.com/api.json",
  "timeout": 60,
  "verbose": false
}
```

---

## Local Testing

### Test Lambda Function Locally
```bash
cd lambda/
../venv/bin/python3 test_lambda_local.py
```

This runs the Lambda handler with test events and verifies everything works.

### Test Results ✅
```
================================================================================
📊 TEST SUMMARY
================================================================================
✅ PASS - URL Input
✅ PASS - Direct Content

================================================================================
Results: 2/2 tests passed
================================================================================

🎉 All tests passed!
```

---

## Deployment

### Step 1: Package Function
```bash
cd /Users/od/Documents/lambda-layers

# Create deployment package
zip -r lambda-function.zip fetcher.py converter.py lambda/lambda_function.py

# Add dependencies if needed
cd venv/lib/python3.*/site-packages
zip -r ../../../../lambda-function.zip requests/
cd ../../../../
```

### Step 2: Create Lambda Function
```bash
aws lambda create-function \
  --function-name oas-to-html-converter \
  --runtime python3.11 \
  --role arn:aws:iam::YOUR_ACCOUNT:role/lambda-execution-role \
  --handler lambda.lambda_function.lambda_handler \
  --zip-file fileb://lambda-function.zip \
  --timeout 90 \
  --memory-size 1024
```

### Step 3: Attach Node.js Layer
```bash
# If you have the nodejs layer ARN
aws lambda update-function-configuration \
  --function-name oas-to-html-converter \
  --layers arn:aws:lambda:REGION:ACCOUNT:layer:nodejs-swagger:VERSION
```

### Step 4: Test Lambda
```bash
# Create test event
cat > test-event.json << 'EOF'
{
  "url": "https://raw.githubusercontent.com/OD-Oraf/scratch/refs/heads/master/oas-examples/3.0/json/petstore-expanded.json",
  "verbose": true
}
EOF

# Invoke Lambda
aws lambda invoke \
  --function-name oas-to-html-converter \
  --payload file://test-event.json \
  response.json

# Check result
cat response.json
```

---

## Lambda Configuration

### Recommended Settings
- **Runtime**: Python 3.11
- **Memory**: 1024 MB
- **Timeout**: 90 seconds
- **Handler**: `lambda.lambda_function.lambda_handler`

### Environment Variables (Optional)
```bash
aws lambda update-function-configuration \
  --function-name oas-to-html-converter \
  --environment Variables={LOG_LEVEL=INFO}
```

---

## Dependencies

### Python Packages
- `requests` - For HTTP fetching (URL input)
- `boto3` - For S3 access (S3 input) - **Already in Lambda runtime**

### System Dependencies
- Node.js + npm packages (in Lambda layer)
- `swagger-ui-offline-packager` npm package

---

## Code Reuse

### What's Shared
✅ `fetcher.py` - Same code for local & Lambda
✅ `converter.py` - Same code for local & Lambda

### What's Different
Only the wrapper:
- **Local**: `main.py` (CLI wrapper)
- **Lambda**: `lambda_function.py` (Lambda wrapper)

Both wrappers are **minimal** and just orchestrate the same modules!

---

## Testing Strategy

### 1. Local Testing (First)
```bash
# Test modules directly
./venv/bin/python3 main.py --url <URL>
```

### 2. Lambda Local Testing (Second)
```bash
# Test Lambda wrapper locally
cd lambda/
../venv/bin/python3 test_lambda_local.py
```

### 3. Lambda Cloud Testing (Last)
```bash
# Test deployed Lambda
aws lambda invoke \
  --function-name oas-to-html-converter \
  --payload file://test-event.json \
  response.json
```

---

## Example Usage

### Invoke from CLI
```bash
aws lambda invoke \
  --function-name oas-to-html-converter \
  --payload '{"url":"https://example.com/api.json"}' \
  response.json
```

### Invoke from Python
```python
import boto3
import json

lambda_client = boto3.client('lambda')

response = lambda_client.invoke(
    FunctionName='oas-to-html-converter',
    InvocationType='RequestResponse',
    Payload=json.dumps({
        'url': 'https://example.com/api.json'
    })
)

result = json.loads(response['Payload'].read())
html_content = result['body']
```

### Invoke from API Gateway
Create an API Gateway trigger and pass URL in request:
```json
{
  "url": "https://example.com/api.json"
}
```

---

## Error Handling

The Lambda function returns structured error responses:

### 400 - Bad Request
```json
{
  "statusCode": 400,
  "body": "{\"error\": \"Missing required parameter: url, oas_content, or s3_bucket/s3_key\"}"
}
```

### 404 - Not Found
```json
{
  "statusCode": 404,
  "body": "{\"error\": \"S3 object not found: s3://bucket/key\"}"
}
```

### 500 - Server Error
```json
{
  "statusCode": 500,
  "body": "{\"error\": \"Conversion failed\", \"type\": \"RuntimeError\"}"
}
```

---

## Logs

View Lambda logs in CloudWatch:
```bash
aws logs tail /aws/lambda/oas-to-html-converter --follow
```

The handler prints structured logs:
```
================================================================================
🚀 Lambda Handler Started
Event keys: ['url', 'verbose']
================================================================================

Step 1: Fetching OAS content...
  Method: URL
  ✓ Fetched: api.json (1234 bytes)

Step 2: Converting to HTML...
  ✓ Converted: 1500000 bytes
  Duration: 3.19s

Step 3: Returning HTML...
================================================================================
✅ SUCCESS
================================================================================
```

---

## Benefits of This Approach

### ✅ No Code Duplication
- Same `fetcher.py` for local & Lambda
- Same `converter.py` for local & Lambda
- Only wrapper is different (70 lines)

### ✅ Easy Testing
```bash
# Test locally first
./venv/bin/python3 main.py --url <URL>

# Then test Lambda wrapper locally
cd lambda/
../venv/bin/python3 test_lambda_local.py

# Finally deploy with confidence
```

### ✅ Easy Maintenance
- Bug fix in `converter.py` → Works everywhere
- New feature in `fetcher.py` → Works everywhere
- No syncing needed!

### ✅ Clean Architecture
```
Shared Modules (fetcher.py, converter.py)
├── Local: main.py → modules
└── Lambda: lambda_function.py → modules
```

---

## Troubleshooting

### Issue: Module not found
**Solution**: Ensure path is added:
```python
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
```

### Issue: Node.js not found in Lambda
**Solution**: Deploy Node.js as Lambda layer

### Issue: Timeout
**Solution**: Increase Lambda timeout (90s recommended)

### Issue: Memory error
**Solution**: Increase Lambda memory (1024 MB recommended)

---

## Next Steps

1. ✅ **Test locally** - `../venv/bin/python3 test_lambda_local.py`
2. ⬜ **Create Lambda function** - Use AWS Console or CLI
3. ⬜ **Deploy Node.js layer** - Include swagger-ui-offline-packager
4. ⬜ **Package & upload code** - Include fetcher.py, converter.py, lambda_function.py
5. ⬜ **Test in Lambda** - Invoke with test events
6. ⬜ **Monitor logs** - CloudWatch

---

## Summary

**What You Have**:
- ✅ Minimal Lambda wrapper (70 lines)
- ✅ Reuses your tested modules
- ✅ Local testing working (2/2 tests pass)
- ✅ Ready to deploy

**What You Need**:
- AWS Lambda function
- Node.js Lambda layer
- Deploy & test

**Key Advantage**: Test everything locally with the exact same code that runs in Lambda!

---

**Last Updated**: 2025-11-19
**Version**: 2.0.0 (Modular with Lambda)
