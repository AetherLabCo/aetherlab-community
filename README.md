# AetherLab Python SDK

[![PyPI](https://img.shields.io/pypi/v/aetherlab)](https://pypi.org/project/aetherlab/)
[![Python versions](https://img.shields.io/pypi/pyversions/aetherlab)](https://pypi.org/project/aetherlab/)
[![CI](https://github.com/AetherLabCo/aetherlab-community/actions/workflows/ci.yml/badge.svg)](https://github.com/AetherLabCo/aetherlab-community/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

The official Python SDK for [AetherLab](https://aetherlab.co) - AI guardrails,
LLM safety, and content moderation for production AI applications. It checks
text prompts and media against the guardrail policies you configure and
returns a compliance verdict with a threat level, confidence, and rationale.
Built for developers adding a safety and compliance layer to LLM apps,
chatbots, and agents.

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

## Server-side batches

Version 0.5.0 adds server-side prompt and media jobs. Batch helpers submit one
job and return a `BatchJob`; they do not fan out into repeated `check_prompt`
or `check_media` calls. The recommended PromptGuard call is exactly:

```python
job = client.check_prompt_batch(["first", "second"])
```

The submission call returns queued job metadata, not compliance verdicts.
Call `wait_for_batch()` to poll the job to a terminal state, then retrieve its
item results as shown below. Small batches commonly complete in about 1–2
minutes; larger batches can take longer depending on item count, reasoning
mode, and service load. The supported 24-hour processing window is not a
completion-time SLA.

The SDK uses `POST /v1/guardrails/prompt/batches`, where the endpoint and
24-hour window are implicit. Shared settings and per-item overrides remain
available without changing the simple case:

```python
job = client.check_prompt_batch(
    [
        "A normal support message",
        {
            "custom_id": "ticket-42",
            "input": "A per-item prompt",
            "reasoning_mode": "high",
        },
    ],
    blacklisted_keywords=["violence", "weapons"],
    defaults={"risk_tolerance": "medium"},
    metadata={"dataset": "support-review"},
)

job = client.wait_for_batch(job, timeout=900)
for item in client.iter_batch_results(job.id):
    # Results are unordered: always correlate them by custom_id.
    if item.status == "succeeded":
        print(item.custom_id, item.result.compliance_status)
    else:
        print(item.custom_id, item.error)
```

The convenience methods generate deterministic item `custom_id` values and a
stable payload-derived idempotency key when omitted. This makes retrying the
same logical SDK call safe, including after an uncertain network response.
Pass your own `custom_id` values to join unordered results directly to your
records. Pass a stable `idempotency_key` to coordinate retries with another
system, or a new unique key when you intentionally want to resubmit an
identical payload as a new job.

Shared defaults are merged first and each item's fields win on conflicts.
`"Compliant"` and `"Non-Compliant"` are both successful guardrail results;
transport or validation failures use an item failure state.

The generic `create_batch()` resource method is preserved for advanced,
provider-compatible inline or JSONL workflows. For larger datasets, upload
UTF-8 JSONL and create a job from the file:

```python
batch_input = client.upload_file("requests.jsonl", purpose="batch")
job = client.create_batch(
    "/v1/guardrails/prompt",
    input_file_id=batch_input.id,
    completion_window="24h",
    idempotency_key="prompt-jsonl-2026-07-16",
    metadata={"source": "nightly"},
)
```

Each non-empty JSONL line must be an object such as:

```json
{"custom_id":"row-1","body":{"user_prompt":"Text to check"}}
```

Media batches accept HTTPS URLs or IDs returned from a
`purpose="guardrail_media"` upload. The returned `BatchFile` object itself is
also accepted. Embedded base64 is intentionally rejected:

```python
media_file = client.upload_file("photo.png", purpose="guardrail_media")
job = client.check_media_batch(
    [
        "https://cdn.example.com/photo-1.png",
        media_file,
        {"custom_id": "photo-3", "file_id": media_file.id},
    ],
)
```

Use `list_batch_results()` / `get_batch_results()` for cursor-paginated JSON,
or `download_batch_results()` and `iter_batch_results()` for NDJSON. Jobs can
be listed, retrieved, cancelled, and deleted with `list_batches()`,
`retrieve_batch()`, `cancel_batch()`, and `delete_batch()`; only terminal jobs
can be deleted. The async client exposes matching `await`/async-iteration
methods.

Server limits are 1,000 requests and 10 MiB for inline jobs, or 50,000 lines
and 200 MiB for JSONL input. The completion window is exactly `24h`, and
result artifacts expire after seven days.

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

Runnable scripts live in [`examples/`](https://github.com/AetherLabCo/aetherlab-community/tree/main/examples):

- [`check_prompt.py`](https://github.com/AetherLabCo/aetherlab-community/blob/main/examples/check_prompt.py) — basic prompt checking with policies
- [`check_prompt_async.py`](https://github.com/AetherLabCo/aetherlab-community/blob/main/examples/check_prompt_async.py) — the same, using the async client
- [`batch_prompt.py`](https://github.com/AetherLabCo/aetherlab-community/blob/main/examples/batch_prompt.py) — server-side prompt submission and NDJSON results
- [`batch_media_async.py`](https://github.com/AetherLabCo/aetherlab-community/blob/main/examples/batch_media_async.py) — async media batch with URL/file-ID inputs
- [`error_handling.py`](https://github.com/AetherLabCo/aetherlab-community/blob/main/examples/error_handling.py) — handling every error class

Each reads `AETHERLAB_API_KEY` from the environment.

## Migrating from 0.3.x

Version 0.4.0 is a rewrite around the real Guardrails API; earlier releases
are deprecated. See the [CHANGELOG](https://github.com/AetherLabCo/aetherlab-community/blob/main/CHANGELOG.md). In short:

- `test_prompt()` still works but is deprecated — use `check_prompt()`.
- `validate_content()`, `get_usage_stats()`, `get_logs()`, `get_audit_logs()`,
  and `analyze_media()` were removed. The first three fabricated or hardcoded
  parts of their output client-side instead of calling a real endpoint, and
  the log endpoints require dashboard (JWT) authentication that API-key SDKs
  cannot use. Use `check_media()` for media checks; view logs in the
  [dashboard](https://app.aetherlab.co).

## Contributing

See [CONTRIBUTING.md](https://github.com/AetherLabCo/aetherlab-community/blob/main/CONTRIBUTING.md). Bug reports and PRs are welcome in
the [issue tracker](https://github.com/AetherLabCo/aetherlab-community/issues).

## License

[MIT](https://github.com/AetherLabCo/aetherlab-community/blob/main/LICENSE)
