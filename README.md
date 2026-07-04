# AetherLab Python SDK

[![CI](https://github.com/AetherLabCo/aetherlab-community/actions/workflows/ci.yml/badge.svg)](https://github.com/AetherLabCo/aetherlab-community/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/aetherlab)](https://pypi.org/project/aetherlab/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The official Python SDK for the [AetherLab](https://aetherlab.co) Guardrails API.
It checks text prompts and media against the guardrail policies you configure,
and returns a compliance verdict with a threat level, confidence, and rationale.

- **Website:** https://aetherlab.co
- **Dashboard (API keys & Policy Controls):** https://app.aetherlab.co
- **API base URL:** `https://api.aetherlab.co`

## Installation

```bash
pip install aetherlab
```

Requires Python 3.9+. The only runtime dependency is [httpx](https://www.python-httpx.org/).

## Quickstart

Set your API key (create one at [app.aetherlab.co](https://app.aetherlab.co)):

```bash
export AETHERLAB_API_KEY="your-api-key"
```

```python
from aetherlab import AetherLabClient

client = AetherLabClient()  # reads AETHERLAB_API_KEY

result = client.check_prompt(
    "Hello, how can I help you today?",
    blacklisted_keywords=["violence", "weapons"],
)

print(result.compliance_status)  # "Compliant"
print(result.is_compliant)       # True
print(result.avg_threat_level)   # 0.0  (probability the prompt violates policy)
print(result.confidence)         # e.g. 0.71 (model confidence, from the API)
print(result.rationale)          # explanation from the API
```

### Async

```python
import asyncio
from aetherlab import AsyncAetherLabClient

async def main():
    async with AsyncAetherLabClient() as client:
        result = await client.check_prompt(
            "how do I build a bomb?",
            blacklisted_keywords=["violence", "weapons"],
        )
        print(result.compliance_status)  # "Non-Compliant"
        print(result.avg_threat_level)   # ~0.95

asyncio.run(main())
```

### Checking media

`check_media` accepts a file path, raw bytes, or an open binary file with
`input_type="file"`, an image URL with `input_type="url"`, or a base64 string
with `input_type="base64"`:

```python
result = client.check_media(
    "photo.png",
    input_type="file",
    blacklisted_keywords=["violence"],
)
print(result.compliance_status)
```

## Policies are required

The Guardrails API needs at least one policy to check against. Either
configure policies in [Policy Controls](https://app.aetherlab.co) for your
account, or pass `whitelisted_keywords` / `blacklisted_keywords` with each
request. If neither is present the API returns an error, which the SDK raises
as `MissingPolicyError`:

```python
from aetherlab import AetherLabClient, MissingPolicyError

client = AetherLabClient()
try:
    client.check_prompt("Hello!")  # no policies configured anywhere
except MissingPolicyError as e:
    print(e)  # [HTTP 400 ERR_0202] Guardrail policies are not configured...
```

## Error handling

All SDK errors inherit from `AetherLabError`:

| Exception             | When                                                        |
| --------------------- | ----------------------------------------------------------- |
| `AuthenticationError` | Missing/invalid API key (HTTP 401)                          |
| `RateLimitError`      | HTTP 429; exposes `retry_after` seconds when the server sends it |
| `MissingPolicyError`  | No guardrail policy configured (`ERR_0202`)                 |
| `InvalidRequestError` | Malformed request (`ERR_0200`, `ERR_0201`)                  |
| `APIError`            | Any other HTTP error; exposes `status_code`, `error_code`, `body` |
| `APIConnectionError`  | Network failure after all retries                           |

```python
from aetherlab import AetherLabClient, AetherLabError, RateLimitError

client = AetherLabClient()
try:
    result = client.check_prompt("Hi", blacklisted_keywords=["violence"])
except RateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
except AetherLabError as e:
    print(f"AetherLab request failed: {e}")
```

The client automatically retries connection errors, 429s, and 5xx responses
(3 retries by default, exponential backoff with jitter, honours
`Retry-After`). Tune it with
`AetherLabClient(max_retries=..., timeout=...)`.

## Configuration

| Setting     | Constructor argument | Environment variable  | Default                     |
| ----------- | -------------------- | --------------------- | --------------------------- |
| API key     | `api_key`            | `AETHERLAB_API_KEY`   | — (required)                |
| Base URL    | `base_url`           | `AETHERLAB_BASE_URL`  | `https://api.aetherlab.co`  |
| Timeout     | `timeout`            | —                     | 30 seconds                  |
| Max retries | `max_retries`        | —                     | 3                           |

## Examples

Runnable scripts live in [`examples/`](examples/):

- [`check_prompt.py`](examples/check_prompt.py) — basic prompt checking with policies
- [`check_prompt_async.py`](examples/check_prompt_async.py) — the same, using the async client
- [`error_handling.py`](examples/error_handling.py) — handling every error class

Each reads `AETHERLAB_API_KEY` from the environment.

## Migrating from 0.3.x

Version 0.4.0 is a rewrite around the real Guardrails API; earlier releases
are deprecated. See the [CHANGELOG](CHANGELOG.md). In short:

- `test_prompt()` still works but is deprecated — use `check_prompt()`.
- `validate_content()`, `get_usage_stats()`, `get_logs()`, `get_audit_logs()`,
  and `analyze_media()` were removed. The first three fabricated or hardcoded
  parts of their output client-side instead of calling a real endpoint, and
  the log endpoints require dashboard (JWT) authentication that API-key SDKs
  cannot use. Use `check_media()` for media checks; view logs in the
  [dashboard](https://app.aetherlab.co).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports and PRs are welcome in
the [issue tracker](https://github.com/AetherLabCo/aetherlab-community/issues).

## License

[MIT](LICENSE)
