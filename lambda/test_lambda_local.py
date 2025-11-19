#!/usr/bin/env python3
"""
Test Lambda function locally
"""

import json
import sys
from lambda_function import lambda_handler


def test_lambda(event_name, event):
    """Test lambda handler with an event"""
    print("\n" + "="*80)
    print(f"TEST: {event_name}")
    print("="*80)
    print(f"Event: {json.dumps(event, indent=2)}")
    print()
    
    result = lambda_handler(event, context=None)
    
    print("\n" + "="*80)
    print("RESULT:")
    print("="*80)
    print(f"Status Code: {result['statusCode']}")
    
    if result['statusCode'] == 200:
        html_length = len(result['body'])
        print(f"HTML Length: {html_length} bytes ({html_length / 1024:.2f} KB, {html_length / 1024 / 1024:.2f} MB)")
        print(f"Content-Type: {result.get('headers', {}).get('Content-Type', 'N/A')}")
        print("✅ SUCCESS")
    else:
        body = json.loads(result['body']) if isinstance(result['body'], str) else result['body']
        print(f"Error: {body}")
        print("❌ FAILED")
    
    return result['statusCode'] == 200


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🧪 Lambda Function Local Tests")
    print("="*80)
    
    tests = [
        ("URL Input", {
            'url': 'https://raw.githubusercontent.com/OD-Oraf/scratch/refs/heads/master/oas-examples/3.0/json/petstore-expanded.json',
            'verbose': True
        }),
        
        ("Direct Content", {
            'oas_content': '''openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /test:
    get:
      summary: Test endpoint
      responses:
        '200':
          description: OK''',
            'oas_file_name': 'test-api.yaml',
            'verbose': True
        }),
        
        # S3 test would require AWS credentials
        # ("S3 Input", {
        #     's3_bucket': 'my-bucket',
        #     's3_key': 'oas-files/api.json',
        #     'verbose': True
        # }),
    ]
    
    results = []
    for test_name, event in tests:
        try:
            passed = test_lambda(test_name, event)
            results.append((test_name, passed))
        except Exception as e:
            print(f"\n❌ Test exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print("\n" + "="*80)
    print(f"Results: {passed}/{total} tests passed")
    print("="*80)
    
    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n❌ {total - passed} test(s) failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
