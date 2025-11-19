# Quick Start Guide

## ✅ Restructured to Modular Design!

The OAS converter is now split into **3 simple, focused modules** that are easy to understand and test.

---

## 📁 Structure

```
main.py         ← Entry point (orchestrates everything)
fetcher.py      ← Fetches OAS files (URL or filesystem)
converter.py    ← Converts OAS to HTML
```

---

## 🚀 Quick Commands

### 1. Fetch from URL and Convert (saves to output/ directory)
```bash
./venv/bin/python3 main.py --url https://raw.githubusercontent.com/OD-Oraf/scratch/refs/heads/master/oas-examples/3.0/json/petstore-expanded.json
# Outputs: output/petstore-expanded.html
```

### 2. Convert Local File (saves to output/ directory)
```bash
./venv/bin/python3 main.py --file sample-oas-files/simple-api.yaml
# Outputs: output/simple-api.html
```

### 3. Save to Custom Location (optional)
```bash
./venv/bin/python3 main.py \
  --url https://example.com/api.json \
  --output docs/api.html
```

### 4. Quiet Mode
```bash
./venv/bin/python3 main.py --url <URL> --quiet
```

### 5. Help
```bash
./venv/bin/python3 main.py --help
```

---

## 📊 Flow

```
┌─────────┐
│ main.py │  ← You run this
└────┬────┘
     │
     ├──→ fetcher.py   ← Fetches OAS file (URL or local)
     │         ↓
     │      Returns: {content, filename}
     │
     └──→ converter.py ← Converts OAS to HTML
               ↓
            Returns: {html_content, html_file}
```

---

## 🎯 Test Results

### URL Fetch + Convert ✅
```bash
./venv/bin/python3 main.py --url https://raw.githubusercontent.com/OD-Oraf/scratch/refs/heads/master/oas-examples/3.0/json/petstore-expanded.json

✅ SUCCESS
OAS File: petstore-expanded.json
HTML Output: output/petstore-expanded.html
HTML Size: 1499.34 KB (1.46 MB)
Total Duration: 3.03s
```

### File Fetch + Convert ✅
```bash
./venv/bin/python3 main.py --file sample-oas-files/simple-api.yaml

✅ SUCCESS
OAS File: simple-api.yaml
HTML Output: output/simple-api.html
HTML Size: 1497.09 KB (1.46 MB)
Total Duration: 3.19s
```

---

## 🧩 Use Modules Independently

### Example: Batch Processing
```python
from fetcher import fetch_oas_from_url
from converter import convert_oas

urls = [
    "https://example.com/api1.json",
    "https://example.com/api2.json"
]

for url in urls:
    # Fetch
    fetch_result = fetch_oas_from_url(url)
    if not fetch_result['success']:
        continue
    
    # Convert
    conv_result = convert_oas(
        fetch_result['content'],
        fetch_result['filename']
    )
    
    # Save
    with open(f"output/{fetch_result['filename']}.html", 'w') as f:
        f.write(conv_result['html_content'])
```

---

## 📚 Key Benefits

✅ **Simple**: Clear flow through 3 focused modules  
✅ **Testable**: Each module can be tested independently  
✅ **Reusable**: Import and use in other scripts  
✅ **Maintainable**: Changes localized to specific modules  
✅ **Easy to Extend**: Add new fetchers or converters easily  

---

## 🔧 Dependencies

### Installed
```bash
./venv/bin/pip install requests  # ✅ Already installed
```

### Required
- Node.js (system or local)
- npm package: swagger-ui-offline-packager (in nodejs/node_modules/)

---

## 📖 Documentation

| File | Purpose |
|------|---------|
| `QUICK_START.md` | This file - Quick reference |
| `MODULAR_STRUCTURE.md` | Complete documentation |
| `main.py` | Example usage (run it!) |
| `fetcher.py` | Can test standalone |
| `converter.py` | Can test standalone |

---

## ✅ Summary

**What You Have**:
- 3 focused, reusable modules
- Command-line tool (main.py)
- Works with URLs and local files
- Clean, easy-to-understand code flow

**What You Can Do**:
```bash
# Simplest usage (saves to output/ directory)
./venv/bin/python3 main.py --url <YOUR_OAS_URL>

# That's it! ✅
```

**Output Directory**:
- All HTML files save to `output/` by default
- Automatically created if doesn't exist
- Filename matches OAS file: `api.json` → `output/api.html`
- Override with `--output` flag for custom locations

**Next Steps**:
- Run with your OAS URLs
- Check `output/` directory for generated HTML
- Use modules in custom scripts
- Extend with new features (S3, etc.)

---

**Last Updated**: 2025-11-19  
**Version**: 2.0.0 (Modular Structure)
