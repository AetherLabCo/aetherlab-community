# AetherLab Python SDK

[![PyPI version](https://badge.fury.io/py/aetherlab.svg)](https://pypi.org/project/aetherlab/)
[![Python Versions](https://img.shields.io/pypi/pyversions/aetherlab.svg)](https://pypi.org/project/aetherlab/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://pepy.tech/badge/aetherlab)](https://pepy.tech/project/aetherlab)

The official Python SDK for AetherLab's AI Guardrails and Compliance Platform. Build safer AI applications with real-time content moderation, prompt injection detection, and comprehensive compliance monitoring.

## Installation

```bash
pip install aetherlab
```

## Quick Start

```python
from aetherlab import AetherLabClient

# Initialize the client
client = AetherLabClient(api_key="your-api-key")

# Test a text prompt
result = client.test_prompt(
    user_prompt="How can I help you today?",
    blacklisted_keywords=["harmful", "illegal"]
)

print(f"Compliance: {'✅ PASS' if result.is_compliant else '❌ FAIL'}")
print(f"Confidence: {result.confidence_score:.2%}")
```

## Features

- **Text Compliance Testing**: Test prompts against guardrails
- **Image Compliance**: Analyze images for inappropriate content  
- **Secure Watermarking**: Add trackable watermarks to images
- **Compliance Logging**: Track all AI interactions
- **Real-time Monitoring**: Monitor AI behavior in production

## Documentation

Full documentation available at [docs.aetherlab.ai](https://docs.aetherlab.ai)

## Examples

See the [examples directory](https://github.com/AetherLabCo/aetherlab-community/tree/main/examples/python) for detailed examples.

## Support

- Documentation: [docs.aetherlab.ai](https://docs.aetherlab.ai)
- Issues: [GitHub Issues](https://github.com/AetherLabCo/aetherlab-community/issues)
- Email: support@aetherlab.ai

## License

This project is licensed under the MIT License. 