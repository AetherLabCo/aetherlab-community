# AetherLab Python SDK

[![PyPI version](https://badge.fury.io/py/aetherlab.svg)](https://pypi.org/project/aetherlab/)
[![Python Versions](https://img.shields.io/pypi/pyversions/aetherlab.svg)](https://pypi.org/project/aetherlab/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://pepy.tech/badge/aetherlab)](https://pepy.tech/project/aetherlab)

The official Python SDK for AetherLab's AI Control Platform. Ensure your AI outputs are safe, compliant, and aligned with your business requirements.

## Installation

```bash
pip install aetherlab
```

## Quick Start

```python
from aetherlab import AetherLabClient

# Initialize the client
client = AetherLabClient(api_key="your-api-key")

# AI generates content that could be risky
ai_response = "You should invest all your money in crypto! Guaranteed 10x returns!"

# AetherLab ensures it's safe and compliant
result = client.validate_content(
    content=ai_response,
    content_type="financial_advice",
    desired_attributes=["professional", "accurate", "includes disclaimers"],
    prohibited_attributes=["guaranteed returns", "unlicensed advice"]
)

if result.is_compliant:
    print(f"✅ Safe to send: {result.content}")
else:
    print(f"🚫 Blocked: {result.violations}")
    print(f"✅ Safe alternative: {result.suggested_revision}")
```

## Features

- **Context-Aware Control**: Not just keyword blocking - understands intent
- **Real-Time Validation**: <50ms response times
- **Multi-Language Support**: Works across 42+ languages
- **Compliance Ready**: Built-in support for SEC, HIPAA, GDPR, and more
- **Enterprise Scale**: Handle millions of requests per day

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