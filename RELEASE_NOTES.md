# AetherLab Python SDK 0.5.1

Version 0.5.1 is a compatibility patch for the server-side batch helpers
introduced in 0.5.0.

## Fixed

- Mapped `check_prompt_batch()` items now accept all documented prompt source
  names: `input`, `prompt`, and `user_prompt`.
- Ambiguous mapped items that provide more than one prompt source fail
  locally before any request is sent.
- Plain-string prompt batches, media batches, scalar methods, JSONL resource
  methods, polling, and typed results remain unchanged.

## Compatibility

`check_prompt()`, `check_media()`, `test_prompt()`, existing models, exception
mapping, retry behavior, `https://api.aetherlab.co`, and `x-api-key`
authentication are unchanged. Version 0.5.1 is a drop-in replacement for
0.5.0.

## Validation

- Unit, lint, type, and distribution builds pass across Python 3.9–3.13.
- A production canary using the documented mapped `input` form completed
  successfully.
