# Changelog

All notable changes to the AetherLab Python SDK are documented here.

## [Unreleased]

### Fixed
- Mapped `check_prompt_batch()` items now accept the documented `input` alias
  as well as `prompt` and `user_prompt`, and reject ambiguous combinations
  before issuing a request.

## [0.5.0] - 2026-07-16

### Added
- Raw API-key file methods for batch JSONL and guardrail media uploads:
  `upload_file()`, `retrieve_file()`, and `delete_file()`, with matching async
  methods.
- Full server-side batch lifecycle: `create_batch()`, `list_batches()`,
  `retrieve_batch()`, `cancel_batch()`, and terminal-only `delete_batch()`.
- Cursor-paginated JSON results plus NDJSON download and parsed sync/async
  iteration. Results retain their `custom_id` because server ordering is not
  significant.
- Bounded `wait_for_batch()` polling with capped backoff, overall timeout, and
  caller-controlled cancellation.
- Additive `check_prompt_batch()` and `check_media_batch()` helpers. They
  use the recommended guardrail-specific routes, create one server-side job,
  merge shared defaults with per-item bodies, and generate deterministic
  custom IDs only when omitted. Media batches accept HTTPS URLs, uploaded file
  IDs, and returned `BatchFile` objects.
- Convenience methods derive a stable payload-based idempotency key when one
  is omitted, so an uncertain submission can be retried safely. Explicit keys
  remain supported, and `create_batch()` preserves the advanced generic
  `/v1/batches` contract.
- Typed `BatchFile`, `BatchRequestCounts`, `BatchJob`, `BatchItemError`,
  `BatchResultItem`, and `BatchResultsPage` models, all exported at package
  level and retaining raw response payloads.

### Changed
- Package version is now 0.5.0. Existing `check_prompt()`, `check_media()`, and
  the deprecated `test_prompt()` alias retain their 0.4.1 signatures and wire
  behavior.
- The simplest batch call is now
  `client.check_prompt_batch(["first", "second"])`; endpoint and completion
  window are implicit on convenience routes.

### Validation
- Inline submissions enforce the 1,000-request/10 MiB limits; batch JSONL
  uploads enforce 50,000 lines/200 MiB.
- The SDK rejects missing or duplicate custom IDs, endpoint/body mismatches,
  mutually exclusive inline/file forms, unsupported batch base64 media, an
  invalid completion window, and known invalid cancel/delete state
  transitions before the corresponding network request.

## [0.4.1] - 2026-07-03

Packaging/metadata polish and small robustness fixes. No API changes.

### Changed
- PyPI metadata: search-friendly summary, expanded keywords, and a fuller
  classifier set (MIT license, AI and security topics).
- README: added a Python-versions badge, clarified the intro, and switched
  relative links to absolute URLs so they work on the PyPI project page.
- Tightened the mypy configuration (`warn_unreachable`, extra error codes).

### Fixed
- Error responses without a `message` field (e.g. `{"error": true, ...}`) no
  longer produce the literal message "True"; the SDK now falls back to the
  HTTP reason phrase.
- A non-finite `Retry-After` header (e.g. `inf`) no longer crashes the retry
  sleep with `OverflowError`; it is ignored and normal backoff is used.
- Removed an unused `image` parameter from the internal media form builder.

## [0.4.0] - 2026-07-03

Complete rework of the SDK around the real Guardrails API. Releases prior to
0.4.0 (0.1.x-0.3.x) are deprecated: parts of their public surface fabricated
results client-side or called endpoints that cannot work with API-key
authentication, and their version metadata was inconsistent. Upgrading is
strongly recommended.

### Added
- `AsyncAetherLabClient`: first-class async support (httpx).
- `check_prompt()`: prompt guardrail checks via `POST /v1/guardrails/prompt`,
  with `whitelisted_keywords`, `blacklisted_keywords`, `reasoning_mode`,
  `risk_tolerance`, and `environment`.
- `check_media()`: media guardrail checks via `POST /v1/guardrails/media`
  (multipart), supporting file/URL/base64 inputs.
- Error taxonomy: `AuthenticationError`, `RateLimitError` (with
  `retry_after`), `MissingPolicyError`, `InvalidRequestError`, `APIError`,
  `APIConnectionError` - all subclasses of `AetherLabError`.
- Automatic retries with exponential backoff and jitter for connection
  errors, 429, and 5xx responses; honours `Retry-After`.
- `ComplianceResult` / `MediaComplianceResult` now expose every field the API
  returns (`compliance_status`, `avg_threat_level`, `confidence`,
  `rationale`) plus `raw` with the full response body. Nothing is invented
  client-side.
- Typed package (`py.typed`), `src/` layout, single-sourced version
  (`aetherlab.__version__` matches the installed distribution and the
  User-Agent header).

### Changed
- The default base URL is `https://api.aetherlab.co`, overridable with
  `AETHERLAB_BASE_URL`.
- `test_prompt()` is now a thin deprecated alias of `check_prompt()` and
  emits a `DeprecationWarning`.
- Requires Python 3.9+. The only runtime dependency is `httpx`.

### Removed
- `validate_content()`: it generated "violations" and "suggested revisions"
  client-side from hardcoded templates instead of the API.
- `get_usage_stats()`: it returned hardcoded zeros.
- `get_logs()` / `get_audit_logs()`: the logs endpoint requires dashboard
  (JWT) authentication and can never work with an API key.
- `analyze_media()`: replaced by `check_media()`.
- Committed API keys and fabricated documentation/examples were removed from
  the repository.

## [0.3.1] and earlier

Deprecated. These releases shipped inconsistent version metadata
(`__version__` 0.1.2, package metadata 0.3.1, User-Agent 0.3.0) and the
fabricated behaviors described above. Their changelog entries have been
removed because their dates and claims were not reliable.
