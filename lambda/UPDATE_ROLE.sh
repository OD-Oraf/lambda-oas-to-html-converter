#!/bin/bash
#
# Update Lambda Execution Role Permissions
#

ROLE_NAME="lambda-layers-demo-role"  # Update with your role name
POLICY_NAME="lambda-s3-access"

echo "Updating Lambda execution role with S3 permissions..."

# Put the inline policy
aws iam put-role-policy \
  --role-name $ROLE_NAME \
  --policy-name $POLICY_NAME \
  --policy-document file://execution-role.json

echo "✅ Role policy updated successfully!"
echo ""
echo "Permissions granted:"
echo "  ✓ Read from s3://oo-lambda-layers-demo/*"
echo "  ✓ Write to s3://oo-lambda-layers-demo/html/*"
echo "  ✓ CloudWatch Logs"
