#!/bin/bash
#
# Lambda Deployment Script
# Packages code for AWS Lambda deployment
#

set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "📦 Lambda Deployment Packager"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Change to project root
cd "$(dirname "$0")/.."

# Clean previous builds
echo "🧹 Cleaning previous builds..."
rm -rf build/
rm -f lambda-function.zip
echo "  ✓ Clean complete"
echo ""

# Create build directory
echo "📁 Creating build directory..."
mkdir -p build/lambda
echo "  ✓ Created build/lambda/"
echo ""

# Copy Python modules
echo "📋 Copying modules..."
cp fetcher.py build/lambda/
cp converter.py build/lambda/
cp auth.py build/lambda/
cp lambda/lambda_function.py build/lambda/
echo "  ✓ Copied fetcher.py"
echo "  ✓ Copied converter.py"
echo "  ✓ Copied auth.py"
echo "  ✓ Copied lambda_function.py"
echo ""

# Package dependencies
echo "📦 Packaging dependencies..."
if [ -d "venv/lib/python3.13/site-packages" ]; then
    cd venv/lib/python3.13/site-packages
    zip -r ../../../../build/lambda-function.zip requests/ certifi/ charset_normalizer/ idna/ urllib3/ -q
    echo "  ✓ Added requests and dependencies"
    cd ../../../../
elif [ -d "venv/lib/python3.12/site-packages" ]; then
    cd venv/lib/python3.12/site-packages
    zip -r ../../../../build/lambda-function.zip requests/ certifi/ charset_normalizer/ idna/ urllib3/ -q
    echo "  ✓ Added requests and dependencies"
    cd ../../../../
elif [ -d "venv/lib/python3.11/site-packages" ]; then
    cd venv/lib/python3.11/site-packages
    zip -r ../../../../build/lambda-function.zip requests/ certifi/ charset_normalizer/ idna/ urllib3/ -q
    echo "  ✓ Added requests and dependencies"
    cd ../../../../
else
    echo "  ⚠️  Virtual environment not found, skipping dependencies"
    echo "  Note: boto3 is already in Lambda runtime"
fi
echo ""

# Package Lambda function
echo "📦 Packaging Lambda function..."
cd build/lambda
zip -r ../../lambda-function.zip . -q
cd ../..
echo "  ✓ Created lambda-function.zip"
echo ""

# Get package size
SIZE=$(du -h lambda-function.zip | cut -f1)
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ Package Complete"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Package: lambda-function.zip"
echo "Size: $SIZE"
echo ""
echo "Contents:"
echo "  - fetcher.py (OAS fetcher module)"
echo "  - converter.py (HTML converter module)"
echo "  - lambda/lambda_function.py (Lambda handler)"
echo "  - requests/ (HTTP library)"
echo ""
echo "Next Steps:"
echo "  1. Create Lambda function (if not exists):"
echo "     aws lambda create-function \\"
echo "       --function-name oas-to-html-converter \\"
echo "       --runtime python3.11 \\"
echo "       --role YOUR_LAMBDA_ROLE_ARN \\"
echo "       --handler lambda.lambda_function.lambda_handler \\"
echo "       --zip-file fileb://lambda-function.zip \\"
echo "       --timeout 90 \\"
echo "       --memory-size 1024"
echo ""
echo "  2. Or update existing function:"
echo "     aws lambda update-function-code \\"
echo "       --function-name oas-to-html-converter \\"
echo "       --zip-file fileb://lambda-function.zip"
echo ""
echo "  3. Test the function:"
echo "     aws lambda invoke \\"
echo "       --function-name oas-to-html-converter \\"
echo "       --payload '{\"url\":\"https://example.com/api.json\"}' \\"
echo "       response.json"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"


aws lambda update-function-code \
--function-name lambda-layers-demo \
--zip-file fileb://lambda-function.zip