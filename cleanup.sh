#!/bin/bash
#
# Cleanup script for lambda-layers repository
# Removes obsolete files from old structure
#

cd "$(dirname "$0")"

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🗑️  Repository Cleanup"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "This will remove obsolete files from the old structure:"
echo "  - oas_converter.py (old monolithic version)"
echo "  - test_handler.py (old tests)"
echo "  - events/ (old test events)"
echo "  - *.html (generated output files)"
echo "  - Old documentation files"
echo ""
echo "Your new modular structure will remain intact:"
echo "  ✓ main.py, fetcher.py, converter.py"
echo "  ✓ QUICK_START.md, MODULAR_STRUCTURE.md"
echo "  ✓ nodejs/, venv/, sample-oas-files/"
echo ""
read -p "Continue with cleanup? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Starting cleanup..."
echo "────────────────────────────────────────────────────────────────────────────────"

# Remove old converter files
if [ -f "oas_converter.py" ]; then
    echo "  ✓ Removing oas_converter.py"
    rm -f oas_converter.py
fi

if [ -f "test_handler.py" ]; then
    echo "  ✓ Removing test_handler.py"
    rm -f test_handler.py
fi

if [ -d "events" ]; then
    echo "  ✓ Removing events/ directory"
    rm -rf events/
fi

# Remove generated files
if [ -f "petstore-expanded.html" ]; then
    echo "  ✓ Removing petstore-expanded.html"
    rm -f petstore-expanded.html
fi

if [ -f "simple-api-output.html" ]; then
    echo "  ✓ Removing simple-api-output.html"
    rm -f simple-api-output.html
fi

# Remove outdated documentation
if [ -f "CONVERSION_SUMMARY.md" ]; then
    echo "  ✓ Removing CONVERSION_SUMMARY.md"
    rm -f CONVERSION_SUMMARY.md
fi

if [ -f "EVENT_BASED_GUIDE.md" ]; then
    echo "  ✓ Removing EVENT_BASED_GUIDE.md"
    rm -f EVENT_BASED_GUIDE.md
fi

# Remove empty directories
if [ -d "markdown" ]; then
    echo "  ✓ Removing markdown/ directory"
    rm -rf markdown/
fi

if [ -d "__pycache__" ]; then
    echo "  ✓ Removing __pycache__/ directory"
    rm -rf __pycache__/
fi

if [ -d ".idea" ]; then
    echo "  ✓ Removing .idea/ directory"
    rm -rf .idea/
fi

echo ""
echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ Cleanup Complete!"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Remaining files:"
echo "────────────────────────────────────────────────────────────────────────────────"
ls -1 | grep -v venv | grep -v nodejs | grep -v cleanup.sh | grep -v CLEANUP_PLAN.md
echo ""
echo "Note: lambda/ and test-events/ directories were preserved."
echo "      Remove them manually if not needed for Lambda deployment."
echo ""
echo "Test your setup:"
echo "  ./venv/bin/python3 main.py --file sample-oas-files/simple-api.yaml"
echo ""
