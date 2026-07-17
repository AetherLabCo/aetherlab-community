# AetherLab Python SDK 0.5.0

Version 0.5.0 adds first-class server-side batch processing while preserving
the complete 0.4.1 scalar API.

## Highlights

- Submit the simplest prompt job with
  `client.check_prompt_batch(["first", "second"])`; media has the analogous
  URL/uploaded-file call.
- `check_prompt_batch()` and `check_media_batch()` use the recommended
  guardrail-specific routes, generate stable item correlation IDs, and derive
  a stable retry key when callers omit one.
- Use `create_batch()` unchanged for advanced provider-compatible inline or
  JSONL workflows.
- Upload JSONL inputs and batch-safe media with raw `x-api-key`
  authentication through the new file methods.
- Poll jobs with bounded backoff, cancel active jobs, and delete terminal
  jobs.
- Read unordered results as cursor-paginated JSON or NDJSON, correlated by
  each input's `custom_id`.
- Use the same API from `AetherLabClient` and `AsyncAetherLabClient`.

## Compatibility

`check_prompt()`, `check_media()`, `test_prompt()`, existing models, exception
mapping, retry behavior, `https://api.aetherlab.co`, and `x-api-key`
authentication are unchanged. Batch polling is available only through the v1
batch endpoints. Existing explicit custom IDs, per-item bodies/defaults,
idempotency keys, and low-level resource methods remain supported.

## Operational limits

- Inline: 1,000 requests or 10 MiB.
- JSONL: 50,000 requests or 200 MiB.
- Completion window: exactly 24 hours.
- Result retention: seven days.
- Batch media: HTTPS URL or uploaded `guardrail_media` file ID; embedded base64
  is not supported.

This release has not been published to TestPyPI or PyPI.
