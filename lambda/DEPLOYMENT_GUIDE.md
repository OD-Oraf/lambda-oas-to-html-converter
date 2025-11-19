# Lambda Deployment Guide

Complete guide for deploying OAS converter to AWS Lambda with layers.

---

## Overview

Your Lambda deployment consists of:
1. **Python Layer** - Python dependencies (requests)
2. **Node.js Layer** - Node.js + swagger-ui-offline-packager
3. **Lambda Function** - Your code (fetcher.py, converter.py, lambda_function.py)

---

## Prerequisites

- AWS CLI configured with credentials
- AWS account with Lambda permissions
- Lambda execution role ARN

---

## Step 1: Build Python Layer

### Build the layer
```bash
cd lambda/
chmod +x build_python_layer.sh
./build_python_layer.sh
```

### What this creates
- `python-layer.zip` (~500 KB)
- Contains: requests, certifi, charset_normalizer, idna, urllib3

---

## Step 2: Publish Python Layer to AWS

### Publish the layer
```bash
aws lambda publish-layer-version \
  --layer-name python-dependencies \
  --description "Python dependencies (requests) for OAS converter" \
  --zip-file fileb://python-layer.zip \
  --compatible-runtimes python3.11 python3.12 python3.13
```

### Expected output
```json
{
    "LayerArn": "arn:aws:lambda:us-east-1:123456789012:layer:python-dependencies",
    "LayerVersionArn": "arn:aws:lambda:us-east-1:123456789012:layer:python-dependencies:1",
    "Version": 1,
    "CompatibleRuntimes": ["python3.11", "python3.12", "python3.13"]
}
```

### Save the LayerVersionArn
```bash
# Example:
PYTHON_LAYER_ARN="arn:aws:lambda:us-east-1:123456789012:layer:python-dependencies:1"
```

---

## Step 3: Build Node.js Layer (If Needed)

### Option A: If you have nodejs-layer.zip already
```bash
# Check if you have it
ls -lh nodejs-layer.zip
```

### Option B: Build Node.js layer
```bash
# Create layer structure
mkdir -p build/nodejs-layer/nodejs/node_modules
cd build/nodejs-layer/nodejs

# Install swagger-ui-offline-packager
npm install swagger-ui-offline-packager

# Package layer
cd ..
zip -r ../../../nodejs-layer.zip nodejs/ -q
cd ../../..
```

---

## Step 4: Publish Node.js Layer to AWS

### Publish the layer
```bash
aws lambda publish-layer-version \
  --layer-name nodejs-swagger-packager \
  --description "Node.js with swagger-ui-offline-packager" \
  --zip-file fileb://nodejs-layer.zip \
  --compatible-runtimes nodejs18.x nodejs20.x
```

### Save the LayerVersionArn
```bash
# Example:
NODEJS_LAYER_ARN="arn:aws:lambda:us-east-1:123456789012:layer:nodejs-swagger-packager:1"
```

---

## Step 5: Build Lambda Function

### Build the function package
```bash
cd lambda/
./deploy.sh
```

### What this creates
- `lambda-function.zip` (~500 KB)
- Contains: fetcher.py, converter.py, lambda_function.py

---

## Step 6: Update Lambda Function

### Update function code
```bash
aws lambda update-function-code \
  --function-name lambda-layers-demo \
  --zip-file fileb://lambda-function.zip
```

---

## Step 7: Attach Layers to Lambda Function

### Attach both layers
```bash
aws lambda update-function-configuration \
  --function-name lambda-layers-demo \
  --layers \
    arn:aws:lambda:REGION:ACCOUNT:layer:python-dependencies:1 \
    arn:aws:lambda:REGION:ACCOUNT:layer:nodejs-swagger-packager:1
```

### Replace with your actual ARNs
```bash
# Example (replace with your actual values):
aws lambda update-function-configuration \
  --function-name lambda-layers-demo \
  --layers \
    arn:aws:lambda:us-east-1:123456789012:layer:python-dependencies:1 \
    arn:aws:lambda:us-east-1:123456789012:layer:nodejs-swagger-packager:1
```

---

## Step 8: Configure Lambda Settings

### Set timeout and memory
```bash
aws lambda update-function-configuration \
  --function-name lambda-layers-demo \
  --timeout 90 \
  --memory-size 1024
```

### Set handler (if needed)
```bash
aws lambda update-function-configuration \
  --function-name lambda-layers-demo \
  --handler lambda.lambda_function.lambda_handler
```

---

## Step 9: Test Lambda Function

### Create test event
```bash
cat > test-event.json << 'EOF'
{
  "url": "https://raw.githubusercontent.com/OD-Oraf/scratch/refs/heads/master/oas-examples/3.0/json/petstore-expanded.json",
  "verbose": true
}
EOF
```

### Invoke Lambda
```bash
aws lambda invoke \
  --function-name lambda-layers-demo \
  --payload file://test-event.json \
  --cli-binary-format raw-in-base64-out \
  response.json
```

### Check response
```bash
cat response.json | jq
```

### View logs
```bash
aws logs tail /aws/lambda/lambda-layers-demo --follow
```

---

## Complete Deployment Script

Save this as `full-deploy.sh`:

```bash
#!/bin/bash
set -e

# Variables (UPDATE THESE!)
FUNCTION_NAME="lambda-layers-demo"
REGION="us-east-1"
ACCOUNT_ID="123456789012"  # Replace with your AWS account ID

echo "🚀 Full Lambda Deployment"
echo ""

# Build Python layer
echo "Step 1: Building Python layer..."
./build_python_layer.sh

# Publish Python layer
echo ""
echo "Step 2: Publishing Python layer..."
PYTHON_LAYER_RESPONSE=$(aws lambda publish-layer-version \
  --layer-name python-dependencies \
  --description "Python dependencies for OAS converter" \
  --zip-file fileb://python-layer.zip \
  --compatible-runtimes python3.11 python3.12 python3.13 \
  --output json)

PYTHON_LAYER_ARN=$(echo $PYTHON_LAYER_RESPONSE | jq -r '.LayerVersionArn')
echo "  Python Layer ARN: $PYTHON_LAYER_ARN"

# Publish Node.js layer (if exists)
if [ -f "nodejs-layer.zip" ]; then
    echo ""
    echo "Step 3: Publishing Node.js layer..."
    NODEJS_LAYER_RESPONSE=$(aws lambda publish-layer-version \
      --layer-name nodejs-swagger-packager \
      --description "Node.js with swagger-ui-offline-packager" \
      --zip-file fileb://nodejs-layer.zip \
      --compatible-runtimes nodejs18.x nodejs20.x \
      --output json)
    
    NODEJS_LAYER_ARN=$(echo $NODEJS_LAYER_RESPONSE | jq -r '.LayerVersionArn')
    echo "  Node.js Layer ARN: $NODEJS_LAYER_ARN"
fi

# Build function
echo ""
echo "Step 4: Building Lambda function..."
./deploy.sh

# Update function code
echo ""
echo "Step 5: Updating Lambda function code..."
aws lambda update-function-code \
  --function-name $FUNCTION_NAME \
  --zip-file fileb://lambda-function.zip

# Attach layers
echo ""
echo "Step 6: Attaching layers to Lambda..."
if [ -n "$NODEJS_LAYER_ARN" ]; then
    aws lambda update-function-configuration \
      --function-name $FUNCTION_NAME \
      --layers $PYTHON_LAYER_ARN $NODEJS_LAYER_ARN
else
    aws lambda update-function-configuration \
      --function-name $FUNCTION_NAME \
      --layers $PYTHON_LAYER_ARN
fi

# Configure Lambda
echo ""
echo "Step 7: Configuring Lambda settings..."
aws lambda update-function-configuration \
  --function-name $FUNCTION_NAME \
  --timeout 90 \
  --memory-size 1024

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Test with:"
echo "  aws lambda invoke \\"
echo "    --function-name $FUNCTION_NAME \\"
echo "    --payload file://test-event.json \\"
echo "    response.json"
```

---

## Quick Reference Commands

### List all layers
```bash
aws lambda list-layers
```

### List layer versions
```bash
aws lambda list-layer-versions --layer-name python-dependencies
```

### Get function configuration
```bash
aws lambda get-function-configuration --function-name lambda-layers-demo
```

### Delete layer version
```bash
aws lambda delete-layer-version \
  --layer-name python-dependencies \
  --version-number 1
```

### View function logs
```bash
aws logs tail /aws/lambda/lambda-layers-demo --follow
```

---

## Layer Structure

### Python Layer
```
python-layer.zip
└── python/
    ├── requests/
    ├── certifi/
    ├── charset_normalizer/
    ├── idna/
    └── urllib3/
```

Lambda automatically adds `/opt/python` to Python path.

### Node.js Layer
```
nodejs-layer.zip
└── nodejs/
    └── node_modules/
        └── swagger-ui-offline-packager/
```

Lambda automatically adds `/opt/nodejs/node_modules` to NODE_PATH.

---

## Troubleshooting

### Issue: "Module not found: requests"
**Solution**: Ensure Python layer is attached and published correctly
```bash
# Check layers
aws lambda get-function-configuration \
  --function-name lambda-layers-demo \
  --query 'Layers[*].Arn'
```

### Issue: "Node.js not found"
**Solution**: Ensure Node.js layer is attached
```bash
# Verify layers are attached
aws lambda get-function-configuration \
  --function-name lambda-layers-demo
```

### Issue: "Function timed out"
**Solution**: Increase timeout
```bash
aws lambda update-function-configuration \
  --function-name lambda-layers-demo \
  --timeout 120
```

### Issue: "Memory limit exceeded"
**Solution**: Increase memory
```bash
aws lambda update-function-configuration \
  --function-name lambda-layers-demo \
  --memory-size 2048
```

---

## Best Practices

### Layer Versioning
- Keep track of layer versions
- Use descriptive names
- Document what's in each version

### Layer Size
- Python layer: ~500 KB (lightweight)
- Node.js layer: ~50-60 MB (larger due to npm packages)
- Combined: Under Lambda's 250 MB limit ✅

### Updates
When updating dependencies:
1. Build new layer
2. Publish new version
3. Update function to use new version
4. Test thoroughly
5. Delete old versions (optional)

---

## Example: Complete Fresh Deployment

```bash
# 1. Build layers
cd lambda/
./build_python_layer.sh

# 2. Publish Python layer
aws lambda publish-layer-version \
  --layer-name python-dependencies \
  --zip-file fileb://python-layer.zip \
  --compatible-runtimes python3.11

# Save the ARN from output
# Example: arn:aws:lambda:us-east-1:123456789012:layer:python-dependencies:1

# 3. Publish Node.js layer (if you have nodejs-layer.zip)
aws lambda publish-layer-version \
  --layer-name nodejs-swagger-packager \
  --zip-file fileb://nodejs-layer.zip \
  --compatible-runtimes nodejs18.x

# Save the ARN from output

# 4. Build and deploy function
./deploy.sh

# 5. Attach layers (replace ARNs with your actual values)
aws lambda update-function-configuration \
  --function-name lambda-layers-demo \
  --layers \
    arn:aws:lambda:us-east-1:123456789012:layer:python-dependencies:1 \
    arn:aws:lambda:us-east-1:123456789012:layer:nodejs-swagger-packager:1

# 6. Configure settings
aws lambda update-function-configuration \
  --function-name lambda-layers-demo \
  --timeout 90 \
  --memory-size 1024

# 7. Test
aws lambda invoke \
  --function-name lambda-layers-demo \
  --payload '{"url":"https://raw.githubusercontent.com/OD-Oraf/scratch/refs/heads/master/oas-examples/3.0/json/petstore-expanded.json"}' \
  response.json

# 8. Check result
cat response.json
```

---

## Summary

**What You Need to Deploy**:
1. ✅ Python layer (requests) - `./build_python_layer.sh`
2. ✅ Node.js layer (swagger-ui) - Already have or build
3. ✅ Lambda function code - `./deploy.sh`

**Publish to AWS**:
1. Publish Python layer → Get ARN
2. Publish Node.js layer → Get ARN
3. Update Lambda function code
4. Attach both layers to function
5. Configure timeout/memory
6. Test!

---

**Last Updated**: 2025-11-19
