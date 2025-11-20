"""
OAS File Fetcher
Downloads OAS files from URLs using requests library
"""

import requests
import os
from typing import Optional, Dict, List

# Try to import auth module (optional)
try:
    from auth import generate_bearer_token
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False


def fetch_oas_from_url(
    url: str, 
    timeout: int = 30,
    use_auth: bool = False,
    token_url: Optional[str] = None
) -> Dict[str, any]:
    """
    Fetch OAS file from a URL
    
    Args:
        url: URL to fetch OAS file from
        timeout: Request timeout in seconds
        use_auth: Whether to use bearer token authentication
        token_url: OAuth token endpoint URL (required if use_auth=True)
    
    Returns:
        Dictionary with:
        - success: bool
        - content: str (OAS content)
        - filename: str (extracted from URL)
        - error: str (if failed)
    """
    print(f"📥 Fetching OAS from URL...")
    print(f"URL: {url}")
    
    try:
        headers = {}
        
        # Add authentication if requested
        if use_auth:
            if not AUTH_AVAILABLE:
                error = "Authentication requested but auth module not available"
                print(f"❌ Error: {error}")
                return {
                    'success': False,
                    'error': error
                }
            
            if not token_url:
                # Try to get token_url from environment
                token_url = os.environ.get('TOKEN_URL')
                if not token_url:
                    error = "TOKEN_URL not provided and not found in environment"
                    print(f"❌ Error: {error}")
                    return {
                        'success': False,
                        'error': error
                    }
            
            print(f"🔐 Requesting bearer token...")
            token_result = generate_bearer_token(token_url)
            
            if not token_result['success']:
                error = f"Failed to generate token: {token_result['error']}"
                print(f"❌ Error: {error}")
                return {
                    'success': False,
                    'error': error
                }
            
            headers['Authorization'] = f"Bearer {token_result['token']}"
            print(f"  ✓ Using bearer token authentication")
        
        # Make request
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()  # Raise exception for bad status codes
        
        # Get content
        content = response.text
        
        # Extract filename from URL
        filename = url.split('/')[-1]
        if not filename:
            filename = 'openapi.json'
        
        # Get content type
        content_type = response.headers.get('Content-Type', 'unknown')
        
        print(f"✓ Successfully fetched")
        print(f"  Filename: {filename}")
        print(f"  Size: {len(content)} bytes ({len(content) / 1024:.2f} KB)")
        print(f"  Content-Type: {content_type}")
        
        return {
            'success': True,
            'content': content,
            'filename': filename,
            'size': len(content),
            'content_type': content_type
        }
        
    except requests.exceptions.Timeout:
        error = f"Request timed out after {timeout} seconds"
        print(f"❌ Error: {error}")
        return {
            'success': False,
            'error': error
        }
    
    except requests.exceptions.HTTPError as e:
        error = f"HTTP error: {e.response.status_code} - {e.response.reason}"
        print(f"❌ Error: {error}")
        return {
            'success': False,
            'error': error
        }
    
    except requests.exceptions.RequestException as e:
        error = f"Request failed: {str(e)}"
        print(f"❌ Error: {error}")
        return {
            'success': False,
            'error': error
        }


def fetch_oas_from_file(filepath: str) -> Dict[str, any]:
    """
    Read OAS file from local filesystem
    
    Args:
        filepath: Path to local OAS file
    
    Returns:
        Dictionary with:
        - success: bool
        - content: str (OAS content)
        - filename: str
        - error: str (if failed)
    """
    print(f"📂 Reading OAS from file...")
    print(f"Path: {filepath}")
    
    try:
        if not os.path.exists(filepath):
            error = f"File not found: {filepath}"
            print(f"❌ Error: {error}")
            return {
                'success': False,
                'error': error
            }
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        filename = os.path.basename(filepath)
        size = os.path.getsize(filepath)
        
        print(f"✓ Successfully read")
        print(f"  Filename: {filename}")
        print(f"  Size: {size} bytes ({size / 1024:.2f} KB)")
        
        return {
            'success': True,
            'content': content,
            'filename': filename,
            'size': size
        }
        
    except Exception as e:
        error = f"Failed to read file: {str(e)}"
        print(f"❌ Error: {error}")
        return {
            'success': False,
            'error': error
        }


def fetch_urls_from_file(filepath: str = "urls.txt") -> Dict[str, any]:
    """
    Read URLs from a text file (one URL per line)
    Can read from local filesystem or S3
    
    Args:
        filepath: Path to URLs file (default: urls.txt)
                 Can be local path or S3 path (s3://bucket/key)
    
    Returns:
        Dictionary with:
        - success: bool
        - urls: List[str] (list of URLs)
        - count: int (number of URLs)
        - error: str (if failed)
    """
    print(f"📋 Reading URLs from file...")
    print(f"Path: {filepath}")
    
    try:
        # Check if it's an S3 path
        if filepath.startswith('s3://'):
            # Parse S3 path
            parts = filepath.replace('s3://', '').split('/', 1)
            bucket = parts[0]
            key = parts[1] if len(parts) > 1 else 'urls.txt'
            
            print(f"  S3 Bucket: {bucket}")
            print(f"  S3 Key: {key}")
            
            try:
                import boto3
                s3_client = boto3.client('s3')
                response = s3_client.get_object(Bucket=bucket, Key=key)
                content = response['Body'].read().decode('utf-8')
            except Exception as e:
                error = f"Failed to read from S3: {str(e)}"
                print(f"❌ Error: {error}")
                return {
                    'success': False,
                    'error': error
                }
        else:
            # Read from local file
            if not os.path.exists(filepath):
                error = f"File not found: {filepath}"
                print(f"❌ Error: {error}")
                return {
                    'success': False,
                    'error': error
                }
            
            with open(filepath, 'r') as f:
                content = f.read()
        
        # Parse URLs (one per line, skip empty lines and comments)
        urls = []
        for line in content.strip().split('\n'):
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith('#'):
                # Remove trailing dots/periods (typo fix)
                line = line.rstrip('.')
                urls.append(line)
        
        print(f"✓ Successfully read")
        print(f"  URLs found: {len(urls)}")
        
        return {
            'success': True,
            'urls': urls,
            'count': len(urls)
        }
        
    except Exception as e:
        error = f"Failed to read URLs file: {str(e)}"
        print(f"❌ Error: {error}")
        return {
            'success': False,
            'error': error
        }


def fetch_all_from_urls_file(
    urls_file: str = "urls.txt", 
    timeout: int = 30,
    use_auth: bool = False,
    token_url: Optional[str] = None
) -> Dict[str, any]:
    """
    Fetch all OAS files from URLs listed in a file
    
    Args:
        urls_file: Path to file containing URLs (one per line)
        timeout: Request timeout for each URL
        use_auth: Whether to use bearer token authentication
        token_url: OAuth token endpoint URL (required if use_auth=True)
    
    Returns:
        Dictionary with:
        - success: bool
        - results: List[Dict] (list of fetch results for each URL)
        - total: int (total URLs)
        - successful: int (number of successful fetches)
        - failed: int (number of failed fetches)
        - error: str (if reading URLs file failed)
    """
    print(f"\n{'='*80}")
    print(f"📦 Batch Fetch from URLs File")
    print(f"{'='*80}\n")
    
    # Read URLs from file
    urls_result = fetch_urls_from_file(urls_file)
    
    if not urls_result['success']:
        return {
            'success': False,
            'error': urls_result['error']
        }
    
    urls = urls_result['urls']
    total = len(urls)
    
    print(f"\nFetching {total} OAS files...\n")
    
    results = []
    successful = 0
    failed = 0
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{total}] Processing: {url}")
        
        result = fetch_oas_from_url(url, timeout=timeout, use_auth=use_auth, token_url=token_url)
        result['url'] = url  # Add URL to result
        results.append(result)
        
        if result['success']:
            successful += 1
            print(f"  ✓ Success\n")
        else:
            failed += 1
            print(f"  ✗ Failed: {result.get('error', 'Unknown error')}\n")
    
    print(f"{'='*80}")
    print(f"📊 Batch Fetch Summary")
    print(f"{'='*80}")
    print(f"Total URLs: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"{'='*80}\n")
    
    return {
        'success': True,
        'results': results,
        'total': total,
        'successful': successful,
        'failed': failed
    }


if __name__ == '__main__':
    # Test fetcher
    url = "https://raw.githubusercontent.com/OD-Oraf/scratch/refs/heads/master/oas-examples/3.0/json/petstore-expanded.json"
    result = fetch_oas_from_url(url)
    
    if result['success']:
        print(f"\n✅ Fetch successful!")
        print(f"Content preview: {result['content'][:100]}...")
    else:
        print(f"\n❌ Fetch failed: {result['error']}")
