"""Exception types raised by the AetherLab SDK.

All exceptions inherit from :class:`AetherLabError`, so ``except AetherLabError``
catches everything this SDK raises on purpose.
"""

from __future__ import annotations

from typing import Any

__all__ = [
    "AetherLabError",
    "APIConnectionError",
    "APIError",
    "AuthenticationError",
    "InvalidRequestError",
    "MissingPolicyError",
    "RateLimitError",
]


class AetherLabError(Exception):
    """Base class for every error raised by the AetherLab SDK."""


class APIConnectionError(AetherLabError):
    """Could not reach the AetherLab API (DNS, connect, or read failure).

    Raised after all retries have been exhausted.
    """


class APIError(AetherLabError):
    """The API returned an HTTP error response.

    Attributes:
        status_code: HTTP status code of the response.
        error_code: AetherLab error code (e.g. ``"ERR_0202"``) when present.
        message: Human-readable message from the server.
        body: The parsed response body (dict) or raw text when not JSON.
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        error_code: str | None = None,
        body: Any = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.body = body

    def __str__(self) -> str:
        parts = []
        if self.status_code is not None:
            parts.append(f"HTTP {self.status_code}")
        if self.error_code:
            parts.append(self.error_code)
        prefix = " ".join(parts)
        return f"[{prefix}] {self.message}" if prefix else self.message


class AuthenticationError(APIError):
    """The API key is missing, malformed, or revoked (HTTP 401)."""


class RateLimitError(APIError):
    """Too many requests (HTTP 429).

    Attributes:
        retry_after: Seconds to wait before retrying, when the server sent a
            ``Retry-After`` header, otherwise ``None``.
    """

    def __init__(
        self,
        message: str,
        *,
        retry_after: float | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class MissingPolicyError(APIError):
    """No guardrail policy is configured (``ERR_0202``).

    The Guardrails API requires at least one policy: either configure one in
    Policy Controls (https://app.aetherlab.co) or pass ``whitelisted_keywords``
    / ``blacklisted_keywords`` with the request.
    """


class InvalidRequestError(APIError):
    """The request was malformed (``ERR_0200`` / ``ERR_0201``)."""
