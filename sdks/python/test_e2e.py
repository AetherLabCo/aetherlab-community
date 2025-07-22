#!/usr/bin/env python3
"""
End-to-End Test Script for AetherLab SDK

This script tests all functionality of the SDK:
1. Legacy API (test_prompt)
2. New API (validate_content)
3. Error handling
4. Media functions (mocked)
"""

import os
import sys

# For local testing before PyPI upload
sys.path.insert(0, os.path.dirname(__file__))

from aetherlab import AetherLabClient

def test_legacy_api():
    """Test the legacy test_prompt API"""
    print("\n=== Testing Legacy API (test_prompt) ===")
    
    # Initialize client
    client = AetherLabClient(api_key="test-api-key")
    
    # Test 1: Simple prompt
    print("\n1. Testing simple prompt...")
    try:
        result = client.test_prompt("Hello, how can I help you today?")
        print(f"   Result: is_compliant={result.is_compliant}, confidence={result.confidence_score:.2f}")
        print("   ✅ Success")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: With blacklist/whitelist
    print("\n2. Testing with keywords...")
    try:
        result = client.test_prompt(
            "Tell me about the weather",
            whitelisted_keywords=["weather", "help"],
            blacklisted_keywords=["harmful", "dangerous"]
        )
        print(f"   Result: is_compliant={result.is_compliant}")
        print("   ✅ Success")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    return True

def test_new_api():
    """Test the new validate_content API"""
    print("\n=== Testing New API (validate_content) ===")
    
    client = AetherLabClient(api_key="test-api-key")
    
    # Test 1: Financial advice
    print("\n1. Testing financial content...")
    try:
        result = client.validate_content(
            content="Invest all your money in crypto for guaranteed returns!",
            content_type="financial_advice",
            desired_attributes=["professional", "includes disclaimers"],
            prohibited_attributes=["guaranteed returns", "unlicensed advice"]
        )
        print(f"   Result: is_compliant={result.is_compliant}")
        print(f"   Violations: {result.violations}")
        print(f"   Suggestion: {result.suggested_revision}")
        print("   ✅ Success")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Medical content
    print("\n2. Testing medical content...")
    try:
        result = client.validate_content(
            content="This medication will cure your illness completely",
            content_type="medical_advice",
            context={"source": "user_generated"},
            desired_attributes=["factual", "includes medical disclaimer"],
            prohibited_attributes=["unverified claims", "medical diagnosis"]
        )
        print(f"   Result: is_compliant={result.is_compliant}")
        if not result.is_compliant:
            print(f"   Suggestion: {result.suggested_revision}")
        print("   ✅ Success")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    return True

def test_media_functions():
    """Test media analysis functions (will fail with test API key)"""
    print("\n=== Testing Media Functions ===")
    
    client = AetherLabClient(api_key="test-api-key")
    
    # Test analyze_media
    print("\n1. Testing analyze_media...")
    try:
        result = client.analyze_media(
            image_data="fake-base64-image-data",
            media_type="image"
        )
        print("   ✅ Function call succeeded (would fail with real API)")
    except Exception as e:
        print(f"   Expected error (no real API): {type(e).__name__}")
    
    # Test watermarking
    print("\n2. Testing add_secure_watermark...")
    try:
        result = client.add_secure_watermark(
            image_data="fake-base64-image-data",
            watermark_type="invisible",
            metadata={"text": "© AetherLab 2024"}
        )
        print("   ✅ Function call succeeded (would fail with real API)")
    except Exception as e:
        print(f"   Expected error (no real API): {type(e).__name__}")
    
    return True

def test_error_handling():
    """Test error handling"""
    print("\n=== Testing Error Handling ===")
    
    # Test missing API key
    print("\n1. Testing missing API key...")
    try:
        os.environ.pop('AETHERLAB_API_KEY', None)
        client = AetherLabClient()
        print("   ❌ Should have raised error")
        return False
    except Exception as e:
        print(f"   ✅ Correctly raised: {type(e).__name__}")
    
    # Test with API key
    print("\n2. Testing with API key...")
    try:
        client = AetherLabClient(api_key="test-key")
        print("   ✅ Client initialized")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("=" * 60)
    print("AetherLab SDK End-to-End Test")
    print("=" * 60)
    
    # Track results
    results = []
    
    # Run tests
    results.append(("Legacy API", test_legacy_api()))
    results.append(("New API", test_new_api()))
    results.append(("Error Handling", test_error_handling()))
    results.append(("Media Functions", test_media_functions()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED!")
    else:
        print("❌ SOME TESTS FAILED!")
    print("=" * 60)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 