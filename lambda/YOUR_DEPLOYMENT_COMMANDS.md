# Your Deployment Commands

## ✅ Python Layer Already Published!

Your Python layer has been created and published:

```
LayerVersionArn: arn:aws:lambda:us-east-1:289491622160:layer:python-dependencies:1
```

---

## 🚀 Next Steps for lambda-layers-demo

### Step 1: Check Current Lambda Configuration

```bash
aws lambda get-function-configuration \
  --function-name lambda-layers-demo \
  --query '{Handler:Handler,Runtime:Runtime,Timeout:Timeout,MemorySize:MemorySize,Layers:Layers[*].Arn}'
```

This will show you what layers are currently attached (including any Node.js layer).

---

### Step 2: Build and Deploy Function Code

```bash
cd /Users/od/Documents/lambda-layers/lambda
./deploy.sh
```

This will:
- Package your code (fetcher.py, converter.py, lambda_function.py)
- Create lambda-function.zip
- Automatically deploy to lambda-layers-demo

---

### Step 3: Attach Python Layer

#### Option A: If you have a Node.js layer already attached

First, get your existing Node.js layer ARN:
```bash
aws lambda get-function-configuration \
  --function-name lambda-layers-demo \
  --query 'Layers[*].Arn' \
  --output table
```

Then attach BOTH layers:
```bash
aws lambda update-function-configuration \
  --function-name lambda-layers-demo \
  --layers \
    arn:aws:lambda:us-east-1:289491622160:layer:python-dependencies:1 \
    YOUR_NODEJS_LAYER_ARN_HERE
```

#### Option B: If you don't have Node.js layer yet

Just attach the Python layer for now:
```bash
aws lambda update-function-configuration \
  --function-name lambda-layers-demo \
  --layers \
    arn:aws:lambda:us-east-1:289491622160:layer:python-dependencies:1
```

---

### Step 4: Configure Lambda Settings

```bash
aws lambda update-function-configuration \
  --function-name lambda-layers-demo \
  --timeout 90 \
  --memory-size 1024
```

---

### Step 5: Test Lambda Function

Create test event:
```bash
cat > test-event.json << 'EOF'
{
  "url": "https://raw.githubusercontent.com/OD-Oraf/scratch/refs/heads/master/oas-examples/3.0/json/petstore-expanded.json",
  "verbose": true
}
EOF
```

Invoke Lambda:
```bash
aws lambda invoke \
  --function-name lambda-layers-demo \
  --payload file://test-event.json \
  --cli-binary-format raw-in-base64-out \
  response.json
```

Check response:
```bash
# View first 500 characters
cat response.json | head -c 500
echo ""

# Check if it's HTML
grep -q "<!DOCTYPE html>" response.json && echo "✅ HTML Response!" || echo "❌ Not HTML"

# Get size
ls -lh response.json
```

---

### Step 6: View Logs

```bash
aws logs tail /aws/lambda/lambda-layers-demo --follow
```

Look for:
```
================================================================================
🚀 Lambda Handler Started
Event keys: ['url', 'verbose']
================================================================================

Step 1: Fetching OAS content...
  ✓ Fetched: petstore-expanded.json (7357 bytes)

Step 2: Converting to HTML...
  ✓ Converted: 1535320 bytes
  Duration: 3.19s

✅ SUCCESS
```

---

## 🔧 Troubleshooting Commands

### Check if layers are attached
```bash
aws lambda get-function-configuration \
  --function-name lambda-layers-demo \
  --query 'Layers[*].{Arn:Arn,CodeSize:CodeSize}' \
  --output table
```

### List all your layers
```bash
aws lambda list-layers
```

### Test with simple event
```bash
aws lambda invoke \
  --function-name lambda-layers-demo \
  --payload '{"oas_content":"openapi: 3.0.0\ninfo:\n  title: Test\n  version: 1.0.0\npaths:\n  /test:\n    get:\n      responses:\n        \"200\":\n          description: OK"}' \
  --cli-binary-format raw-in-base64-out \
  response-simple.json
```

---

## 📋 Complete Deployment Checklist

- [x] Build Python layer - ✅ Done
- [x] Publish Python layer - ✅ Done (ARN: ...python-dependencies:1)
- [ ] Deploy function code - Run `./deploy.sh`
- [ ] Attach layers to function
- [ ] Configure timeout/memory
- [ ] Test with sample event
- [ ] Verify logs

---

## 🎯 Quick Copy-Paste Commands

```bash
# 1. Deploy function code
cd /Users/od/Documents/lambda-layers/lambda
./deploy.sh

# 2. Get current layers (to find Node.js layer ARN if exists)
aws lambda get-function-configuration \
  --function-name lambda-layers-demo \
  --query 'Layers[*].Arn'

# 3. Attach Python layer (+ Node.js if you have it)
# Replace NODEJS_LAYER_ARN if you have one, otherwise remove that line
aws lambda update-function-configuration \
  --function-name lambda-layers-demo \
  --layers \
    arn:aws:lambda:us-east-1:289491622160:layer:python-dependencies:1
    # Add your Node.js layer ARN here if you have one

# 4. Configure settings
aws lambda update-function-configuration \
  --function-name lambda-layers-demo \
  --timeout 90 \
  --memory-size 1024

# 5. Test
cat > test-event.json << 'EOF'
{
  "url": "https://raw.githubusercontent.com/OD-Oraf/scratch/refs/heads/master/oas-examples/3.0/json/petstore-expanded.json"
}
EOF

aws lambda invoke \
  --function-name lambda-layers-demo \
  --payload file://test-event.json \
  --cli-binary-format raw-in-base64-out \
  response.json

# 6. Check response
head -c 200 response.json
echo ""
```

---

## ✅ Summary

**Python Layer**: ✅ Published
```
arn:aws:lambda:us-east-1:289491622160:layer:python-dependencies:1
```

**Next**: 
1. Run `./deploy.sh` to update function code
2. Attach layer to your function
3. Test!

---

**Function Name**: lambda-layers-demo  
**Region**: us-east-1  
**Account**: 289491622160
