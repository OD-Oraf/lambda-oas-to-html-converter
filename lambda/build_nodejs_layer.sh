#!/bin/bash
#
# Build Node.js Lambda Layer
# Creates a Lambda layer with Node.js and swagger-ui-offline-packager
#

set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "📦 Node.js Lambda Layer Builder"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Change to project root
cd "$(dirname "$0")/.."

# Clean previous builds
echo "🧹 Cleaning previous layer builds..."
rm -rf build/nodejs-layer/
rm -f nodejs-layer.zip
echo "  ✓ Clean complete"
echo ""

# Create layer directory structure
# Lambda layers use nodejs/ directory for Node.js packages
echo "📁 Creating layer directory structure..."
mkdir -p build/nodejs-layer/nodejs/node_modules
echo "  ✓ Created build/nodejs-layer/nodejs/"
echo ""

# Check if node and npm are available
if ! command -v node &> /dev/null; then
    echo "❌ Error: node is not installed"
    echo "   Install Node.js first: brew install node"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "❌ Error: npm is not installed"
    echo "   Install npm first (usually comes with Node.js)"
    exit 1
fi

echo "✓ Node.js version: $(node --version)"
echo "✓ npm version: $(npm --version)"
echo ""

# Install swagger-ui-offline-packager
echo "📦 Installing swagger-ui-offline-packager..."
cd build/nodejs-layer/nodejs
npm install swagger-ui-offline-packager --production
cd ../../..
echo "  ✓ Package installed"
echo ""

# List installed packages
echo "📋 Installed packages:"
ls -1 build/nodejs-layer/nodejs/node_modules/ | head -10
TOTAL=$(ls -1 build/nodejs-layer/nodejs/node_modules/ | wc -l | xargs)
echo "  ... and $(($TOTAL - 10)) more packages"
echo ""

# Create layer zip
echo "📦 Creating layer zip file..."
cd build/nodejs-layer
zip -r ../../nodejs-layer.zip nodejs/ -q
cd ../..
echo "  ✓ Created nodejs-layer.zip"
echo ""

# Get package size
SIZE=$(du -h nodejs-layer.zip | cut -f1)

echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ Node.js Layer Complete"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Layer Package: nodejs-layer.zip"
echo "Size: $SIZE"
echo ""
echo "Layer Structure:"
echo "  nodejs-layer.zip"
echo "  └── nodejs/"
echo "      └── node_modules/"
echo "          └── swagger-ui-offline-packager/"
echo ""
echo "Next Steps:"
echo ""
echo "  1. Publish layer to AWS:"
echo "     aws lambda publish-layer-version \\"
echo "       --layer-name nodejs-swagger-packager \\"
echo "       --description 'Node.js with swagger-ui-offline-packager' \\"
echo "       --zip-file fileb://nodejs-layer.zip \\"
echo "       --compatible-runtimes nodejs18.x nodejs20.x nodejs22.x"
echo ""
echo "  2. Note the LayerVersionArn from the output"
echo ""
echo "  3. Attach BOTH layers to Lambda function:"
echo "     aws lambda update-function-configuration \\"
echo "       --function-name lambda-layers-demo \\"
echo "       --layers \\"
echo "         arn:aws:lambda:REGION:ACCOUNT:layer:python-dependencies:VERSION \\"
echo "         arn:aws:lambda:REGION:ACCOUNT:layer:nodejs-swagger-packager:VERSION"
echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
