#!/bin/bash
#
# Quick Commands for Lambda Deployment
# Copy and paste these commands to deploy to AWS
#

# ════════════════════════════════════════════════════════════════════════════════
# STEP 1: Build Python Layer
# ════════════════════════════════════════════════════════════════════════════════

./build_python_layer.sh


# ════════════════════════════════════════════════════════════════════════════════
# STEP 2: Publish Python Layer to AWS
# ════════════════════════════════════════════════════════════════════════════════

aws lambda publish-layer-version \
  --layer-name python-dependencies \
  --description "Python dependencies (requests) for OAS converter" \
  --zip-file fileb://python-layer.zip \
  --compatible-runtimes python3.11 python3.12 python3.13

# ⚠️  IMPORTANT: Save the "LayerVersionArn" from the output above!
# Example: arn:aws:lambda:us-east-1:123456789012:layer:python-dependencies:1


# ════════════════════════════════════════════════════════════════════════════════
# STEP 3: Publish Node.js Layer (if you have nodejs-layer.zip)
# ════════════════════════════════════════════════════════════════════════════════

# Check if you have the Node.js layer
ls -lh ../nodejs-layer.zip

# If you have it, publish:
aws lambda publish-layer-version \
  --layer-name nodejs-swagger-packager \
  --description "Node.js with swagger-ui-offline-packager" \
  --zip-file fileb://../nodejs-layer.zip \
  --compatible-runtimes nodejs18.x nodejs20.x

# ⚠️  IMPORTANT: Save the "LayerVersionArn" from the output above!
# Example: arn:aws:lambda:us-east-1:123456789012:layer:nodejs-swagger-packager:1


# ════════════════════════════════════════════════════════════════════════════════
# STEP 4: Build and Deploy Lambda Function
# ════════════════════════════════════════════════════════════════════════════════

./deploy.sh

# This will automatically run:
# aws lambda update-function-code \
#   --function-name lambda-layers-demo \
#   --zip-file fileb://lambda-function.zip


# ════════════════════════════════════════════════════════════════════════════════
# STEP 5: Attach Layers to Lambda Function
# ════════════════════════════════════════════════════════════════════════════════

# ⚠️  REPLACE THE ARNS BELOW WITH YOUR ACTUAL LAYER ARNs FROM STEPS 2 & 3!

# If you have BOTH Python and Node.js layers:
aws lambda update-function-configuration \
  --function-name lambda-layers-demo \
  --layers \
    arn:aws:lambda:REGION:ACCOUNT:layer:python-dependencies:VERSION \
    arn:aws:lambda:REGION:ACCOUNT:layer:nodejs-swagger-packager:VERSION

# If you have ONLY Python layer (Node.js from existing layer):
# aws lambda update-function-configuration \
#   --function-name lambda-layers-demo \
#   --layers \
#     arn:aws:lambda:REGION:ACCOUNT:layer:python-dependencies:VERSION \
#     arn:aws:lambda:REGION:ACCOUNT:layer:existing-nodejs-layer:VERSION


# ════════════════════════════════════════════════════════════════════════════════
# STEP 6: Configure Lambda Settings
# ════════════════════════════════════════════════════════════════════════════════

aws lambda update-function-configuration \
  --function-name lambda-layers-demo \
  --timeout 90 \
  --memory-size 1024


# ════════════════════════════════════════════════════════════════════════════════
# STEP 7: Test Lambda Function
# ════════════════════════════════════════════════════════════════════════════════

# Create test event
cat > test-event.json << 'EOF'
{
  "url": "https://raw.githubusercontent.com/OD-Oraf/scratch/refs/heads/master/oas-examples/3.0/json/petstore-expanded.json",
  "verbose": true
}
EOF

# Invoke Lambda
aws lambda invoke \
  --function-name lambda-layers-demo \
  --payload file://test-event.json \
  --cli-binary-format raw-in-base64-out \
  response.json

# Check response
cat response.json | head -c 500
echo ""
echo "..."


# ════════════════════════════════════════════════════════════════════════════════
# STEP 8: View Logs
# ════════════════════════════════════════════════════════════════════════════════

aws logs tail /aws/lambda/lambda-layers-demo --follow


# ════════════════════════════════════════════════════════════════════════════════
# VERIFICATION COMMANDS
# ════════════════════════════════════════════════════════════════════════════════

# Check Lambda configuration
aws lambda get-function-configuration \
  --function-name lambda-layers-demo \
  --query '{Handler:Handler,Runtime:Runtime,Timeout:Timeout,MemorySize:MemorySize,Layers:Layers[*].Arn}'

# List all your layers
aws lambda list-layers

# List versions of a specific layer
aws lambda list-layer-versions --layer-name python-dependencies
