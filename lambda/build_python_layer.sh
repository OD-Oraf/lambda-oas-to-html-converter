#!/bin/bash
#
# Build Python Lambda Layer
# Creates a Lambda layer with Python dependencies
#

set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🐍 Python Lambda Layer Builder"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Change to project root
cd "$(dirname "$0")/.."

# Clean previous builds
echo "🧹 Cleaning previous layer builds..."
rm -rf build/python-layer/
rm -f python-layer.zip
echo "  ✓ Clean complete"
echo ""

# Create layer directory structure
# Lambda layers must use python/ directory for Python packages
echo "📁 Creating layer directory structure..."
mkdir -p build/python-layer/python
echo "  ✓ Created build/python-layer/python/"
echo ""

# Install dependencies to layer directory
echo "📦 Installing Python dependencies..."
echo "  Installing requests and its dependencies..."

pip3 install \
  --target build/python-layer/python \
  --upgrade \
  requests

echo "  ✓ Dependencies installed"
echo ""

# List installed packages
echo "📋 Installed packages:"
ls -1 build/python-layer/python/ | grep -v "\.dist-info" | grep -v "__pycache__"
echo ""

# Create layer zip
echo "📦 Creating layer zip file..."
cd build/python-layer
zip -r ../../python-layer.zip python/ -q
cd ../..
echo "  ✓ Created python-layer.zip"
echo ""

# Get package size
SIZE=$(du -h python-layer.zip | cut -f1)

echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ Python Layer Complete"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Layer Package: python-layer.zip"
echo "Size: $SIZE"
echo ""
echo "Contents:"
ls -1 build/python-layer/python/ | grep -v "\.dist-info" | grep -v "__pycache__" | sed 's/^/  - /'
echo ""
echo "Next Steps:"
echo ""
echo "  1. Publish layer to AWS:"
echo "     aws lambda publish-layer-version \\"
echo "       --layer-name python-dependencies \\"
echo "       --description 'Python dependencies (requests)' \\"
echo "       --zip-file fileb://python-layer.zip \\"
echo "       --compatible-runtimes python3.11 python3.12 python3.13"
echo ""
echo "  2. Note the LayerVersionArn from the output"
echo ""
echo "  3. Attach layer to Lambda function:"
echo "     aws lambda update-function-configuration \\"
echo "       --function-name lambda-layers-demo \\"
echo "       --layers <LAYER_ARN> <NODEJS_LAYER_ARN>"
echo ""
echo "     Or attach only this layer:"
echo "     aws lambda update-function-configuration \\"
echo "       --function-name lambda-layers-demo \\"
echo "       --layers \\"
echo "         arn:aws:lambda:REGION:ACCOUNT:layer:python-dependencies:VERSION"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"


aws lambda publish-layer-version \
--layer-name python-dependencies \
--description 'Python dependencies (requests)' \
--zip-file fileb://python-layer.zip \
--compatible-runtimes python3.11 python3.12 python3.13 python3.14