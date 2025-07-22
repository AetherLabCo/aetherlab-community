# Quick Start Guide

Welcome to AetherLab! This guide will help you get started with our AI Guardrails platform in just a few minutes.

## Installation

### Python SDK

```bash
# Install from PyPI
pip install aetherlab

# Upgrade to latest version
pip install --upgrade aetherlab
```

## Get Your API Key

1. Sign up at [aetherlab.ai](https://aetherlab.ai)
2. Navigate to your dashboard
3. Generate an API key from the settings page

## Your First Script

Create a file called `test_aetherlab.py`:

```python
from aetherlab import AetherLabClient

# Initialize the client
client = AetherLabClient(api_key="your-api-key-here")

# Test a simple prompt
result = client.test_prompt("Hello, how can I help you today?")

# Check the results
if result.is_compliant:
    print("✅ This prompt is safe to use!")
else:
    print("❌ This prompt may have issues.")
    
print(f"Confidence: {result.confidence_score:.2%}")
print(f"Threat Level: {result.avg_threat_level:.4f}")
```

## Using Environment Variables (Recommended)

Instead of hardcoding your API key, use environment variables:

```bash
export AETHERLAB_API_KEY="your-api-key-here"
```

Then in your code:

```python
from aetherlab import AetherLabClient

# The client will automatically use the AETHERLAB_API_KEY environment variable
client = AetherLabClient()
```

## Testing with Keywords

### Blacklisted Keywords

Prevent specific terms from being used:

```python
result = client.test_prompt(
    "Tell me about harmful activities",
    blacklisted_keywords=["harmful", "dangerous", "illegal"]
)

if not result.is_compliant:
    print("Prompt contains blacklisted terms!")
```

### Whitelisted Keywords

Ensure specific terms are present:

```python
result = client.test_prompt(
    "What's the weather forecast for tomorrow?",
    whitelisted_keywords=["weather", "forecast"],
    blacklisted_keywords=["harmful"]
)
```

## Understanding Results

The `ComplianceResult` object contains:

- `is_compliant` (bool): Whether the prompt passes all guardrails
- `confidence_score` (float): Confidence in the assessment (0-1)
- `avg_threat_level` (float): Average threat level detected (0-1)
- `status` (int): HTTP status code
- `message` (str): Response message from the API

## Common Use Cases

### 1. Content Moderation

```python
def moderate_user_content(user_input):
    result = client.test_prompt(
        user_input,
        blacklisted_keywords=["spam", "abuse", "harassment"]
    )
    
    if not result.is_compliant:
        return "Your message violates our community guidelines."
    
    return user_input  # Safe to display
```

### 2. AI Response Validation

```python
def validate_ai_response(ai_output):
    result = client.test_prompt(ai_output)
    
    if result.avg_threat_level > 0.5:
        return "I cannot provide that information."
    
    return ai_output
```

### 3. Input Sanitization

```python
def sanitize_prompt(user_prompt):
    result = client.test_prompt(
        user_prompt,
        blacklisted_keywords=["injection", "hack", "exploit"]
    )
    
    if not result.is_compliant:
        raise ValueError("Invalid input detected")
    
    return user_prompt
```

## Next Steps

- Read the [API Reference](../api-reference/python-sdk.md)
- Check out [Tutorials](../tutorials/index.md)
- Learn [Best Practices](../best-practices/security.md)
- Join our [Community](https://discord.gg/aetherlab)

## Need Help?

- 📧 Email: support@aetherlab.ai
- 💬 Discord: [Join our server](https://discord.gg/aetherlab)
- 📚 Docs: [docs.aetherlab.ai](https://docs.aetherlab.ai) 