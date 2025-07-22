# AetherLab SDK Quick Start Guide

## Installation

```bash
# Install from PyPI
pip install aetherlab

# Upgrade to latest version
pip install --upgrade aetherlab
```

## Basic Usage

### 1. Set up your API key

You can either set it as an environment variable:
```bash
export AETHERLAB_API_KEY="your-api-key-here"
```

Or pass it directly when creating the client:
```python
from aetherlab import AetherLabClient

client = AetherLabClient(api_key="your-api-key-here")
```

### 2. Test a text prompt

```python
from aetherlab import AetherLabClient

# Initialize the client
client = AetherLabClient(api_key="your-api-key")

# Test a prompt
result = client.test_prompt("How can I help you today?")

# Check the results
print(f"Is Compliant: {result.is_compliant}")
print(f"Confidence: {result.confidence_score:.2%}")
```

### 3. Use blacklisted keywords

```python
result = client.test_prompt(
    user_prompt="Tell me something harmful",
    blacklisted_keywords=["harmful", "dangerous", "illegal"]
)

if not result.is_compliant:
    print("This prompt contains blacklisted content!")
```

### 4. Run the example script

Save this as `test_aetherlab.py`:

```python
from aetherlab import AetherLabClient

# Initialize client (use your API key)
client = AetherLabClient(api_key="your-api-key")

# Test some prompts
prompts = [
    "Hello, how are you?",
    "What's the weather like?",
    "Tell me something inappropriate"
]

for prompt in prompts:
    result = client.test_prompt(prompt)
    status = "✅ Safe" if result.is_compliant else "❌ Unsafe"
    print(f"{status}: {prompt}")
```

Then run it:
```bash
python test_aetherlab.py
```

## Full Example

For a complete working example, check out the `simple_example.py` file or the more comprehensive `examples/python/guardrails_demo.py` in the repository.

## Common Use Cases

1. **Content Moderation**: Check user-generated content before displaying
2. **Chatbot Safety**: Validate AI responses before sending to users
3. **Input Validation**: Screen user inputs for harmful requests
4. **Compliance Checking**: Ensure outputs meet regulatory requirements

## Need Help?

- Documentation: https://docs.aetherlab.ai
- GitHub: https://github.com/AetherLabCo/aetherlab-community
- Support: support@aetherlab.ai 