"""
AWS Lambda Handler - Minimal Wrapper
Calls existing fetcher.py and converter.py modules
"""

import sys
import os
import json

# Add parent directory to path to import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fetcher import fetch_oas_from_url, fetch_oas_from_file, fetch_urls_from_file, fetch_all_from_urls_file
from converter import convert_oas


def lambda_handler(event, context):
    """
    AWS Lambda handler - supports both automatic S3 triggers and manual invocation
    
    Mode 1: Automatic S3 Event Trigger (Primary)
    --------------------------------------------
    Triggered when urls.txt is uploaded/updated in S3.
    
    Event structure:
    {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "my-bucket"},
                    "object": {"key": "urls.txt"}
                }
            }
        ]
    }
    
    Mode 2: Manual Invocation (Secondary)
    -------------------------------------
    Direct Lambda invocation with bucket and file specified.
    
    Event structure:
    {
        "s3_bucket": "my-bucket",
        "urls_file": "urls.txt",  # optional, defaults to "urls.txt"
        "use_auth": true,         # optional, defaults to false (MuleSoft Anypoint)
        "verbose": true           # optional, defaults to false
    }
    
    Returns:
    {
        "statusCode": 200,
        "body": {
            "message": "Batch processing complete",
            "s3_bucket": "my-bucket",
            "total_urls": 4,
            "successful": 3,
            "failed": 1,
            "results": [...]
        }
    }
    """
    
    print("="*80)
    print("🚀 Lambda Handler Started")
    print("="*80)
    
    try:
        # Mode 1: S3 Event Notification (Automatic)
        if 'Records' in event:
            print("\n📥 S3 Event Notification (Automatic Trigger)")
            record = event['Records'][0]
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            print(f"Bucket: {bucket}")
            print(f"Key: {key}")
            
            # Verify this is a urls.txt file
            if not key.endswith('urls.txt'):
                print(f"\n⚠️  Skipping - Not a urls.txt file: {key}")
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'message': f'Skipped - only urls.txt files are processed',
                        'file': key
                    })
                }
            
            # Process the urls.txt file
            batch_event = {
                's3_bucket': bucket,
                'urls_file': key,
                'verbose': False
            }
            
            return _batch_process_from_s3(batch_event)
        
        # Mode 2: Manual Invocation
        elif 's3_bucket' in event:
            print("\n🔧 Manual Invocation")
            print(f"Bucket: {event['s3_bucket']}")
            print(f"URLs file: {event.get('urls_file', 'urls.txt')}")
            
            return _batch_process_from_s3(event)
        
        else:
            # Invalid event
            print("\n❌ Invalid event structure")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid event. Expected either S3 event or manual invocation with s3_bucket parameter.',
                    'help': {
                        'automatic': 'Upload urls.txt to S3 to trigger automatically',
                        'manual': 'Invoke with: {"s3_bucket": "my-bucket", "urls_file": "urls.txt"}'
                    }
                })
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


def _batch_process_from_s3(event):
    """
    Batch process all URLs from urls.txt in S3 bucket
    
    Args:
        event: Lambda event with s3_bucket and optional urls_file
    
    Returns:
        Lambda response with batch processing results
    """
    bucket = event['s3_bucket']
    urls_file = event.get('urls_file', 'urls.txt')
    verbose = event.get('verbose', False)
    use_auth = event.get('use_auth', False)
    
    print(f"Bucket: {bucket}")
    print(f"URLs file: {urls_file}")
    print()
    
    try:
        # Fetch URLs from S3
        s3_path = f"s3://{bucket}/{urls_file}"
        urls_result = fetch_urls_from_file(s3_path)
        
        if not urls_result['success']:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': f"Failed to read {urls_file}: {urls_result['error']}"
                })
            }
        
        urls = urls_result['urls']
        total = len(urls)
        
        print(f"Found {total} URLs to process\n")
        
        # Process each URL
        results = []
        successful = 0
        failed = 0
        
        for i, url in enumerate(urls, 1):
            print(f"[{i}/{total}] Processing: {url}")
            
            try:
                # Fetch OAS
                fetch_result = fetch_oas_from_url(url, use_auth=use_auth)
                
                if not fetch_result['success']:
                    print(f"  ✗ Fetch failed: {fetch_result['error']}\n")
                    results.append({
                        'url': url,
                        'success': False,
                        'error': fetch_result['error']
                    })
                    failed += 1
                    continue
                
                print(f"  ✓ Fetched: {fetch_result['filename']} ({fetch_result['size']} bytes)")
                
                # Convert to HTML
                conv_result = convert_oas(
                    fetch_result['content'],
                    fetch_result['filename'],
                    verbose=verbose
                )
                
                if not conv_result['success']:
                    print(f"  ✗ Conversion failed: {conv_result['error']}\n")
                    results.append({
                        'url': url,
                        'filename': fetch_result['filename'],
                        'success': False,
                        'error': conv_result['error']
                    })
                    failed += 1
                    continue
                
                print(f"  ✓ Converted: {conv_result['output_size']} bytes ({conv_result['duration']:.2f}s)")
                
                # Upload to S3
                html_filename = fetch_result['filename'].replace('.yaml', '.html').replace('.yml', '.html').replace('.json', '.html')
                s3_key = f"html/{html_filename}"
                
                upload_result = _upload_to_s3(
                    bucket,
                    s3_key,
                    conv_result['html_content']
                )
                
                if not upload_result['success']:
                    print(f"  ✗ Upload failed: {upload_result['error']}\n")
                    results.append({
                        'url': url,
                        'filename': fetch_result['filename'],
                        'success': False,
                        'error': upload_result['error']
                    })
                    failed += 1
                    continue
                
                print(f"  ✓ Uploaded to: s3://{bucket}/{s3_key}\n")
                
                results.append({
                    'url': url,
                    'filename': fetch_result['filename'],
                    'success': True,
                    's3_url': f"s3://{bucket}/{s3_key}",
                    's3_key': s3_key,
                    'html_size': conv_result['output_size'],
                    'duration': conv_result['duration']
                })
                successful += 1
                
            except Exception as e:
                print(f"  ✗ Exception: {e}\n")
                results.append({
                    'url': url,
                    'success': False,
                    'error': str(e)
                })
                failed += 1
        
        # Summary
        print("="*80)
        print("📊 Batch Processing Summary")
        print("="*80)
        print(f"Total URLs: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print("="*80)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Batch processing complete',
                's3_bucket': bucket,
                'total_urls': total,
                'successful': successful,
                'failed': failed,
                'results': results
            }),
            'headers': {
                'Content-Type': 'application/json'
            }
        }
        
    except Exception as e:
        print(f"\n❌ Batch processing exception: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': f"Batch processing failed: {str(e)}",
                'type': type(e).__name__
            })
        }


def _upload_to_s3(bucket, key, content):
    """
    Upload HTML content to S3
    
    Args:
        bucket: S3 bucket name
        key: S3 object key (e.g., "html/api.html")
        content: HTML content as string
    
    Returns:
        Dictionary with success, s3_url, error
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
        
        # Upload to S3
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=content.encode('utf-8'),
            ContentType='text/html',
            CacheControl='max-age=3600'
        )
        
        print(f"  ✓ Uploaded to S3: {len(content)} bytes")
        
        return {
            'success': True,
            's3_url': f's3://{bucket}/{key}',
            'size': len(content)
        }
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'NoSuchBucket':
            error = f'S3 bucket not found: {bucket}'
        elif error_code == 'AccessDenied':
            error = f'Access denied to S3 bucket: {bucket}'
        else:
            error = f'S3 error: {error_message}'
        
        print(f"  ❌ {error}")
        
        return {
            'success': False,
            'error': error
        }
    
    except Exception as e:
        error = f'Failed to upload to S3: {str(e)}'
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
