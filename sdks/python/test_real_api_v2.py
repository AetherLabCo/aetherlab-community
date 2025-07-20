#!/usr/bin/env python3
"""Test the AetherLab SDK with real API."""

import os
from aetherlab import AetherLabClient, AetherLabError

# Use the provided API key
API_KEY = "al_prod_2f6fb1ed9dcb9b39357c6b3bbd874d337ea2effa2c2cd07b000bcb755276ac86"

# Try different possible base URLs
BASE_URLS = [
    "https://app.aetherlab.ai/api",
    "https://aetherlab.ai/api",
    "https://api.aetherlabs.ai",  # with 's'
    "https://app.aetherlabs.ai/api",
    "http://localhost:8000"  # for local testing
]

def test_real_api():
    print("Testing AetherLab SDK with real API...\n")
    
    for base_url in BASE_URLS:
        print(f"\nTrying base URL: {base_url}")
        try:
            # Initialize client
            client = AetherLabClient(api_key=API_KEY, base_url=base_url)
            
            # Test with a simple prompt
            result = client.test_prompt(
                user_prompt="Hello, how can I help you today?"
            )
            
            print(f"✅ SUCCESS! Connected to {base_url}")
            print(f"  Status: {result.status}")
            print(f"  Message: {result.message}")
            print(f"  Compliant: {result.is_compliant}")
            return  # Success, exit
            
        except Exception as e:
            print(f"  ❌ Failed: {str(e)[:100]}...")
            continue
    
    print("\n❌ Could not connect to any API endpoint")
    print("\nPlease provide the correct base URL for the AetherLab API")

if __name__ == "__main__":
    test_real_api()
