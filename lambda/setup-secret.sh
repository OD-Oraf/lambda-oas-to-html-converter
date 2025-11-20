#!/bin/bash
#
# Setup OAuth Credentials in AWS Secrets Manager
#

set -e

echo "════════════════════════════════════════════════════════════════════════════════"
echo "🔐 AWS Secrets Manager Setup"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""

# Check if secret already exists
echo "Checking if secret 'token_cred' exists..."
if aws secretsmanager describe-secret --secret-id token_cred &>/dev/null; then
    echo "⚠️  Secret 'token_cred' already exists!"
    echo ""
    read -p "Do you want to update it? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 0
    fi
    UPDATE_MODE=true
else
    echo "✓ Secret does not exist, will create new"
    UPDATE_MODE=false
fi

echo ""

# Get credentials from user
echo "Enter OAuth credentials:"
read -p "Client ID: " CLIENT_ID
read -s -p "Client Secret: " CLIENT_SECRET
echo ""
echo ""

# Validate input
if [ -z "$CLIENT_ID" ] || [ -z "$CLIENT_SECRET" ]; then
    echo "❌ Error: Client ID and Client Secret cannot be empty"
    exit 1
fi

# Create JSON secret
SECRET_JSON=$(cat <<EOF
{
  "client_id": "$CLIENT_ID",
  "client_secret": "$CLIENT_SECRET"
}
EOF
)

echo "Creating/Updating secret..."

if [ "$UPDATE_MODE" = true ]; then
    # Update existing secret
    aws secretsmanager update-secret \
        --secret-id token_cred \
        --secret-string "$SECRET_JSON"
    
    echo "✅ Secret 'token_cred' updated successfully!"
else
    # Create new secret
    aws secretsmanager create-secret \
        --name token_cred \
        --description "OAuth credentials for OAS API access" \
        --secret-string "$SECRET_JSON"
    
    echo "✅ Secret 'token_cred' created successfully!"
fi

echo ""
echo "Secret Name: token_cred"
echo "Region: $(aws configure get region || echo 'us-east-1')"
echo ""

# Show secret ARN
SECRET_ARN=$(aws secretsmanager describe-secret --secret-id token_cred --query ARN --output text)
echo "Secret ARN: $SECRET_ARN"
echo ""

echo "════════════════════════════════════════════════════════════════════════════════"
echo "✅ Setup Complete"
echo "════════════════════════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  1. Update Lambda execution role with Secrets Manager permission"
echo "     ./UPDATE_ROLE.sh"
echo ""
echo "  2. Deploy Lambda function"
echo "     ./deploy.sh"
echo ""
echo "  3. Test with authentication"
echo "     aws lambda invoke \\"
echo "       --function-name lambda-layers-demo \\"
echo "       --payload file://test-manual-event-with-auth.json \\"
echo "       response.json"
echo ""
