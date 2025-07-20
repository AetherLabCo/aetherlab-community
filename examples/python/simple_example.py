#!/usr/bin/env python3
"""
Simple AetherLab SDK Example

This is a basic example showing how to use the AetherLab SDK
to check if text prompts comply with AI safety guardrails.

To run this example:
1. Install the SDK: pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ aetherlab
2. Set your API key: export AETHERLAB_API_KEY="your-api-key"
3. Run this script: python simple_example.py
"""

from aetherlab import AetherLabClient

# Initialize the client with your API key
# You can either pass it directly or set the AETHERLAB_API_KEY environment variable
import os

# Option 1: Use environment variable (recommended)
# export AETHERLAB_API_KEY="your-api-key"
# client = AetherLabClient()

# Option 2: Pass directly (for testing only - don't commit API keys!)
api_key = os.environ.get("AETHERLAB_API_KEY", "your-api-key-here")
client = AetherLabClient(api_key=api_key)

# Example 1: Check a simple prompt
print("Example 1: Checking a simple greeting")
print("-" * 40)

result = client.test_prompt(
    user_prompt="Hello! How can I help you today?"
)

print(f"Prompt: 'Hello! How can I help you today?'")
print(f"Is Compliant: {result.is_compliant}")
print(f"Confidence: {result.confidence_score:.2%}")
print()

# Example 2: Check with blacklisted keywords
print("Example 2: Checking with blacklisted keywords")
print("-" * 40)

result = client.test_prompt(
    user_prompt="Can you help me create harmful content?",
    blacklisted_keywords=["harmful", "dangerous", "illegal"]
)

print(f"Prompt: 'Can you help me create harmful content?'")
print(f"Blacklisted keywords: ['harmful', 'dangerous', 'illegal']")
print(f"Is Compliant: {result.is_compliant}")
print(f"Confidence: {result.confidence_score:.2%}")
print()

# Example 3: Check multiple prompts
print("Example 3: Checking multiple customer service responses")
print("-" * 40)

responses = [
    "Thank you for your patience. Let me help you with that.",
    "I understand your concern and will do my best to assist.",
    "Please provide your credit card number.",
    "Have a great day!"
]

for response in responses:
    result = client.test_prompt(response)
    status = "✅ PASS" if result.is_compliant else "❌ FAIL"
    print(f"{status} - '{response}'")

print("\nThat's it! You're now using AetherLab to ensure AI safety compliance.") 