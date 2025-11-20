# S3 Event Trigger Setup

## Overview

The Lambda function is **automatically triggered** when `urls.txt` is uploaded or updated in your S3 bucket.

**Workflow:**
1. Upload/update `urls.txt` to S3 bucket
2. S3 automatically triggers Lambda
3. Lambda reads urls.txt, processes all URLs
4. Lambda uploads HTML files to `html/` folder in same bucket

---

## Setup Instructions

### Step 1: Deploy Lambda Function

```bash
cd /Users/od/Documents/lambda-layers/lambda
./deploy.sh
```

### Step 2: Add S3 Trigger Permission to Lambda

Allow S3 to invoke your Lambda function:

```bash
aws lambda add-permission \
  --function-name lambda-layers-demo \
  --statement-id s3-trigger-urls-txt \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::YOUR-BUCKET-NAME
```

**Replace `YOUR-BUCKET-NAME` with your actual bucket name.**

### Step 3: Configure S3 Event Notification

```bash
# Save bucket name
BUCKET_NAME="your-bucket-name"
LAMBDA_ARN="arn:aws:lambda:us-east-1:289491622160:function:lambda-layers-demo"

# Create notification configuration
cat > /tmp/s3-notification.json << EOF
{
  "LambdaFunctionConfigurations": [
    {
      "Id": "urls-txt-upload-trigger",
      "LambdaFunctionArn": "$LAMBDA_ARN",
      "Events": ["s3:ObjectCreated:*"],
      "Filter": {
        "Key": {
          "FilterRules": [
            {
              "Name": "suffix",
              "Value": "urls.txt"
            }
          ]
        }
      }
    }
  ]
}
EOF

# Apply configuration
aws s3api put-bucket-notification-configuration \
  --bucket $BUCKET_NAME \
  --notification-configuration file:///tmp/s3-notification.json
```

### Step 4: Test the Trigger

Upload urls.txt to S3:

```bash
aws s3 cp /Users/od/Documents/lambda-layers/urls.txt s3://your-bucket-name/urls.txt
```

This will automatically trigger the Lambda function!

---

## Verification

### Check Lambda was triggered:

```bash
aws logs tail /aws/lambda/lambda-layers-demo --follow
```

You should see:
```
================================================================================
🚀 Lambda Handler Started - S3 Event Triggered
================================================================================

📥 S3 Event Notification received
Bucket: your-bucket-name
Key: urls.txt

🔄 Batch Processing Mode
...
```

### Check HTML files were created:

```bash
aws s3 ls s3://your-bucket-name/html/
```

You should see:
```
2024-01-01 12:00:00   1500000 circular-paths.html
2024-01-01 12:00:01   1500000 circular.html
2024-01-01 12:00:02   1500000 petstore-simple-no-tags.html
2024-01-01 12:00:03   1500000 readme.html
```

---

## Event Flow

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  1. Upload urls.txt to S3                                   │
│     aws s3 cp urls.txt s3://bucket/urls.txt                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  2. S3 Event Notification                                   │
│     Automatically triggers Lambda                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  3. Lambda Handler                                          │
│     - Reads urls.txt from S3                               │
│     - Fetches each URL                                     │
│     - Converts to HTML                                     │
│     - Uploads to s3://bucket/html/                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  4. Result                                                  │
│     HTML files available at:                                │
│     s3://bucket/html/file1.html                            │
│     s3://bucket/html/file2.html                            │
│     etc.                                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Testing Without S3 Trigger

For local testing, you can manually invoke with S3 event format:

```bash
aws lambda invoke \
  --function-name lambda-layers-demo \
  --payload file://test-s3-upload-event.json \
  --cli-binary-format raw-in-base64-out \
  response.json
```

Or with simple format:

```bash
aws lambda invoke \
  --function-name lambda-layers-demo \
  --payload '{"s3_bucket":"my-bucket","urls_file":"urls.txt"}' \
  --cli-binary-format raw-in-base64-out \
  response.json
```

---

## IAM Permissions Required

### Lambda Execution Role

Your Lambda execution role needs:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::your-bucket/html/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

---

## Updating urls.txt

Every time you update urls.txt, the Lambda will automatically run:

```bash
# Edit your local urls.txt
nano /Users/od/Documents/lambda-layers/urls.txt

# Upload to S3 (triggers Lambda automatically)
aws s3 cp /Users/od/Documents/lambda-layers/urls.txt s3://your-bucket/urls.txt

# Lambda runs automatically - check logs
aws logs tail /aws/lambda/lambda-layers-demo --follow
```

---

## Troubleshooting

### Lambda not triggering?

1. **Check S3 notification is configured:**
   ```bash
   aws s3api get-bucket-notification-configuration --bucket your-bucket
   ```

2. **Check Lambda has permission:**
   ```bash
   aws lambda get-policy --function-name lambda-layers-demo
   ```

3. **Check CloudWatch logs:**
   ```bash
   aws logs tail /aws/lambda/lambda-layers-demo --follow
   ```

### Files not uploading to html/?

Check Lambda execution role has `s3:PutObject` permission for `html/*`.

### urls.txt not found?

Check the file exists in S3:
```bash
aws s3 ls s3://your-bucket/urls.txt
```

---

## Quick Setup Commands

```bash
# Set your variables
BUCKET_NAME="your-bucket-name"
LAMBDA_ARN="arn:aws:lambda:us-east-1:ACCOUNT_ID:function:lambda-layers-demo"

# 1. Add Lambda permission for S3
aws lambda add-permission \
  --function-name lambda-layers-demo \
  --statement-id s3-trigger-urls-txt \
  --action lambda:InvokeFunction \
  --principal s3.amazonaws.com \
  --source-arn arn:aws:s3:::$BUCKET_NAME

# 2. Configure S3 notification (use s3-event-config.json)
# Edit s3-event-config.json with your Lambda ARN first
aws s3api put-bucket-notification-configuration \
  --bucket $BUCKET_NAME \
  --notification-configuration file://s3-event-config.json

# 3. Upload urls.txt to trigger Lambda
aws s3 cp ../urls.txt s3://$BUCKET_NAME/urls.txt

# 4. Watch the logs
aws logs tail /aws/lambda/lambda-layers-demo --follow
```

---

## Summary

**Setup Once:**
1. ✅ Deploy Lambda function
2. ✅ Add S3 trigger permission
3. ✅ Configure S3 event notification

**Use Forever:**
- Upload/update `urls.txt` → Lambda automatically processes → HTML files created

**That's it!** No manual Lambda invocations needed.

---

**Last Updated**: 2025-11-19
