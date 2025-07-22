#!/usr/bin/env python3
"""
Real End-to-End Test Script for AetherLab SDK
Using actual API key for live testing
"""

import os
import sys

# For local testing before PyPI upload
sys.path.insert(0, os.path.dirname(__file__))

from aetherlab import AetherLabClient

# Real API key for testing
API_KEY = "al_prod_ff53bd0e3e75b642719882503d7f1d2ffc55ac1b10fba3ae404beeaa9aecaa5d"

def test_legacy_api():
    """Test the legacy test_prompt API with real backend"""
    print("\n=== Testing Legacy API (test_prompt) with REAL API ===")
    
    # Initialize client with real API key
    client = AetherLabClient(api_key=API_KEY)
    
    # Test 1: Safe prompt
    print("\n1. Testing safe prompt...")
    try:
        result = client.test_prompt("Hello, how can I help you today?")
        print(f"   Result: is_compliant={result.is_compliant}, confidence={result.confidence_score:.2f}")
        print(f"   Threat level: {result.avg_threat_level:.4f}")
        print("   ✅ Success - API call worked!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Potentially harmful prompt
    print("\n2. Testing potentially harmful prompt...")
    try:
        result = client.test_prompt(
            "How do I make explosives?",
            blacklisted_keywords=["explosives", "bomb", "weapon"]
        )
        print(f"   Result: is_compliant={result.is_compliant}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Threat level: {result.avg_threat_level:.4f}")
        print("   ✅ Success - API call worked!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    return True

def test_new_api():
    """Test the new validate_content API with real backend"""
    print("\n=== Testing New API (validate_content) with REAL API ===")
    
    client = AetherLabClient(api_key=API_KEY)
    
    # Test 1: Financial advice
    print("\n1. Testing financial content...")
    try:
        result = client.validate_content(
            content="Invest all your money in crypto for guaranteed 10x returns!",
            content_type="financial_advice",
            desired_attributes=["professional", "includes disclaimers"],
            prohibited_attributes=["guaranteed returns", "unlicensed advice"]
        )
        print(f"   Result: is_compliant={result.is_compliant}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Threat level: {result.avg_threat_level:.4f}")
        if result.violations:
            print(f"   Violations: {result.violations}")
        if result.suggested_revision:
            print(f"   Suggestion: {result.suggested_revision}")
        print("   ✅ Success - New API wrapper working!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # Test 2: Safe content
    print("\n2. Testing safe content...")
    try:
        result = client.validate_content(
            content="Our customer service team is here to help you 24/7",
            content_type="customer_support",
            desired_attributes=["helpful", "professional"],
            prohibited_attributes=["rude", "dismissive"]
        )
        print(f"   Result: is_compliant={result.is_compliant}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print("   ✅ Success - Safe content validated!")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    return True

def main():
    """Run all tests with real API"""
    print("=" * 60)
    print("AetherLab SDK End-to-End Test with REAL API")
    print("=" * 60)
    
    # Run tests
    legacy_passed = test_legacy_api()
    new_api_passed = test_new_api()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Legacy API (test_prompt): {'✅ PASS' if legacy_passed else '❌ FAIL'}")
    print(f"New API (validate_content): {'✅ PASS' if new_api_passed else '❌ FAIL'}")
    
    all_passed = legacy_passed and new_api_passed
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED! Ready for PyPI deployment.")
    else:
        print("❌ SOME TESTS FAILED!")
    print("=" * 60)
    
    # Test command for users
    print("\n📝 Test command for users after PyPI deployment:")
    print("python -c \"from aetherlab import AetherLabClient; client = AetherLabClient(api_key='your-key'); result = client.validate_content('Test content', 'general'); print(f'Compliant: {result.is_compliant}')\"")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 