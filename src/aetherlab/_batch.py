"""Validation and payload helpers for the server-side batch API."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from typing import Any, cast

from .exceptions import APIError
from .models import (
    BatchEndpoint,
    BatchJob,
    BatchResultItem,
    BatchResultsPage,
    BatchUploadPurpose,
)

BATCH_ENDPOINTS = frozenset({"/v1/guardrails/prompt", "/v1/guardrails/media"})
BATCH_FILE_PURPOSES = frozenset({"batch", "guardrail_media"})
BATCH_TERMINAL_STATUSES = frozenset({"completed", "failed", "cancelled", "expired"})
BATCH_CANCELLABLE_STATUSES = frozenset(
    {"validating", "queued", "in_progress", "finalizing"}
)

MAX_INLINE_REQUESTS = 1_000
MAX_INLINE_BYTES = 10 * 1024 * 1024
MAX_JSONL_REQUESTS = 50_000
MAX_JSONL_BYTES = 200 * 1024 * 1024

_MEDIA_KEYS = frozenset(
    {
        "image",
        "image_url",
        "url",
        "file_id",
        "media_url",
        "media_file_id",
        "input_type",
    }
)
_BASE64_KEYS = frozenset({"base64", "image_base64", "media_base64"})


def validate_endpoint(endpoint: object) -> BatchEndpoint:
    """Validate and narrow a server-supported batch endpoint."""
    if not isinstance(endpoint, str):
        raise TypeError("endpoint must be a string")
    if endpoint not in BATCH_ENDPOINTS:
        choices = ", ".join(sorted(BATCH_ENDPOINTS))
        raise ValueError(f"endpoint must be exactly one of {choices}; got {endpoint!r}")
    return cast(BatchEndpoint, endpoint)


def validate_file_purpose(purpose: object) -> BatchUploadPurpose:
    """Validate and narrow a file purpose."""
    if not isinstance(purpose, str):
        raise TypeError("purpose must be a string")
    if purpose not in BATCH_FILE_PURPOSES:
        choices = ", ".join(sorted(BATCH_FILE_PURPOSES))
        raise ValueError(f"purpose must be one of {choices}; got {purpose!r}")
    return cast(BatchUploadPurpose, purpose)


def validate_resource_id(value: object, name: str) -> str:
    """Reject missing or path-like resource IDs before issuing a request."""
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value.strip():
        raise ValueError(f"{name} must be a non-empty string")
    if "/" in value or value in {".", ".."}:
        raise ValueError(f"{name} must not contain path separators")
    return value


def validate_idempotency_key(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("idempotency_key must be a string")
    if not value.strip():
        raise ValueError("idempotency_key must be a non-empty string")
    return value


def _json_bytes(value: Any, *, name: str) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{name} must contain only JSON-serializable values") from exc


def _https_url(value: Any, *, name: str) -> str:
    if not isinstance(value, str) or not value.startswith("https://"):
        raise ValueError(f"{name} must be an HTTPS URL")
    return value


def _media_reference(body: Mapping[str, Any]) -> tuple[str | None, str | None]:
    input_type = body.get("input_type")
    if input_type == "base64" or any(key in body for key in _BASE64_KEYS):
        raise ValueError("batch media requests do not support embedded base64")

    url_value: Any = None
    for key in ("image_url", "media_url", "url"):
        if key in body:
            url_value = body[key]
            break
    if url_value is None and input_type == "url":
        url_value = body.get("image")
    if url_value is None:
        image_value = body.get("image")
        if isinstance(image_value, str) and image_value.startswith(
            ("https://", "http://", "data:")
        ):
            url_value = image_value

    file_id_value: Any = body.get("file_id", body.get("media_file_id"))
    if input_type in {"file", "file_id"} and file_id_value is None:
        image_value = body.get("image")
        if isinstance(image_value, str) and not image_value.startswith(("http://", "https://")):
            file_id_value = image_value

    url: str | None = None
    file_id: str | None = None
    if url_value is not None:
        if isinstance(url_value, str) and url_value.startswith("data:"):
            raise ValueError("batch media requests do not support embedded base64")
        url = _https_url(url_value, name="media URL")
    if file_id_value is not None:
        file_id = validate_resource_id(file_id_value, "media file_id")
    return url, file_id


def validate_request_body(endpoint: BatchEndpoint, body: Mapping[str, Any]) -> None:
    """Catch endpoint/body mismatches and unsupported media encodings."""
    if endpoint == "/v1/guardrails/prompt":
        if any(key in body for key in _MEDIA_KEYS):
            raise ValueError("media request body does not match the prompt batch endpoint")
        if "user_prompt" not in body:
            raise ValueError("prompt batch request body requires 'user_prompt'")
        prompt = body["user_prompt"]
        if not isinstance(prompt, str) or not prompt:
            raise ValueError("'user_prompt' must be a non-empty string")
        return

    if "user_prompt" in body:
        raise ValueError("prompt request body does not match the media batch endpoint")
    url, file_id = _media_reference(body)
    if (url is None) == (file_id is None):
        raise ValueError("media batch body requires exactly one HTTPS URL or uploaded file_id")


def normalize_batch_requests(
    endpoint: BatchEndpoint,
    requests: Iterable[Mapping[str, Any]],
    *,
    inline: bool = True,
) -> list[dict[str, Any]]:
    """Materialize, validate, and copy request records."""
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, request in enumerate(requests):
        if not isinstance(request, Mapping):
            raise TypeError(f"requests[{index}] must be a mapping")
        custom_id = request.get("custom_id")
        if not isinstance(custom_id, str) or not custom_id.strip():
            raise ValueError(f"requests[{index}].custom_id must be a non-empty string")
        if custom_id in seen:
            raise ValueError(f"duplicate custom_id {custom_id!r}")
        seen.add(custom_id)

        body = request.get("body")
        if not isinstance(body, Mapping):
            raise ValueError(f"requests[{index}].body must be a mapping")
        endpoint_value = request.get("endpoint", request.get("url"))
        if endpoint_value is not None and endpoint_value != endpoint:
            raise ValueError(
                f"requests[{index}] endpoint {endpoint_value!r} does not match {endpoint!r}"
            )
        body_copy = dict(body)
        validate_request_body(endpoint, body_copy)
        normalized.append({"custom_id": custom_id, "body": body_copy})

    if not normalized:
        raise ValueError("requests must contain at least one item")
    if inline and len(normalized) > MAX_INLINE_REQUESTS:
        raise ValueError(f"inline batches are limited to {MAX_INLINE_REQUESTS} requests")
    if inline and len(_json_bytes(normalized, name="requests")) > MAX_INLINE_BYTES:
        raise ValueError(f"inline batch requests are limited to {MAX_INLINE_BYTES} bytes")
    return normalized


def build_batch_payload(
    endpoint: str,
    *,
    requests: Iterable[Mapping[str, Any]] | None,
    input_file_id: str | None,
    completion_window: str,
    metadata: Mapping[str, Any] | None,
) -> tuple[BatchEndpoint, dict[str, Any]]:
    """Validate create arguments and build the wire payload."""
    checked_endpoint = validate_endpoint(endpoint)
    if completion_window != "24h":
        raise ValueError("completion_window must be exactly '24h'")
    if (requests is None) == (input_file_id is None):
        raise ValueError("provide exactly one of requests or input_file_id")

    payload: dict[str, Any] = {
        "endpoint": checked_endpoint,
        "completion_window": "24h",
    }
    if requests is not None:
        payload["requests"] = normalize_batch_requests(checked_endpoint, requests)
    else:
        payload["input_file_id"] = validate_resource_id(
            cast(str, input_file_id),
            "input_file_id",
        )

    if metadata is not None:
        if not isinstance(metadata, Mapping):
            raise TypeError("metadata must be a mapping")
        metadata_copy = dict(metadata)
        _json_bytes(metadata_copy, name="metadata")
        payload["metadata"] = metadata_copy
    if requests is not None and len(_json_bytes(payload, name="batch payload")) > MAX_INLINE_BYTES:
        raise ValueError(f"inline batch payloads are limited to {MAX_INLINE_BYTES} bytes")
    return checked_endpoint, payload


def validate_batch_jsonl(content: bytes) -> None:
    """Validate batch JSONL count, size, shape, and duplicate IDs."""
    if not content:
        raise ValueError("batch JSONL file must not be empty")
    if len(content) > MAX_JSONL_BYTES:
        raise ValueError(f"batch JSONL files are limited to {MAX_JSONL_BYTES} bytes")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("batch JSONL file must be UTF-8 encoded") from exc

    count = 0
    seen: set[str] = set()
    for line_number, line in enumerate(text.splitlines(), 1):
        if not line.strip():
            continue
        count += 1
        if count > MAX_JSONL_REQUESTS:
            raise ValueError(f"batch JSONL files are limited to {MAX_JSONL_REQUESTS} requests")
        try:
            request = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON on batch file line {line_number}") from exc
        if not isinstance(request, dict):
            raise ValueError(f"batch file line {line_number} must be a JSON object")
        custom_id = request.get("custom_id")
        if not isinstance(custom_id, str) or not custom_id.strip():
            raise ValueError(
                f"batch file line {line_number} requires a non-empty custom_id"
            )
        if custom_id in seen:
            raise ValueError(f"duplicate custom_id {custom_id!r} in batch file")
        seen.add(custom_id)
        body = request.get("body")
        if not isinstance(body, dict):
            raise ValueError(f"batch file line {line_number} requires an object body")
        image_value = body.get("image")
        if (
            body.get("input_type") == "base64"
            or any(key in body for key in _BASE64_KEYS)
            or (isinstance(image_value, str) and image_value.startswith("data:"))
        ):
            raise ValueError(
                f"batch file line {line_number} uses unsupported embedded base64 media"
            )
        media_urls = [
            body.get(key) for key in ("image_url", "media_url", "url")
        ]
        if body.get("input_type") == "url":
            media_urls.append(image_value)
        if any(
            isinstance(value, str) and value.startswith("http://")
            for value in media_urls
        ):
            raise ValueError(
                f"batch file line {line_number} uses a non-HTTPS media URL"
            )
    if count == 0:
        raise ValueError("batch JSONL file must contain at least one request")


def _stable_custom_id(prefix: str, body: Mapping[str, Any], index: int) -> str:
    digest = hashlib.sha256(_json_bytes(body, name="batch item body")).hexdigest()[:12]
    return f"{prefix}-{index:06d}-{digest}"


def _item_parts(
    item: str | Mapping[str, Any],
    *,
    index: int,
    kind: str,
) -> tuple[str | None, dict[str, Any]]:
    if isinstance(item, str):
        if kind == "prompt":
            return None, {"user_prompt": item}
        if item.startswith(("https://", "http://")):
            return None, {"input_type": "url", "image": item}
        return None, {"input_type": "file", "file_id": item}
    if not isinstance(item, Mapping):
        raise TypeError(f"{kind} batch item {index} must be a string or mapping")
    custom_id_value = item.get("custom_id")
    if custom_id_value is not None and (
        not isinstance(custom_id_value, str) or not custom_id_value.strip()
    ):
        raise ValueError(f"{kind} batch item {index} custom_id must be non-empty")
    custom_id = custom_id_value
    nested_body = item.get("body")
    if nested_body is not None:
        if not isinstance(nested_body, Mapping):
            raise ValueError(f"{kind} batch item {index} body must be a mapping")
        body = dict(nested_body)
    else:
        body = {key: value for key, value in item.items() if key != "custom_id"}
    return custom_id, body


def build_prompt_batch_requests(
    items: Iterable[str | Mapping[str, Any]],
    *,
    defaults: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if isinstance(items, (str, bytes)):
        raise TypeError("prompts must be an iterable of batch items, not one string")
    requests: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        custom_id, item_body = _item_parts(item, index=index, kind="prompt")
        if "prompt" in item_body and "user_prompt" not in item_body:
            item_body["user_prompt"] = item_body.pop("prompt")
        body = {**defaults, **item_body}
        requests.append(
            {
                "custom_id": custom_id or _stable_custom_id("prompt", body, index),
                "body": body,
            }
        )
    return requests


def build_media_batch_requests(
    items: Iterable[str | Mapping[str, Any]],
    *,
    defaults: Mapping[str, Any],
) -> list[dict[str, Any]]:
    if isinstance(items, (str, bytes)):
        raise TypeError("media must be an iterable of batch items, not one string")
    requests: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        custom_id, item_body = _item_parts(item, index=index, kind="media")
        if "url" in item_body and not any(
            key in item_body for key in ("image", "image_url", "media_url")
        ):
            item_body["input_type"] = "url"
            item_body["image"] = item_body.pop("url")
        elif "image_url" in item_body and "input_type" not in item_body:
            item_body["input_type"] = "url"
        elif "file_id" in item_body and "input_type" not in item_body:
            item_body["input_type"] = "file"
        body = {**defaults, **item_body}
        requests.append(
            {
                "custom_id": custom_id or _stable_custom_id("media", body, index),
                "body": body,
            }
        )
    return requests


def parse_batch_list(response: dict[str, Any]) -> list[BatchJob]:
    """Parse tolerated list envelopes into strict job models."""
    value: Any = response.get("data", response.get("batches", response.get("items")))
    if isinstance(value, dict):
        value = value.get("items", value.get("batches", value.get("data")))
    if not isinstance(value, list):
        raise ValueError("batch list response does not contain a list")
    jobs: list[BatchJob] = []
    for item in value:
        if not isinstance(item, dict):
            raise ValueError("each listed batch must be an object")
        jobs.append(BatchJob.from_response(item))
    return jobs


def parse_results_page(
    response: dict[str, Any],
    *,
    endpoint: BatchEndpoint | None,
) -> BatchResultsPage:
    return BatchResultsPage.from_response(response, endpoint=endpoint)


def parse_ndjson_results(
    content: bytes,
    *,
    endpoint: BatchEndpoint | None,
) -> list[BatchResultItem]:
    """Parse an NDJSON result download without losing each raw item."""
    results: list[BatchResultItem] = []
    for line_number, line in enumerate(content.splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise APIError(
                f"API returned invalid NDJSON on line {line_number}",
                body=line.decode("utf-8", errors="replace"),
            ) from exc
        if not isinstance(value, dict):
            raise APIError(
                f"API returned a non-object NDJSON item on line {line_number}",
                body=value,
            )
        try:
            results.append(BatchResultItem.from_response(value, endpoint=endpoint))
        except ValueError as exc:
            raise APIError(
                f"API returned an invalid batch result on NDJSON line {line_number}: {exc}",
                body=value,
            ) from exc
    return results
