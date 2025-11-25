#!/usr/bin/env python3
"""
OAS to HTML Converter - GitHub Actions Script

Processes OAS files from URLs, converts to HTML, and uploads to S3.
Equivalent to the Lambda function but runs in GitHub Actions.
"""

import os
import sys
import json
from pathlib import Path

# Add parent directories to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fetcher import fetch_urls_from_file, fetch_oas_from_url
from converter import convert_oas_to_html

def setup_output_dir():
    """Create output directory for HTML files"""
    output_dir = Path("output/html")
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def upload_to_s3(file_path: str, s3_key: str, bucket: str):
    """Upload file to S3"""
    try:
        import boto3
        s3_client = boto3.client('s3')
        
        print(f"  📤 Uploading to S3...")
        print(f"     Bucket: {bucket}")
        print(f"     Key: {s3_key}")
        
        s3_client.upload_file(
            file_path,
            bucket,
            s3_key,
            ExtraArgs={'ContentType': 'text/html'}
        )
        
        print(f"  ✓ Uploaded to s3://{bucket}/{s3_key}")
        return True
    except Exception as e:
        print(f"  ✗ S3 upload failed: {e}")
        return False

def main():
    """Main processing function"""
    print("="*80)
    print("🚀 OAS to HTML Converter - GitHub Actions")
    print("="*80)
    print()
    
    # Get configuration from environment
    urls_file = os.environ.get('URLS_FILE', 'urls.txt')
    use_auth = os.environ.get('USE_AUTH', 'false').lower() == 'true'
    verbose = os.environ.get('VERBOSE', 'false').lower() == 'true'
    s3_bucket = os.environ.get('S3_BUCKET')
    
    print(f"Configuration:")
    print(f"  URLs file: {urls_file}")
    print(f"  Use auth: {use_auth}")
    print(f"  S3 bucket: {s3_bucket or 'Not configured'}")
    print(f"  Verbose: {verbose}")
    print()
    
    # Setup output directory
    output_dir = setup_output_dir()
    print(f"Output directory: {output_dir}")
    print()
    
    # Read URLs from file
    print(f"📋 Reading URLs from {urls_file}...")
    urls_result = fetch_urls_from_file(urls_file)
    
    if not urls_result['success']:
        print(f"✗ Failed to read URLs: {urls_result['error']}")
        sys.exit(1)
    
    urls = urls_result['urls']
    total = len(urls)
    
    print(f"✓ Found {total} URLs to process")
    print()
    
    # Process each URL
    results = []
    successful = 0
    failed = 0
    
    print("="*80)
    print(f"Processing {total} OAS files...")
    print("="*80)
    print()
    
    for i, url in enumerate(urls, 1):
        print(f"[{i}/{total}] Processing: {url}")
        print("-" * 80)
        
        try:
            # Fetch OAS
            fetch_result = fetch_oas_from_url(url, use_auth=use_auth)
            
            if not fetch_result['success']:
                print(f"  ✗ Fetch failed: {fetch_result['error']}")
                results.append({
                    'url': url,
                    'success': False,
                    'error': fetch_result['error']
                })
                failed += 1
                print()
                continue
            
            oas_content = fetch_result['content']
            oas_filename = fetch_result['filename']
            
            print(f"  ✓ Fetched: {oas_filename} ({fetch_result['size']} bytes)")
            
            # Convert to HTML
            print(f"  🔄 Converting to HTML...")
            convert_result = convert_oas_to_html(oas_content, oas_filename)
            
            if not convert_result['success']:
                print(f"  ✗ Conversion failed: {convert_result['error']}")
                results.append({
                    'url': url,
                    'success': False,
                    'error': convert_result['error']
                })
                failed += 1
                print()
                continue
            
            html_content = convert_result['html']
            html_filename = convert_result['filename']
            
            print(f"  ✓ Converted: {html_filename} ({len(html_content)} bytes)")
            
            # Save locally
            local_path = output_dir / html_filename
            with open(local_path, 'w') as f:
                f.write(html_content)
            
            print(f"  ✓ Saved locally: {local_path}")
            
            # Upload to S3 if configured
            s3_uploaded = False
            if s3_bucket:
                s3_key = f"html/{html_filename}"
                s3_uploaded = upload_to_s3(str(local_path), s3_key, s3_bucket)
            
            results.append({
                'url': url,
                'success': True,
                'oas_filename': oas_filename,
                'html_filename': html_filename,
                'local_path': str(local_path),
                's3_uploaded': s3_uploaded,
                's3_key': f"html/{html_filename}" if s3_uploaded else None
            })
            
            successful += 1
            print(f"  ✅ Complete")
            print()
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            if verbose:
                traceback.print_exc()
            
            results.append({
                'url': url,
                'success': False,
                'error': str(e)
            })
            failed += 1
            print()
    
    # Summary
    print("="*80)
    print("📊 Processing Summary")
    print("="*80)
    print(f"Total URLs: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(successful/total*100) if total > 0 else 0:.1f}%")
    print()
    
    # Save results to file
    results_file = Path("output/results.json")
    with open(results_file, 'w') as f:
        json.dump({
            'total': total,
            'successful': successful,
            'failed': failed,
            'results': results
        }, f, indent=2)
    
    print(f"Results saved to: {results_file}")
    print()
    
    # List generated files
    html_files = list(output_dir.glob('*.html'))
    if html_files:
        print("Generated HTML files:")
        for f in sorted(html_files):
            size = f.stat().st_size
            print(f"  - {f.name} ({size:,} bytes)")
    
    print()
    print("="*80)
    print("✅ Processing Complete")
    print("="*80)
    
    # Exit with error if any failures
    if failed > 0:
        sys.exit(1)

if __name__ == '__main__':
    main()
