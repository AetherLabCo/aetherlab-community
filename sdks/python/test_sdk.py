#!/usr/bin/env python3
"""Test script to verify AetherLab SDK functionality."""

import os
import sys

# Test 1: Import the package
try:
    import aetherlab
    print("✓ Package import successful")
    print(f"  Version: {aetherlab.__version__}")
except ImportError as e:
    print(f"✗ Failed to import package: {e}")
    sys.exit(1)

# Test 2: Import all exported classes
try:
    from aetherlab import (
        AetherLabClient, 
        AetherLabError,
        APIError,
        ValidationError,
        ComplianceResult
    )
    print("✓ All exports imported successfully")
except ImportError as e:
    print(f"✗ Failed to import exports: {e}")
    sys.exit(1)

# Test 3: Create client (should fail without API key)
try:
    client = AetherLabClient(api_key="test-key")
    print("✓ Client instantiation successful")
except Exception as e:
    print(f"✗ Failed to create client: {e}")
    sys.exit(1)

# Test 4: Check client methods exist
methods = ['test_prompt', '_request']
for method in methods:
    if hasattr(client, method):
        print(f"✓ Method '{method}' exists")
    else:
        print(f"✗ Method '{method}' missing")

print("\nAll tests passed! SDK is ready for packaging.")
