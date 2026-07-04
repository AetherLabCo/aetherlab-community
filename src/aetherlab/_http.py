"""Internal HTTP plumbing shared by the sync and async clients.

Nothing in this module is part of the public API.
"""

from __future__ import annotations

import email.utils
import math
import os
import random
import time
from collections.abc import Iterable
from typing import Any, Optional, Union

import httpx

from .exceptions import (
    APIError,
    AuthenticationError,
    InvalidRequestError,
    MissingPolicyError,
    RateLimitError,
)

DEFAULT_BASE_URL = "https://api.aetherlab.co"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3

# Exponential backoff parameters (seconds).
BACKOFF_BASE = 0.5
BACKOFF_CAP = 8.0

RETRYABLE_STATUS_CODES = frozenset({429, 500, 502, 503, 504})

KeywordList = Optional[Iterable[str]]


def join_keywords(keywords: KeywordList) -> str | None:
    """Comma-join a keyword list into the wire format the API expects."""
    if keywords is None:
        return None
    if isinstance(keywords, str):
        return keywords
    joined = ",".join(str(k).strip() for k in keywords if str(k).strip())
    return joined or None


def build_prompt_payload(
    prompt: str,
    *,
    whitelisted_keywords: KeywordList = None,
    blacklisted_keywords: KeywordList = None,
    reasoning_mode: str | None = "low",
    risk_tolerance: str | None = None,
    environment: str | None = "production",
) -> dict[str, Any]:
    payload: dict[str, Any] = {"user_prompt": prompt}
    whitelist = join_keywords(whitelisted_keywords)
    blacklist = join_keywords(blacklisted_keywords)
    if whitelist is not None:
        payload["whitelisted_keyword"] = whitelist
    if blacklist is not None:
        payload["blacklisted_keyword"] = blacklist
    if reasoning_mode is not None:
        payload["reasoning_mode"] = reasoning_mode
    if risk_tolerance is not None:
        payload["risk_tolerance"] = risk_tolerance
    if environment is not None:
        payload["environment"] = environment
    return payload


def build_media_form(
    *,
    input_type: str,
    output_type: str = "json",
    whitelisted_keywords: KeywordList = None,
    blacklisted_keywords: KeywordList = None,
    reasoning_mode: str | None = None,
    risk_tolerance: str | None = None,
    environment: str | None = None,
) -> dict[str, Any]:
    form: dict[str, Any] = {"input_type": input_type, "output_type": output_type}
    whitelist = join_keywords(whitelisted_keywords)
    blacklist = join_keywords(blacklisted_keywords)
    if whitelist is not None:
        form["whitelisted_keyword"] = whitelist
    if blacklist is not None:
        form["blacklisted_keyword"] = blacklist
    if reasoning_mode is not None:
        form["reasoning_mode"] = reasoning_mode
    if risk_tolerance is not None:
        form["risk_tolerance"] = risk_tolerance
    if environment is not None:
        form["environment"] = environment
    return form


def parse_retry_after(value: str | None) -> float | None:
    """Parse a ``Retry-After`` header (seconds or HTTP-date) into seconds."""
    if not value:
        return None
    try:
        seconds = float(value)
    except ValueError:
        pass
    else:
        # Reject inf/nan: time.sleep(inf) raises OverflowError.
        return max(0.0, seconds) if math.isfinite(seconds) else None
    try:
        # Raises TypeError (3.9) or ValueError (3.10+) for unparseable dates.
        when = email.utils.parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    delta = when.timestamp() - time.time()
    return max(0.0, delta)


def backoff_delay(retry_number: int, retry_after: float | None = None) -> float:
    """Delay before retry ``retry_number`` (1-based), honouring ``Retry-After``."""
    exp = min(BACKOFF_CAP, BACKOFF_BASE * (2 ** (retry_number - 1)))
    delay = random.uniform(0, exp)
    if retry_after is not None:
        delay = max(delay, retry_after)
    return delay


def should_retry_response(response: httpx.Response) -> bool:
    return response.status_code in RETRYABLE_STATUS_CODES


def _extract_error(body: Any, response: httpx.Response) -> tuple[str | None, str]:
    """Pull (error_code, message) out of an error response body."""
    if isinstance(body, dict):
        error_code = body.get("error_code")
        message = body.get("message") or body.get("error")
        if not (isinstance(message, str) and message.strip()):
            # e.g. {"error": true} without a message: fall back to the HTTP
            # reason phrase instead of the string "True".
            message = response.reason_phrase or f"HTTP {response.status_code}"
        return (
            str(error_code) if error_code is not None else None,
            message,
        )
    text = response.text.strip()
    return None, text or response.reason_phrase or f"HTTP {response.status_code}"


def raise_for_response(response: httpx.Response) -> None:
    """Map a non-2xx response onto the SDK exception taxonomy."""
    if response.is_success:
        return

    body: Any
    try:
        body = response.json()
    except ValueError:
        body = response.text

    error_code, message = _extract_error(body, response)
    status = response.status_code
    kwargs: dict[str, Any] = {
        "status_code": status,
        "error_code": error_code,
        "body": body,
    }

    if status == 401:
        raise AuthenticationError(message, **kwargs)
    if status == 429:
        retry_after = parse_retry_after(response.headers.get("Retry-After"))
        raise RateLimitError(message, retry_after=retry_after, **kwargs)
    if error_code == "ERR_0202":
        raise MissingPolicyError(message, **kwargs)
    if error_code in ("ERR_0200", "ERR_0201"):
        raise InvalidRequestError(message, **kwargs)
    raise APIError(message, **kwargs)


def parse_json_response(response: httpx.Response) -> dict[str, Any]:
    try:
        parsed = response.json()
    except ValueError as exc:
        raise APIError(
            "API returned a non-JSON response",
            status_code=response.status_code,
            body=response.text,
        ) from exc
    if not isinstance(parsed, dict):
        raise APIError(
            "API returned an unexpected JSON payload",
            status_code=response.status_code,
            body=parsed,
        )
    return parsed


FileSource = Union[str, bytes, Any]


def coerce_file(file: FileSource) -> tuple[str, bytes]:
    """Turn ``file`` (path, bytes, or file-like object) into a multipart tuple.

    The content is fully read into memory so the request body can be rebuilt
    when a request is retried.
    """
    if isinstance(file, bytes):
        return ("upload", file)
    if isinstance(file, str):
        with open(file, "rb") as handle:
            return (os.path.basename(file) or "upload", handle.read())
    content = file.read()
    if isinstance(content, str):
        content = content.encode("utf-8")
    name = getattr(file, "name", None)
    if isinstance(name, str) and name:
        return (os.path.basename(name), content)
    return ("upload", content)


def form_to_multipart(form: dict[str, Any]) -> dict[str, tuple[None, str]]:
    """Encode plain form fields as multipart parts (forces multipart/form-data)."""
    return {key: (None, str(value)) for key, value in form.items()}


def merge_timeout(
    per_request: float | None, default: float | httpx.Timeout
) -> float | httpx.Timeout:
    return per_request if per_request is not None else default
