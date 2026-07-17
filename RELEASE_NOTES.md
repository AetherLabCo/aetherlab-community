# AetherLab Python SDK 0.5.2

Version 0.5.2 is a MediaGuard compatibility patch for the scalar Python
clients and the end-to-end SDK notebook.

## Fixed

- `AetherLabClient.check_media()` and
  `AsyncAetherLabClient.check_media()` now accept `industry="nsfw"` or
  `industry="scam"` and forward the selected preset in the multipart request.
  Published 0.5.1 did not expose or serialize this production API field.
- The notebook's scalar MediaGuard example now defines the editable
  `MEDIA_TEST_URL` beside the call, passes that variable to `check_media()`,
  and keeps `media_result = None` separate for the returned verdict. This
  prevents an assigned URL from being ignored and then overwritten.
- The public notebook remains saved in safe mode with a benign URL, empty
  outputs, and no credentials or local filesystem paths.

## Compatibility

The `industry` argument is additive and optional. Existing keyword-based
MediaGuard calls, PromptGuard calls, batch helpers, models, exception mapping,
retry behavior, `https://api.aetherlab.co`, and `x-api-key` authentication are
unchanged.

## Validation

- Unit tests, Ruff, mypy, wheel/sdist builds, and Twine metadata checks pass.
- Sync and async multipart regression tests verify that `industry` is sent.
- Safe-mode notebook execution performs no production calls.
- An editable 0.5.2 production canary using `industry="nsfw"` completed with a
  Compliant verdict and threat level 0.
