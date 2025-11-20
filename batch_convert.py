#!/usr/bin/env python3
"""
Batch OAS to HTML Converter
Reads URLs from urls.txt and converts all to HTML
"""

import sys
import os
from fetcher import fetch_all_from_urls_file
from converter import convert_oas


def main():
    """Process all URLs from urls.txt"""
    urls_file = "urls.txt"
    
    if not os.path.exists(urls_file):
        print(f"❌ Error: {urls_file} not found")
        sys.exit(1)
    
    print("="*80)
    print("🔄 Batch OAS to HTML Converter")
    print("="*80)
    print()
    
    # Fetch all OAS files
    fetch_result = fetch_all_from_urls_file(urls_file)
    
    if not fetch_result['success']:
        print(f"❌ Failed to fetch URLs: {fetch_result['error']}")
        sys.exit(1)
    
    # Convert each successful fetch to HTML
    print("\n" + "="*80)
    print("🔄 Converting to HTML")
    print("="*80)
    print()
    
    # Create output directory
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"✓ Created {output_dir}/ directory\n")
    
    converted = 0
    failed = 0
    
    for i, result in enumerate(fetch_result['results'], 1):
        if not result['success']:
            print(f"[{i}/{fetch_result['total']}] Skipping {result['url']} (fetch failed)")
            failed += 1
            continue
        
        print(f"[{i}/{fetch_result['total']}] Converting {result['filename']}...")
        
        # Convert to HTML
        conv_result = convert_oas(
            result['content'],
            result['filename'],
            verbose=False
        )
        
        if conv_result['success']:
            # Save to output directory
            output_file = os.path.join(output_dir, result['filename'].replace('.yaml', '.html').replace('.json', '.html'))
            
            try:
                with open(output_file, 'w') as f:
                    f.write(conv_result['html_content'])
                
                print(f"  ✓ Saved to {output_file}")
                print(f"  Duration: {conv_result['duration']:.2f}s\n")
                converted += 1
            except Exception as e:
                print(f"  ✗ Failed to save: {e}\n")
                failed += 1
        else:
            print(f"  ✗ Conversion failed: {conv_result.get('error', 'Unknown error')}\n")
            failed += 1
    
    # Final summary
    print("="*80)
    print("✅ Batch Conversion Complete")
    print("="*80)
    print(f"Total URLs: {fetch_result['total']}")
    print(f"Fetched: {fetch_result['successful']}")
    print(f"Converted: {converted}")
    print(f"Failed: {failed}")
    print(f"Output directory: {output_dir}/")
    print("="*80)
    
    if converted > 0:
        print(f"\n✅ {converted} file(s) converted successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ No files converted")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
