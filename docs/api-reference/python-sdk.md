# Python SDK API Reference

Complete API reference for the AetherLab Python SDK.

## Installation

```bash
pip install aetherlab
```

## AetherLabClient

The main client class for interacting with the AetherLab API.

### Constructor

```python
AetherLabClient(
    api_key: Optional[str] = None,
    base_url: str = "https://api.aetherlab.co",
    timeout: int = 30
)
```

**Parameters:**
- `api_key` (str, optional): Your AetherLab API key. If not provided, will look for `AETHERLAB_API_KEY` environment variable.
- `base_url` (str): Base URL for the API. Defaults to production endpoint.
- `timeout` (int): Request timeout in seconds. Defaults to 30.

**Raises:**
- `ValidationError`: If no API key is provided or found in environment.

**Example:**
```python
# Using environment variable
client = AetherLabClient()

# Using direct API key
client = AetherLabClient(api_key="your-api-key")

# Using custom endpoint
client = AetherLabClient(
    api_key="your-api-key",
    base_url="https://staging-api.aetherlab.co",
    timeout=60
)
```

### Methods

#### test_prompt()

Test a text prompt for compliance against guardrails.

```python
test_prompt(
    user_prompt: str,
    whitelisted_keywords: Optional[List[str]] = None,
    blacklisted_keywords: Optional[List[str]] = None,
    **kwargs
) -> ComplianceResult
```

**Parameters:**
- `user_prompt` (str): The text prompt to test for compliance.
- `whitelisted_keywords` (List[str], optional): List of keywords that should be present.
- `blacklisted_keywords` (List[str], optional): List of keywords that should not be present.
- `**kwargs`: Additional parameters to pass to the API.

**Returns:**
- `ComplianceResult`: Object containing compliance analysis results.

**Raises:**
- `APIError`: If the API request fails.
- `ValidationError`: If parameters are invalid.
- `AuthenticationError`: If authentication fails.
- `RateLimitError`: If rate limit is exceeded.

**Example:**
```python
# Basic usage
result = client.test_prompt("Hello, how can I help?")

# With keywords
result = client.test_prompt(
    "Tell me about the weather",
    whitelisted_keywords=["weather", "forecast"],
    blacklisted_keywords=["harmful", "dangerous"]
)
```

#### test_image()

Test an image for compliance (placeholder - coming soon).

```python
test_image(
    image: Union[str, BinaryIO],
    input_type: str = "auto",
    output_type: str = "json",
    **kwargs
) -> MediaComplianceResult
```

**Parameters:**
- `image` (Union[str, BinaryIO]): Image to test (file path, URL, base64, or file object).
- `input_type` (str): Type of input ("file", "url", "base64", or "auto").
- `output_type` (str): Response format ("json" or "image").

**Returns:**
- `MediaComplianceResult`: Object containing image compliance analysis.

#### add_watermark()

Add a secure watermark to an image (placeholder - coming soon).

```python
add_watermark(
    image: Union[str, BinaryIO],
    watermark_text: Optional[str] = None,
    input_type: str = "auto",
    **kwargs
) -> SecureMarkResult
```

**Parameters:**
- `image` (Union[str, BinaryIO]): Image to watermark.
- `watermark_text` (str, optional): Custom watermark text.
- `input_type` (str): Type of input ("file", "url", "base64", or "auto").

**Returns:**
- `SecureMarkResult`: Object containing the watermarked image.

## Data Models

### ComplianceResult

Result object from text prompt compliance checking.

**Attributes:**
- `status` (int): HTTP status code of the response.
- `message` (str): Response message from the API.
- `is_compliant` (bool): Whether the prompt passes all guardrails.
- `confidence_score` (float): Confidence in the assessment (0-1).
- `avg_threat_level` (float): Average threat level detected (0-1).
- `guardrails_triggered` (List[str]): List of guardrails that were triggered.
- `details` (Dict[str, Any]): Additional details about the analysis.
- `recommendations` (List[str]): Recommendations for improving compliance.
- `metadata` (Dict[str, Any]): Additional metadata.

**Methods:**
- `__str__()`: Returns a formatted string representation of the result.

**Example:**
```python
result = client.test_prompt("Hello world")

print(f"Compliant: {result.is_compliant}")
print(f"Confidence: {result.confidence_score:.2%}")
print(f"Threat Level: {result.avg_threat_level}")

if not result.is_compliant:
    print(f"Triggered: {', '.join(result.guardrails_triggered)}")
```

### MediaComplianceResult

Result object from image/media compliance checking (coming soon).

**Attributes:**
- `status` (int): HTTP status code.
- `message` (str): Response message.
- `is_compliant` (bool): Whether the media is compliant.
- `confidence_score` (float): Confidence score (0-1).
- `detected_objects` (List[Dict]): Objects detected in the image.
- `detected_text` (Optional[str]): Text detected in the image.
- `content_warnings` (List[str]): Content warnings for the image.
- `metadata` (Dict[str, Any]): Additional metadata.
- `output_image` (Optional[str]): Base64 encoded annotated image.

### SecureMarkResult

Result object from watermarking operation (coming soon).

**Attributes:**
- `status` (int): HTTP status code.
- `message` (str): Response message.
- `success` (bool): Whether watermarking succeeded.
- `watermark_id` (Optional[str]): Unique ID of the watermark.
- `output_image` (str): Base64 encoded watermarked image.
- `metadata` (Dict[str, Any]): Additional metadata.

## Exceptions

### AetherLabError

Base exception class for all AetherLab errors.

```python
class AetherLabError(Exception):
    """Base exception for AetherLab SDK errors."""
```

### APIError

Raised when an API request fails.

```python
class APIError(AetherLabError):
    """Raised when an API request fails."""
```

### ValidationError

Raised when input validation fails.

```python
class ValidationError(AetherLabError):
    """Raised when input validation fails."""
```

### AuthenticationError

Raised when authentication fails.

```python
class AuthenticationError(AetherLabError):
    """Raised when authentication fails."""
```

### RateLimitError

Raised when rate limit is exceeded.

```python
class RateLimitError(AetherLabError):
    """Raised when rate limit is exceeded."""
```

## Error Handling

```python
from aetherlab import AetherLabClient
from aetherlab.exceptions import (
    APIError,
    ValidationError,
    AuthenticationError,
    RateLimitError
)

client = AetherLabClient()

try:
    result = client.test_prompt("Test prompt")
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded, please wait")
except ValidationError as e:
    print(f"Invalid input: {e}")
except APIError as e:
    print(f"API error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

## Rate Limits

The AetherLab API has the following rate limits:

- **Free tier**: 100 requests per minute
- **Pro tier**: 1,000 requests per minute
- **Enterprise**: Custom limits

Rate limit information is returned in response headers:
- `X-RateLimit-Limit`: Total allowed requests
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Unix timestamp when limit resets

## Best Practices

1. **Use environment variables** for API keys
2. **Implement retry logic** for transient failures
3. **Cache results** when testing the same content repeatedly
4. **Batch requests** when possible
5. **Monitor rate limits** to avoid throttling

## Support

- Documentation: [docs.aetherlab.ai](https://docs.aetherlab.ai)
- Email: support@aetherlab.ai
- GitHub: [github.com/AetherLabCo/aetherlab-community](https://github.com/AetherLabCo/aetherlab-community) 