"""
OAS File Fetcher
Downloads OAS files from URLs using requests library
"""

import requests
from typing import Optional, Dict


def fetch_oas_from_url(url: str, timeout: int = 30) -> Dict[str, any]:
    """
    Fetch OAS file from a URL
    
    Args:
        url: URL to fetch OAS file from
        timeout: Request timeout in seconds
    
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
        # Make request
        response = requests.get(url, timeout=timeout)
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
        import os
        
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


if __name__ == '__main__':
    # Test fetcher
    url = "https://raw.githubusercontent.com/OD-Oraf/scratch/refs/heads/master/oas-examples/3.0/json/petstore-expanded.json"
    result = fetch_oas_from_url(url)
    
    if result['success']:
        print(f"\n✅ Fetch successful!")
        print(f"Content preview: {result['content'][:100]}...")
    else:
        print(f"\n❌ Fetch failed: {result['error']}")
