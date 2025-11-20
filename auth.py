"""
Authentication Module
Handles OAuth token generation for API requests
"""

import os
import json
import requests
from typing import Optional, Dict


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
    
    Returns:
        Dictionary with client_id and client_secret
    """
    try:
        import boto3
        from botocore.exceptions import ClientError
        
        secret_name = "token_cred"
        region_name = os.environ.get('AWS_REGION', 'us-east-1')
        
        # Create Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )
        
        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                raise Exception(f"Secret '{secret_name}' not found in Secrets Manager")
            elif error_code == 'InvalidRequestException':
                raise Exception(f"Invalid request for secret '{secret_name}'")
            elif error_code == 'InvalidParameterException':
                raise Exception(f"Invalid parameter for secret '{secret_name}'")
            else:
                raise Exception(f"Error retrieving secret: {e}")
        
        # Parse secret
        secret = json.loads(get_secret_value_response['SecretString'])
        
        if 'client_id' not in secret or 'client_secret' not in secret:
            raise Exception("Secret must contain 'client_id' and 'client_secret' keys")
        
        print(f"  ✓ Retrieved credentials from Secrets Manager")
        
        return {
            'client_id': secret['client_id'],
            'client_secret': secret['client_secret']
        }
        
    except Exception as e:
        print(f"  ✗ Failed to retrieve from Secrets Manager: {e}")
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


def generate_bearer_token(
    token_url: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None
) -> Dict[str, any]:
    """
    Generate OAuth bearer token for MuleSoft Anypoint Platform
    
    Args:
        token_url: OAuth token endpoint URL (defaults to MuleSoft Anypoint)
        client_id: Optional client ID (if not provided, fetched from credentials)
        client_secret: Optional client secret (if not provided, fetched from credentials)
    
    Returns:
        Dictionary with:
        - success: bool
        - token: str (access token)
        - expires_in: int (token expiration in seconds)
        - error: str (if failed)
    """
    # Default to MuleSoft Anypoint token URL
    if not token_url:
        token_url = os.environ.get('TOKEN_URL', 'https://anypoint.mulesoft.com/accounts/api/v2/oauth2/token')
    
    print(f"🔑 Generating bearer token...")
    print(f"Token URL: {token_url}")
    
    try:
        # Get credentials if not provided
        if not client_id or not client_secret:
            creds = get_credentials()
            client_id = creds['client_id']
            client_secret = creds['client_secret']
        
        # Request token (MuleSoft uses JSON, not form data)
        response = requests.post(
            token_url,
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
        
        if response.status_code != 200:
            error = f"Token request failed: {response.status_code} - {response.text}"
            print(f"  ✗ {error}")
            return {
                'success': False,
                'error': error
            }
        
        token_data = response.json()
        
        if 'access_token' not in token_data:
            error = "No access_token in response"
            print(f"  ✗ {error}")
            return {
                'success': False,
                'error': error
            }
        
        print(f"  ✓ Token generated successfully")
        print(f"  Expires in: {token_data.get('expires_in', 'unknown')} seconds")
        
        return {
            'success': True,
            'token': token_data['access_token'],
            'expires_in': token_data.get('expires_in'),
            'token_type': token_data.get('token_type', 'Bearer')
        }
        
    except requests.exceptions.RequestException as e:
        error = f"Request failed: {str(e)}"
        print(f"  ✗ {error}")
        return {
            'success': False,
            'error': error
        }
    except Exception as e:
        error = f"Token generation failed: {str(e)}"
        print(f"  ✗ {error}")
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
    
    # Test credential retrieval
    try:
        creds = get_credentials()
        print(f"\n✓ Credentials retrieved:")
        print(f"  Client ID: {creds['client_id'][:10]}...")
        print(f"  Client Secret: {creds['client_secret'][:10]}...")
    except Exception as e:
        print(f"\n✗ Failed to get credentials: {e}")
        exit(1)
    
    # Test token generation (requires token URL)
    token_url = os.environ.get('TOKEN_URL')
    if token_url:
        print(f"\n\nTesting token generation...")
        result = generate_bearer_token(token_url)
        
        if result['success']:
            print(f"\n✓ Token generated:")
            print(f"  Token: {result['token'][:20]}...")
            print(f"  Expires in: {result['expires_in']} seconds")
        else:
            print(f"\n✗ Token generation failed: {result['error']}")
    else:
        print("\n\nSkipping token generation test (TOKEN_URL not set)")
        print("Set TOKEN_URL environment variable to test token generation")
