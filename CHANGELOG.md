# Changelog

All notable changes to the AetherLab Python SDK are documented here.

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
