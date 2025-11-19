"""
AWS Lambda Handler - Minimal Wrapper
Calls existing fetcher.py and converter.py modules
"""

import sys
import os
import json

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetcher import fetch_oas_from_url, fetch_oas_from_file
from converter import convert_oas


def lambda_handler(event, context):
    """
    AWS Lambda handler that uses our modular scripts
    
    Event structure:
    Option 1 - URL:
    {
        "url": "https://example.com/api.json"
    }
    
    Option 2 - OAS Content:
    {
        "oas_content": "openapi: 3.0.0...",
        "oas_file_name": "api.yaml"  # optional
    }
    
    Option 3 - S3:
    {
        "s3_bucket": "my-bucket",
        "s3_key": "path/to/api.json"
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": "<HTML content>",
        "headers": {"Content-Type": "text/html"}
    }
    """
    
    print("="*80)
    print("🚀 Lambda Handler Started")
    print(f"Event keys: {list(event.keys())}")
    print("="*80)
    
    try:
        # Step 1: Fetch OAS content
        print("\nStep 1: Fetching OAS content...")
        
        if 's3_bucket' in event and 's3_key' in event:
            # S3 input
            print("  Method: S3")
            fetch_result = _fetch_from_s3(event['s3_bucket'], event['s3_key'])
        elif 'url' in event:
            # URL input
            print(f"  Method: URL")
            print(f"  URL: {event['url']}")
            fetch_result = fetch_oas_from_url(event['url'])
        elif 'oas_content' in event:
            # Direct content
            print("  Method: Direct content")
            oas_content = event['oas_content']
            oas_file_name = event.get('oas_file_name', 'openapi.yaml')
            fetch_result = {
                'success': True,
                'content': oas_content,
                'filename': oas_file_name,
                'size': len(oas_content)
            }
        else:
            print("  ❌ No valid input method found")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameter: url, oas_content, or s3_bucket/s3_key'
                })
            }
        
        if not fetch_result['success']:
            print(f"  ❌ Fetch failed: {fetch_result['error']}")
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': fetch_result['error']
                })
            }
        
        print(f"  ✓ Fetched: {fetch_result['filename']} ({fetch_result['size']} bytes)")
        
        # Step 2: Convert to HTML
        print("\nStep 2: Converting to HTML...")
        
        timeout = event.get('timeout', 60)
        verbose = event.get('verbose', False)  # Less verbose in Lambda
        
        conversion_result = convert_oas(
            fetch_result['content'],
            fetch_result['filename'],
            verbose=verbose
        )
        
        if not conversion_result['success']:
            print(f"  ❌ Conversion failed: {conversion_result['error']}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': conversion_result['error']
                })
            }
        
        print(f"  ✓ Converted: {conversion_result['output_size']} bytes")
        print(f"  Duration: {conversion_result['duration']:.2f}s")
        
        # Step 3: Return HTML
        print("\nStep 3: Returning HTML...")
        print("="*80)
        print("✅ SUCCESS")
        print("="*80)
        
        return {
            'statusCode': 200,
            'body': conversion_result['html_content'],
            'headers': {
                'Content-Type': 'text/html'
            }
        }
    
    except Exception as e:
        print(f"\n❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'type': type(e).__name__
            })
        }


def _fetch_from_s3(bucket, key):
    """
    Fetch OAS file from S3
    
    Args:
        bucket: S3 bucket name
        key: S3 object key
    
    Returns:
        Dictionary with success, content, filename, error
    """
    print(f"  Bucket: {bucket}")
    print(f"  Key: {key}")
    
    try:
        import boto3
        from botocore.exceptions import ClientError
        from botocore.config import Config
        
        # Initialize S3 client with timeouts
        config = Config(
            connect_timeout=5,
            read_timeout=30,
            retries={'max_attempts': 2}
        )
        s3_client = boto3.client('s3', config=config)
        
        # Download from S3
        response = s3_client.get_object(Bucket=bucket, Key=key)
        content = response['Body'].read().decode('utf-8')
        
        # Extract filename from key
        filename = os.path.basename(key)
        
        print(f"  ✓ Downloaded from S3: {len(content)} bytes")
        
        return {
            'success': True,
            'content': content,
            'filename': filename,
            'size': len(content)
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'NoSuchKey':
            error = f'S3 object not found: s3://{bucket}/{key}'
        elif error_code == 'NoSuchBucket':
            error = f'S3 bucket not found: {bucket}'
        else:
            error = f'S3 error: {error_message}'
        
        print(f"  ❌ {error}")
        
        return {
            'success': False,
            'error': error
        }
    
    except Exception as e:
        error = f'Failed to fetch from S3: {str(e)}'
        print(f"  ❌ {error}")
        
        return {
            'success': False,
            'error': error
        }


# For local testing
if __name__ == '__main__':
    # Test event
    test_event = {
        'url': 'https://raw.githubusercontent.com/OD-Oraf/scratch/refs/heads/master/oas-examples/3.0/json/petstore-expanded.json',
        'verbose': True
    }
    
    result = lambda_handler(test_event, None)
    
    print(f"\nResult:")
    print(f"  Status Code: {result['statusCode']}")
    if result['statusCode'] == 200:
        html_length = len(result['body'])
        print(f"  HTML Length: {html_length} bytes ({html_length / 1024:.2f} KB)")
    else:
        print(f"  Error: {result['body']}")
