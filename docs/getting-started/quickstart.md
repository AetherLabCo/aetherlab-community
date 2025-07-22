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

# Initialize AetherLab
client = AetherLabClient(api_key="your-api-key")

# AI generates a response that could be risky
ai_response = "You should definitely invest all your savings in crypto! Guaranteed 10x returns!"

# AetherLab ensures it's safe and compliant
result = client.validate_content(
    content=ai_response,
    content_type="financial_advice",
    desired_attributes=["professional", "accurate", "includes disclaimers"],
    prohibited_attributes=["guaranteed returns", "financial advice without disclaimer"]
)

# Check the result
if result.is_compliant:
    print("✅ Content is safe to use!")
    print(f"Confidence: {result.confidence_score:.1%}")
    print(f"Probability of non-compliance: {result.avg_threat_level:.1%}")
else:
    print("❌ Content has compliance issues!")
    print(f"Probability of non-compliance: {result.avg_threat_level:.1%}")
    print(f"Violations: {result.violations}")
    print(f"Suggested revision: {result.suggested_revision}")
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

## Real-World Examples

### Media & Entertainment

Ensure AI-generated content meets brand standards:

```python
# AI generates show description
ai_description = "This show is better than Netflix! Contains spoilers: everyone dies!"

result = client.validate_content(
    content=ai_description,
    content_type="media_description",
    desired_attributes=["engaging", "spoiler-free", "brand-appropriate"],
    prohibited_attributes=["competitor mentions", "plot spoilers"]
)

# Result: Blocked for competitor mention and spoilers
# Suggests: "This captivating show delivers suspense and drama!"
```

### Financial Services

Ensure compliance and prevent harmful advice:

```python
# Customer asks about investments
ai_response = "Bitcoin will definitely 10x! Move your 401k now!"

result = client.validate_content(
    content=ai_response,
    content_type="financial_advice",
    desired_attributes=["educational", "includes disclaimers"],
    prohibited_attributes=["guaranteed returns", "unlicensed advice"],
    regulations=["SEC", "FINRA"]
)

# Result: Blocked for compliance violations
# Suggests: "Cryptocurrency is volatile. Consult a licensed advisor."
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