# Modular Structure Documentation

## Overview

The OAS to HTML converter has been restructured into **three simple, focused modules**:

```
main.py         ← Orchestrator (entry point)
├── fetcher.py  ← Fetch OAS files (from URL or filesystem)
└── converter.py ← Convert OAS to HTML
```

---

## Architecture

### 1. **main.py** - Orchestrator
**Purpose**: Entry point that coordinates fetching and converting

**Flow**:
```
User Input → Fetch OAS → Convert to HTML → Save Output
```

**Responsibilities**:
- Parse command-line arguments
- Call fetcher to get OAS content
- Call converter to generate HTML
- Save output file
- Display results

### 2. **fetcher.py** - OAS Fetcher
**Purpose**: Download OAS files from URLs or read from filesystem

**Functions**:
- `fetch_oas_from_url(url)` - Fetch from HTTP/HTTPS
- `fetch_oas_from_file(filepath)` - Read from local file

**Returns**:
```python
{
    'success': True/False,
    'content': 'OAS content as string',
    'filename': 'extracted filename',
    'size': 1234,
    'error': 'error message if failed'
}
```

### 3. **converter.py** - HTML Converter
**Purpose**: Convert OAS content to HTML using swagger-ui-offline-packager

**Functions**:
- `convert_oas(oas_content, filename)` - Main conversion function
- `OASConverter` class - Manages Node.js environment and conversion

**Returns**:
```python
{
    'success': True/False,
    'html_content': 'HTML as string',
    'html_file': '/tmp/output.html',
    'output_size': 1234567,
    'duration': 3.17,
    'error': 'error message if failed'
}
```

---

## Usage

### Basic Usage (saves to output/ directory)
```bash
# Fetch from URL and convert
./venv/bin/python3 main.py --url https://example.com/api-spec.json
# Creates: output/api-spec.html

# Or with the URL from your example
./venv/bin/python3 main.py --url https://raw.githubusercontent.com/OD-Oraf/scratch/refs/heads/master/oas-examples/3.0/json/petstore-expanded.json
# Creates: output/petstore-expanded.html
```

### With Custom Output Location
```bash
./venv/bin/python3 main.py \
  --url https://example.com/api.json \
  --output docs/api-documentation.html
# Creates: docs/api-documentation.html (directory auto-created)
```

### From Local File
```bash
./venv/bin/python3 main.py --file sample-oas-files/simple-api.yaml
# Creates: output/simple-api.html
```

### Quiet Mode
```bash
./venv/bin/python3 main.py --url https://example.com/api.json --quiet
```

---

## Module Details

### fetcher.py

#### fetch_oas_from_url(url, timeout=30)
Fetches OAS file from a URL using the `requests` library.

**Parameters**:
- `url` (str): URL to fetch
- `timeout` (int): Request timeout in seconds

**Example**:
```python
from fetcher import fetch_oas_from_url

result = fetch_oas_from_url(
    "https://raw.githubusercontent.com/OD-Oraf/scratch/refs/heads/master/oas-examples/3.0/json/petstore-expanded.json"
)

if result['success']:
    print(f"Fetched: {result['filename']}")
    print(f"Size: {result['size']} bytes")
    oas_content = result['content']
```

#### fetch_oas_from_file(filepath)
Reads OAS file from local filesystem.

**Example**:
```python
from fetcher import fetch_oas_from_file

result = fetch_oas_from_file("my-api.yaml")

if result['success']:
    oas_content = result['content']
```

---

### converter.py

#### convert_oas(oas_content, filename, verbose=True)
Converts OAS content to HTML.

**Parameters**:
- `oas_content` (str): OAS specification as string (JSON or YAML)
- `filename` (str): Name for the OAS file (used for temp file)
- `verbose` (bool): Enable detailed logging

**Example**:
```python
from converter import convert_oas

result = convert_oas(
    oas_content="openapi: 3.0.0\n...",
    filename="api.yaml",
    verbose=True
)

if result['success']:
    print(f"Duration: {result['duration']:.2f}s")
    html = result['html_content']
    
    # Save HTML
    with open('output.html', 'w') as f:
        f.write(html)
```

#### OASConverter Class
For more control over the conversion process.

**Example**:
```python
from converter import OASConverter

converter = OASConverter(verbose=True)
result = converter.convert(
    oas_content="...",
    filename="api.json",
    timeout=60
)
```

---

## Complete Example

### Custom Script Using Modules

```python
#!/usr/bin/env python3
"""
Custom OAS processor
"""

from fetcher import fetch_oas_from_url
from converter import convert_oas

# URLs to process
urls = [
    "https://example.com/api1.json",
    "https://example.com/api2.yaml",
]

for url in urls:
    print(f"Processing: {url}")
    
    # Fetch
    fetch_result = fetch_oas_from_url(url)
    if not fetch_result['success']:
        print(f"  ✗ Fetch failed: {fetch_result['error']}")
        continue
    
    # Convert
    conv_result = convert_oas(
        fetch_result['content'],
        fetch_result['filename'],
        verbose=False
    )
    
    if not conv_result['success']:
        print(f"  ✗ Conversion failed: {conv_result['error']}")
        continue
    
    # Save
    output = f"docs/{fetch_result['filename'].replace('.json', '.html')}"
    with open(output, 'w') as f:
        f.write(conv_result['html_content'])
    
    print(f"  ✓ Saved to {output}")
```

---

## Benefits of Modular Structure

### 1. **Clear Separation of Concerns**
- `fetcher.py` - Only handles fetching
- `converter.py` - Only handles conversion
- `main.py` - Only orchestrates

### 2. **Easy to Test**
```python
# Test fetcher independently
from fetcher import fetch_oas_from_url
result = fetch_oas_from_url("...")

# Test converter independently
from converter import convert_oas
result = convert_oas("openapi: 3.0.0\n...")
```

### 3. **Reusable Components**
```python
# Use fetcher in other scripts
from fetcher import fetch_oas_from_url

# Use converter with different sources
from converter import convert_oas
```

### 4. **Easy to Extend**
Want to add S3 fetcher?
```python
# fetcher.py
def fetch_oas_from_s3(bucket, key):
    # Implementation
    pass
```

Want to add different output formats?
```python
# converter.py
def convert_to_pdf(oas_content):
    # Implementation
    pass
```

---

## Testing Each Module

### Test Fetcher
```bash
./venv/bin/python3 fetcher.py
```

This will test fetching the petstore example.

### Test Converter
```bash
./venv/bin/python3 converter.py
```

This will test converting a minimal OAS spec.

### Test Main
```bash
./venv/bin/python3 main.py --url https://raw.githubusercontent.com/OD-Oraf/scratch/refs/heads/master/oas-examples/3.0/json/petstore-expanded.json
```

---

## File Structure

```
lambda-layers/
├── main.py              ← Orchestrator (entry point)
├── fetcher.py           ← Fetch OAS files
├── converter.py         ← Convert to HTML
├── output/              ← Generated HTML files (auto-created)
├── nodejs/              ← Node.js and npm packages
│   └── node_modules/
│       └── swagger-ui-offline-packager/
├── sample-oas-files/    ← Sample OAS files
└── venv/                ← Python virtual environment
```

---

## Command-Line Reference

```bash
# Basic usage
./venv/bin/python3 main.py --url <URL>
./venv/bin/python3 main.py --file <PATH>

# With options
./venv/bin/python3 main.py --url <URL> --output <FILE>
./venv/bin/python3 main.py --url <URL> --timeout 120
./venv/bin/python3 main.py --url <URL> --quiet

# Help
./venv/bin/python3 main.py --help
```

---

## Error Handling

All modules return structured results with `success` flag:

```python
result = {
    'success': True,   # or False
    'content': '...',  # if successful
    'error': '...'     # if failed
}
```

This makes error handling consistent:

```python
result = fetch_oas_from_url(url)
if not result['success']:
    print(f"Error: {result['error']}")
    sys.exit(1)
```

---

## Dependencies

### Python Packages
- `requests` - For HTTP requests in fetcher

Install with:
```bash
./venv/bin/pip install requests
```

### System Requirements
- Node.js (for swagger-ui-offline-packager)
- npm packages in `nodejs/node_modules/`

---

## Comparison: Old vs New

### Old Structure (v1.0)
```
oas_converter.py    ← Everything in one file
├── OASConverter class
├── handler function
├── main function
└── CLI parsing
```

### New Structure (v2.0)
```
main.py         ← Orchestration only
fetcher.py      ← Fetching only
converter.py    ← Conversion only
```

**Benefits**:
- ✅ Easier to understand
- ✅ Easier to test
- ✅ Easier to modify
- ✅ Better code organization
- ✅ Reusable components

---

## Next Steps

### For Local Development
```bash
./venv/bin/python3 main.py --url <YOUR_URL>
```

### For Lambda Deployment
Create a Lambda wrapper that uses these modules:

```python
# lambda_function.py
import sys
sys.path.insert(0, '/opt/python')

from fetcher import fetch_oas_from_url
from converter import convert_oas

def lambda_handler(event, context):
    # Fetch
    result = fetch_oas_from_url(event['url'])
    
    # Convert
    conv = convert_oas(result['content'], result['filename'])
    
    return {
        'statusCode': 200,
        'body': conv['html_content']
    }
```

---

## Summary

✅ **Simple**: Three focused modules
✅ **Clear**: Easy to follow the flow
✅ **Testable**: Each module can be tested independently
✅ **Reusable**: Modules can be used in other scripts
✅ **Maintainable**: Changes are localized to specific modules

**Flow**: `main.py` → `fetcher.py` → `converter.py` → Output

---

**Last Updated**: 2025-11-19
**Version**: 2.0.0 (Modular)
