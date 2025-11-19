#!/usr/bin/env python3
"""
Main OAS to HTML Converter
Orchestrates fetching OAS files and converting them to HTML
"""

import sys
import os
import argparse
from pathlib import Path
from fetcher import fetch_oas_from_url, fetch_oas_from_file
from converter import convert_oas

# Default output directory
OUTPUT_DIR = "output"


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Fetch OAS file and convert to HTML',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch from URL and convert (saves to output/ directory)
  %(prog)s --url https://example.com/api-spec.json
  
  # Fetch from local file (saves to output/ directory)
  %(prog)s --file my-api.yaml
  
  # Save HTML to specific location
  %(prog)s --url https://example.com/api-spec.json --output docs/api.html
  
  # Quiet mode
  %(prog)s --url https://example.com/api-spec.json --quiet

Note: By default, HTML files are saved to the 'output/' directory
        """
    )
    
    # Input options
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument('--url', help='URL to fetch OAS file from')
    input_group.add_argument('--file', help='Local OAS file path')
    
    # Other options
    parser.add_argument('-o', '--output', help=f'Output HTML file path (default: {OUTPUT_DIR}/<filename>.html)')
    parser.add_argument('-t', '--timeout', type=int, default=60, help='Conversion timeout in seconds (default: 60)')
    parser.add_argument('-q', '--quiet', action='store_true', help='Quiet mode (minimal output)')
    parser.add_argument('-v', '--version', action='version', version='%(prog)s 2.0.0')
    
    args = parser.parse_args()
    verbose = not args.quiet
    
    print("="*80)
    print("🚀 OAS to HTML Converter")
    print("="*80)
    print()
    
    # Step 1: Fetch OAS file
    print("Step 1: Fetching OAS file...")
    print("-" * 80)
    
    if args.url:
        result = fetch_oas_from_url(args.url)
    else:
        result = fetch_oas_from_file(args.file)
    
    if not result['success']:
        print(f"\n❌ Failed to fetch OAS file: {result['error']}")
        sys.exit(1)
    
    oas_content = result['content']
    filename = result['filename']
    
    print()
    
    # Step 2: Convert to HTML
    print("Step 2: Converting OAS to HTML...")
    print("-" * 80)
    
    conversion_result = convert_oas(oas_content, filename, verbose=verbose)
    
    if not conversion_result['success']:
        print(f"\n❌ Failed to convert: {conversion_result['error']}")
        sys.exit(1)
    
    html_content = conversion_result['html_content']
    temp_html_file = conversion_result['html_file']
    
    # Step 3: Save HTML file
    print("\nStep 3: Saving HTML file...")
    print("-" * 80)
    
    # Determine output file path
    if args.output:
        output_file = args.output
        # Create directory if path contains directories
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
            print(f"✓ Created directory: {output_dir}")
    else:
        # Create output directory if it doesn't exist
        if not os.path.exists(OUTPUT_DIR):
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            print(f"✓ Created output directory: {OUTPUT_DIR}/")
        
        # Generate output filename (replace .json/.yaml/.yml with .html)
        base_name = os.path.splitext(filename)[0]
        output_file = os.path.join(OUTPUT_DIR, f"{base_name}.html")
    
    print(f"Output: {output_file}")
    
    # Save the file
    try:
        with open(output_file, 'w') as f:
            f.write(html_content)
        print(f"✓ Saved successfully")
    except Exception as e:
        print(f"❌ Failed to save: {e}")
        print(f"HTML is available at: {temp_html_file}")
        sys.exit(1)
    
    # Success summary
    print("\n" + "="*80)
    print("✅ SUCCESS")
    print("="*80)
    print(f"OAS File: {filename}")
    print(f"HTML Output: {output_file}")
    print(f"HTML Size: {conversion_result['output_size'] / 1024:.2f} KB ({conversion_result['output_size'] / 1024 / 1024:.2f} MB)")
    print(f"Total Duration: {conversion_result['duration']:.2f}s")
    print("="*80)
    print()
    
    sys.exit(0)


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
