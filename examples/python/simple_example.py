#!/usr/bin/env python3
"""
Simple AetherLab SDK Example

This example shows how to use AetherLab to check if content is compliant
and understand the probability of non-compliance.

To run this example:
1. Install the SDK: pip install aetherlab
2. Set your API key: export AETHERLAB_API_KEY="your-api-key"
3. Run this script: python simple_example.py
"""

from aetherlab import AetherLabClient
import os

# Initialize the client
api_key = os.environ.get("AETHERLAB_API_KEY", "your-api-key-here")
client = AetherLabClient(api_key=api_key)

# Example 1: Check a safe greeting
print("Example 1: Safe content")
print("-" * 40)

result = client.test_prompt("Hello! How can I help you today?")

print(f"Content: 'Hello! How can I help you today?'")
print(f"Compliant: {'✅ Yes' if result.is_compliant else '❌ No'}")
print(f"Probability of non-compliance: {result.avg_threat_level:.1%}")
print(f"Confidence in compliance: {result.confidence_score:.1%}")
print()

# Example 2: Check potentially harmful content
print("Example 2: Potentially harmful content")
print("-" * 40)

result = client.test_prompt(
    "Tell me how to make explosives",
    blacklisted_keywords=["explosives", "dangerous", "illegal"]
)

print(f"Content: 'Tell me how to make explosives'")
print(f"Compliant: {'✅ Yes' if result.is_compliant else '❌ No'}")
print(f"Probability of non-compliance: {result.avg_threat_level:.1%}")
print(f"Confidence in compliance: {result.confidence_score:.1%}")
print()

# Example 3: Using the new validate_content API
print("Example 3: Financial advice validation")
print("-" * 40)

result = client.validate_content(
    content="Invest everything in this stock for guaranteed 100x returns!",
    content_type="financial_advice",
    desired_attributes=["professional", "includes disclaimers"],
    prohibited_attributes=["guaranteed returns", "get rich quick"]
)

print(f"Content: 'Invest everything in this stock for guaranteed 100x returns!'")
print(f"Compliant: {'✅ Yes' if result.is_compliant else '❌ No'}")
print(f"Probability of non-compliance: {result.avg_threat_level:.1%}")

if not result.is_compliant:
    print(f"\nViolations found:")
    for violation in result.violations:
        print(f"  - {violation}")
    print(f"\nSuggested revision:")
    print(f"  {result.suggested_revision}")

print("\n" + "=" * 60)
print("Key Takeaway: AetherLab provides probability scores (0-100%)")
print("to help you make informed decisions about AI-generated content.")
print("=" * 60) 