"""
Authentication Module
Handles OAuth token generation for MuleSoft Anypoint Platform

Hardcoded Configuration:
- Token URL: https://anypoint.mulesoft.com/accounts/api/v2/oauth2/token
- Secret Name: token_cred
- Secret Keys: client_id, client_secret
"""

import os
import json
import requests
from typing import Dict

# Hardcoded OAuth Configuration - These never change
TOKEN_URL = "https://anypoint.mulesoft.com/accounts/api/v2/oauth2/token"
SECRET_NAME = "token_cred"
SECRET_KEY_CLIENT_ID = "client_id"
SECRET_KEY_CLIENT_SECRET = "client_secret"


def get_credentials() -> Dict[str, str]:
    """
    Get client credentials from AWS Secrets Manager (Lambda) or environment variables (local)
    
    Returns:
        Dictionary with client_id and client_secret
    """
    # Check if running in Lambda (Secrets Manager available)
    if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
        print("🔐 Fetching credentials from Secrets Manager...")
        return _get_credentials_from_secrets_manager()
    else:
        print("🔐 Fetching credentials from environment variables...")
        return _get_credentials_from_env()


def _get_credentials_from_secrets_manager() -> Dict[str, str]:
    """
    Get credentials from AWS Secrets Manager
    
    Uses hardcoded configuration:
    - Secret Name: token_cred
    - Secret Keys: client_id, client_secret
    
    Returns:
        Dictionary with client_id and client_secret
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        region_name = os.environ.get('AWS_REGION', 'us-east-1')
        
        print(f"  📦 Retrieving secret from AWS Secrets Manager...")
        print(f"     Secret Name: {SECRET_NAME}")
        print(f"     Region: {region_name}")
        
        # Create Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        
        try:
            print(f"  🔍 Calling GetSecretValue API...")
            get_secret_value_response = client.get_secret_value(
                SecretId=SECRET_NAME
            )
            print(f"  ✓ Secret retrieved successfully from Secrets Manager")
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            print(f"  ✗ Secrets Manager API error: {error_code}")
            
            if error_code == 'ResourceNotFoundException':
                raise Exception(
                    f"Secret '{SECRET_NAME}' not found in Secrets Manager (Region: {region_name}). "
                    f"Run './setup-secret.sh' to create it."
                )
            elif error_code == 'InvalidRequestException':
                raise Exception(f"Invalid request for secret '{SECRET_NAME}'")
            elif error_code == 'InvalidParameterException':
                raise Exception(f"Invalid parameter for secret '{SECRET_NAME}'")
            elif error_code == 'AccessDeniedException':
                raise Exception(
                    f"Access denied to secret '{SECRET_NAME}'. "
                    f"Ensure Lambda execution role has 'secretsmanager:GetSecretValue' permission."
                )
            else:
                raise Exception(f"Error retrieving secret: {e}")
        
        # Parse secret
        print(f"  🔓 Parsing secret value...")
        secret = json.loads(get_secret_value_response['SecretString'])
        
        # Validate secret structure using hardcoded keys
        if SECRET_KEY_CLIENT_ID not in secret:
            raise Exception(
                f"Secret '{SECRET_NAME}' missing '{SECRET_KEY_CLIENT_ID}' key. "
                f"Expected format: {{\"{SECRET_KEY_CLIENT_ID}\": \"...\", \"{SECRET_KEY_CLIENT_SECRET}\": \"...\"}}"
            )
        if SECRET_KEY_CLIENT_SECRET not in secret:
            raise Exception(
                f"Secret '{SECRET_NAME}' missing '{SECRET_KEY_CLIENT_SECRET}' key. "
                f"Expected format: {{\"{SECRET_KEY_CLIENT_ID}\": \"...\", \"{SECRET_KEY_CLIENT_SECRET}\": \"...\"}}"
            )
        
        print(f"  ✓ Secret parsed and validated")
        print(f"     Client ID: {secret[SECRET_KEY_CLIENT_ID][:12]}... (length: {len(secret[SECRET_KEY_CLIENT_ID])})")
        print(f"     Client Secret: {'*' * 12}... (length: {len(secret[SECRET_KEY_CLIENT_SECRET])})")
        
        return {
            'client_id': secret[SECRET_KEY_CLIENT_ID],
            'client_secret': secret[SECRET_KEY_CLIENT_SECRET]
        }
        
    except Exception as e:
        print(f"  ✗ Failed to retrieve credentials from Secrets Manager: {e}")
        raise


def _get_credentials_from_env() -> Dict[str, str]:
    """
    Get credentials from environment variables (for local development)
    
    Returns:
        Dictionary with client_id and client_secret
    """
    client_id = os.environ.get('CLIENT_ID')
    client_secret = os.environ.get('CLIENT_SECRET')
    
    if not client_id or not client_secret:
        raise Exception(
            "CLIENT_ID and CLIENT_SECRET environment variables must be set.\n"
            "Set them with:\n"
            "  export CLIENT_ID='your_client_id'\n"
            "  export CLIENT_SECRET='your_client_secret'"
        )
    
    print(f"  ✓ Retrieved credentials from environment variables")
    
    return {
        'client_id': client_id,
        'client_secret': client_secret
    }


def generate_bearer_token() -> Dict[str, any]:
    """
    Generate OAuth bearer token for MuleSoft Anypoint Platform
    
    Uses hardcoded configuration:
    - Token URL: https://anypoint.mulesoft.com/accounts/api/v2/oauth2/token
    - Credentials from Secrets Manager (Lambda) or environment variables (local)
    
    Returns:
        Dictionary with:
        - success: bool
        - token: str (access token)
        - expires_in: int (token expiration in seconds)
        - error: str (if failed)
    """
    print(f"\n{'='*80}")
    print(f"🔑 OAuth Token Generation")
    print(f"{'='*80}")
    print(f"Token URL: {TOKEN_URL}")
    
    try:
        # Get credentials from storage
        print(f"\n📋 Retrieving credentials from storage...")
        creds = get_credentials()
        client_id = creds['client_id']
        client_secret = creds['client_secret']
        print(f"✓ Credentials retrieved successfully")
        
        # Request token (MuleSoft uses JSON, not form data)
        print(f"\n🌐 Requesting OAuth token from MuleSoft Anypoint...")
        print(f"   Method: POST")
        print(f"   Content-Type: application/json")
        print(f"   Grant Type: client_credentials")
        
        response = requests.post(
            TOKEN_URL,
            json={
                'grant_type': 'client_credentials',
                'client_id': client_id,
                'client_secret': client_secret
            },
            headers={
                'Content-Type': 'application/json'
            },
            timeout=10
        )
        
        print(f"   Response Status: {response.status_code}")
        
        if response.status_code != 200:
            error = f"Token request failed: {response.status_code} - {response.text}"
            print(f"\n✗ Token generation failed")
            print(f"  Error: {error}")
            print(f"{'='*80}\n")
            return {
                'success': False,
                'error': error
            }
        
        token_data = response.json()
        
        if 'access_token' not in token_data:
            error = "No access_token in response"
            print(f"\n✗ Token generation failed")
            print(f"  Error: {error}")
            print(f"{'='*80}\n")
            return {
                'success': False,
                'error': error
            }
        
        print(f"\n✅ Token generated successfully!")
        print(f"   Token Type: {token_data.get('token_type', 'Bearer')}")
        print(f"   Expires In: {token_data.get('expires_in', 'unknown')} seconds")
        print(f"   Token: {token_data['access_token'][:20]}...{token_data['access_token'][-10:]}")
        print(f"{'='*80}\n")
        
        return {
            'success': True,
            'token': token_data['access_token'],
            'expires_in': token_data.get('expires_in'),
            'token_type': token_data.get('token_type', 'Bearer')
        }
        
    except requests.exceptions.RequestException as e:
        error = f"Request failed: {str(e)}"
        print(f"\n✗ Token generation failed - Network error")
        print(f"  Error: {error}")
        print(f"{'='*80}\n")
        return {
            'success': False,
            'error': error
        }
    except Exception as e:
        error = f"Token generation failed: {str(e)}"
        print(f"\n✗ Token generation failed - Unexpected error")
        print(f"  Error: {error}")
        print(f"{'='*80}\n")
        return {
            'success': False,
            'error': error
        }


# For testing
if __name__ == '__main__':
    print("="*80)
    print("🔐 Authentication Module Test")
    print("="*80)
    print()
    
    print(f"Hardcoded Configuration:")
    print(f"  Token URL: {TOKEN_URL}")
    print(f"  Secret Name: {SECRET_NAME}")
    print(f"  Secret Keys: {SECRET_KEY_CLIENT_ID}, {SECRET_KEY_CLIENT_SECRET}")
    print()
    
    # Test credential retrieval
    try:
        creds = get_credentials()
        print(f"\n✓ Credentials retrieved:")
        print(f"  Client ID: {creds['client_id'][:10]}...")
        print(f"  Client Secret: {creds['client_secret'][:10]}...")
    except Exception as e:
        print(f"\n✗ Failed to get credentials: {e}")
        exit(1)
    
    # Test token generation (uses hardcoded config)
    print(f"\n\nTesting token generation...")
    result = generate_bearer_token()
    
    if result['success']:
        print(f"\n✓ Token generated:")
        print(f"  Token: {result['token'][:20]}...")
        print(f"  Expires in: {result['expires_in']} seconds")
    else:
        print(f"\n✗ Token generation failed: {result['error']}")
