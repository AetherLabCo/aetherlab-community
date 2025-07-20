# AetherLab Community

Official SDKs and examples for the AetherLab AI Guardrails and Compliance Platform.

## 🚀 Quick Start

### Python SDK

```bash
# Install from PyPI
pip install aetherlab
```

### Basic Usage

```python
from aetherlab import AetherLabClient

# Initialize the client
client = AetherLabClient(api_key="your-api-key")

# Test a prompt for compliance
result = client.test_prompt(
    user_prompt="Hello, how can I help you today?",
    blacklisted_keywords=["harmful", "illegal"]
)

print(f"Compliant: {'✅' if result.is_compliant else '❌'}")
print(f"Confidence: {result.confidence_score:.2%}")
print(f"Threat Level: {result.avg_threat_level:.4f}")
```

## 📦 Available SDKs

### Python SDK (v0.1.2)
- **Status**: ✅ Available on TestPyPI
- **Documentation**: [Python SDK README](sdks/python/README.md)
- **Examples**: [Python Examples](examples/python/)

### JavaScript SDK
- **Status**: 🚧 Coming Soon

## 📚 Examples

- [Simple Example](examples/python/simple_example.py) - Quick start example
- [Comprehensive Demo](examples/python/guardrails_demo.py) - Full feature demonstration
- [Quick Start Guide](examples/python/client_quickstart.md) - Step-by-step tutorial

## 🔧 Features

- **Text Compliance Testing**: Validate prompts against customizable guardrails
- **Keyword Filtering**: Blacklist and whitelist specific terms
- **Threat Level Analysis**: Get detailed risk assessments
- **Real-time Monitoring**: Track AI behavior in production
- **Image Compliance**: Analyze visual content (coming soon)
- **Secure Watermarking**: Add trackable watermarks (coming soon)

## 📊 API Response Structure

```python
ComplianceResult:
  - is_compliant: bool        # Whether the prompt passes guardrails
  - confidence_score: float   # Confidence in the assessment (0-1)
  - avg_threat_level: float   # Average threat level (0-1)
  - status: int              # HTTP status code
  - message: str             # Response message
```

## 🛠️ Development

### Building from Source

```bash
cd sdks/python
python -m build
```

### Running Tests

```bash
cd examples/python
python simple_example.py
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 Changelog

### v0.1.2 (2024-07-20)
- 🐛 Fixed API authentication header (X-API-Key)
- 🐛 Fixed compliance status parsing
- ✨ Added avg_threat_level to response
- 🔧 Improved confidence score calculation

### v0.1.1 (2024-07-19)
- 🔧 Updated API endpoint to api.aetherlab.co

### v0.1.0 (2024-07-19)
- 🎉 Initial release

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [AetherLab Website](https://aetherlab.ai)
- [Documentation](https://docs.aetherlab.ai)
- [PyPI Package](https://pypi.org/project/aetherlab/)
- [GitHub Repository](https://github.com/AetherLabCo/aetherlab-community)

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/AetherLabCo/aetherlab-community/issues)
- **Email**: support@aetherlab.ai
- **Documentation**: [docs.aetherlab.ai](https://docs.aetherlab.ai) 