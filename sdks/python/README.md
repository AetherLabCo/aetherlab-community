# AetherLab Python SDK

Official Python SDK for the AetherLab AI Control Layer.

## Installation

```bash
pip install aetherlab
```

## Quick Start

```python
from aetherlab import AetherLabClient

# Initialize the client
client = AetherLabClient(api_key="your-api-key")

# Validate content (recommended new API)
result = client.validate_content(
    content="Your AI-generated content here",
    content_type="customer_support",
    desired_attributes=["helpful", "professional"],
    prohibited_attributes=["rude", "misleading"]
)

# Check compliance metrics
print(f"Compliant: {result.is_compliant}")
print(f"Probability of non-compliance: {result.avg_threat_level:.1%}")
print(f"Confidence in compliance: {result.confidence_score:.1%}")

if result.is_compliant:
    print(f"✅ Content is safe: {result.content}")
else:
    print(f"❌ Issues found: {result.violations}")
    print(f"💡 Suggestion: {result.suggested_revision}")

# Legacy API (still supported)
result = client.test_prompt(
    user_prompt="Hello, how can I help?",
    blacklisted_keywords=["harmful", "dangerous"]
)
print(f"Compliant: {result.is_compliant}")
```

## Features

- ✅ Content validation with context-aware analysis
- ✅ Multi-language support
- ✅ Real-time compliance checking
- ✅ Suggested revisions for non-compliant content
- ✅ Legacy API compatibility
- ✅ Media analysis capabilities
- ✅ Audit logging

## Documentation

For full documentation, visit [docs.aetherlab.ai](https://docs.aetherlab.ai)

## Examples

See the [examples directory](../../examples/python/) for complete examples.

## Support

- GitHub Issues: [github.com/AetherLabCo/aetherlab-community/issues](https://github.com/AetherLabCo/aetherlab-community/issues)
- Email: support@aetherlab.ai

## License

MIT 