"""Synchronous and asynchronous clients for the AetherLab Guardrails API."""

from __future__ import annotations

import asyncio
import os
import time
import warnings
from types import TracebackType
from typing import Any

import httpx

from ._http import (
    DEFAULT_BASE_URL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_TIMEOUT,
    FileSource,
    KeywordList,
    backoff_delay,
    build_media_form,
    build_prompt_payload,
    coerce_file,
    form_to_multipart,
    merge_timeout,
    parse_json_response,
    parse_retry_after,
    raise_for_response,
    should_retry_response,
)
from ._version import __version__
from .exceptions import APIConnectionError, AuthenticationError
from .models import ComplianceResult, MediaComplianceResult

__all__ = ["AetherLabClient", "AsyncAetherLabClient"]

_MEDIA_INPUT_TYPES = ("file", "url", "base64")


def _resolve_api_key(api_key: str | None) -> str:
    key = api_key or os.environ.get("AETHERLAB_API_KEY")
    if not key:
        raise AuthenticationError(
            "No API key provided. Pass api_key=... or set the AETHERLAB_API_KEY "
            "environment variable. You can create a key at https://app.aetherlab.co."
        )
    return key


def _resolve_base_url(base_url: str | None) -> str:
    return (base_url or os.environ.get("AETHERLAB_BASE_URL") or DEFAULT_BASE_URL).rstrip("/")


def _default_headers(api_key: str) -> dict[str, str]:
    return {
        "x-api-key": api_key,
        "User-Agent": f"aetherlab-python/{__version__}",
    }


def _media_parts(
    file: FileSource | None,
    *,
    input_type: str,
    form: dict[str, Any],
) -> dict[str, Any]:
    """Build httpx request kwargs for a media/multipart request."""
    if input_type not in _MEDIA_INPUT_TYPES:
        raise ValueError(
            f"input_type must be one of {', '.join(_MEDIA_INPUT_TYPES)!r}, got {input_type!r}"
        )
    if file is None:
        raise ValueError("file is required (a path, bytes, file object, URL, or base64 string)")
    if input_type == "file":
        return {"data": form, "files": {"file": coerce_file(file)}}
    if not isinstance(file, str):
        raise TypeError(
            f"file must be a string (the image URL or base64 payload) when "
            f"input_type={input_type!r}"
        )
    return {"files": form_to_multipart({**form, "image": file})}


class AetherLabClient:
    """Synchronous client for the AetherLab Guardrails API.

    Args:
        api_key: AetherLab API key. Falls back to the ``AETHERLAB_API_KEY``
            environment variable.
        base_url: API base URL. Falls back to ``AETHERLAB_BASE_URL``, then to
            ``https://api.aetherlab.co``.
        timeout: Default request timeout in seconds (default 30).
        max_retries: Maximum number of retries for connection errors, 429s,
            and 5xx responses (default 3). Retries use exponential backoff
            with jitter and honour ``Retry-After``.

    Example:
        >>> from aetherlab import AetherLabClient
        >>> client = AetherLabClient()  # reads AETHERLAB_API_KEY
        >>> result = client.check_prompt(
        ...     "Hello, how can I help you today?",
        ...     blacklisted_keywords=["violence", "weapons"],
        ... )
        >>> result.is_compliant
        True
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self.api_key = _resolve_api_key(api_key)
        self.base_url = _resolve_base_url(base_url)
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=_default_headers(self.api_key),
            timeout=timeout,
        )

    # -- lifecycle ---------------------------------------------------------

    def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        self._client.close()

    def __enter__(self) -> AetherLabClient:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    # -- transport ---------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        request_timeout = merge_timeout(timeout, self.timeout)
        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.request(
                    method,
                    path,
                    json=json,
                    data=data,
                    files=files,
                    timeout=request_timeout,
                )
            except httpx.TransportError as exc:
                if attempt >= self.max_retries:
                    raise APIConnectionError(
                        f"Could not reach the AetherLab API after "
                        f"{self.max_retries + 1} attempts: {exc}"
                    ) from exc
                time.sleep(backoff_delay(attempt + 1))
                continue
            if should_retry_response(response) and attempt < self.max_retries:
                retry_after = parse_retry_after(response.headers.get("Retry-After"))
                time.sleep(backoff_delay(attempt + 1, retry_after))
                continue
            raise_for_response(response)
            return parse_json_response(response)
        raise AssertionError("unreachable")  # pragma: no cover

    # -- API methods -------------------------------------------------------

    def check_prompt(
        self,
        prompt: str,
        *,
        whitelisted_keywords: KeywordList = None,
        blacklisted_keywords: KeywordList = None,
        reasoning_mode: str = "low",
        risk_tolerance: str | None = None,
        environment: str = "production",
        timeout: float | None = None,
    ) -> ComplianceResult:
        """Check a text prompt against your guardrail policies.

        Calls ``POST /v1/guardrails/prompt``. The API requires at least one
        policy: configure one in Policy Controls (https://app.aetherlab.co) or
        pass ``whitelisted_keywords`` / ``blacklisted_keywords`` here,
        otherwise the API rejects the request with
        :class:`~aetherlab.exceptions.MissingPolicyError`.

        Args:
            prompt: The text to check.
            whitelisted_keywords: Topics/keywords that are allowed.
            blacklisted_keywords: Topics/keywords that are not allowed.
            reasoning_mode: Reasoning effort: ``"low"``, ``"medium"``, or
                ``"high"`` (default ``"low"``).
            risk_tolerance: Optional risk tolerance: ``"low"``, ``"medium"``,
                or ``"high"``.
            environment: Environment tag for the request (default
                ``"production"``).
            timeout: Per-request timeout in seconds; defaults to the client's
                timeout.

        Returns:
            :class:`~aetherlab.models.ComplianceResult` with the verdict
            exactly as returned by the API.
        """
        payload = build_prompt_payload(
            prompt,
            whitelisted_keywords=whitelisted_keywords,
            blacklisted_keywords=blacklisted_keywords,
            reasoning_mode=reasoning_mode,
            risk_tolerance=risk_tolerance,
            environment=environment,
        )
        response = self._request(
            "POST", "/v1/guardrails/prompt", json=payload, timeout=timeout
        )
        return ComplianceResult.from_response(response)

    def check_media(
        self,
        file: FileSource,
        *,
        input_type: str,
        output_type: str = "json",
        whitelisted_keywords: KeywordList = None,
        blacklisted_keywords: KeywordList = None,
        reasoning_mode: str | None = None,
        risk_tolerance: str | None = None,
        environment: str | None = None,
        timeout: float | None = None,
    ) -> MediaComplianceResult:
        """Check an image against your guardrail policies.

        Calls ``POST /v1/guardrails/media`` (multipart). Like
        :meth:`check_prompt`, the API requires at least one policy.

        Args:
            file: The media to check. With ``input_type="file"`` this is a
                file path, ``bytes``, or a binary file object. With
                ``input_type="url"`` it is the image URL, and with
                ``input_type="base64"`` the base64-encoded image string.
            input_type: ``"file"``, ``"url"``, or ``"base64"``.
            output_type: Response format; the SDK supports ``"json"``
                (default).
            whitelisted_keywords: Content descriptions that are allowed.
            blacklisted_keywords: Content descriptions that are not allowed.
            reasoning_mode: Optional reasoning effort (``"low"``/``"medium"``/
                ``"high"``).
            risk_tolerance: Optional risk tolerance (``"low"``/``"medium"``/
                ``"high"``).
            environment: Optional environment tag.
            timeout: Per-request timeout in seconds; defaults to the client's
                timeout.

        Returns:
            :class:`~aetherlab.models.MediaComplianceResult` with the verdict
            exactly as returned by the API.
        """
        form = build_media_form(
            input_type=input_type,
            output_type=output_type,
            whitelisted_keywords=whitelisted_keywords,
            blacklisted_keywords=blacklisted_keywords,
            reasoning_mode=reasoning_mode,
            risk_tolerance=risk_tolerance,
            environment=environment,
        )
        parts = _media_parts(file, input_type=input_type, form=form)
        response = self._request(
            "POST", "/v1/guardrails/media", timeout=timeout, **parts
        )
        return MediaComplianceResult.from_response(response)

    # -- deprecated aliases --------------------------------------------------

    def test_prompt(
        self,
        user_prompt: str,
        whitelisted_keywords: KeywordList = None,
        blacklisted_keywords: KeywordList = None,
        **kwargs: Any,
    ) -> ComplianceResult:
        """Deprecated alias for :meth:`check_prompt` (kept for 0.3.x code)."""
        warnings.warn(
            "AetherLabClient.test_prompt() is deprecated; use check_prompt() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.check_prompt(
            user_prompt,
            whitelisted_keywords=whitelisted_keywords,
            blacklisted_keywords=blacklisted_keywords,
            **kwargs,
        )


class AsyncAetherLabClient:
    """Asynchronous client for the AetherLab Guardrails API.

    Mirrors :class:`AetherLabClient` with ``async``/``await`` semantics.

    Example:
        >>> from aetherlab import AsyncAetherLabClient
        >>> async with AsyncAetherLabClient() as client:
        ...     result = await client.check_prompt(
        ...         "Hello!", blacklisted_keywords=["violence"]
        ...     )
    """

    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ) -> None:
        self.api_key = _resolve_api_key(api_key)
        self.base_url = _resolve_base_url(base_url)
        self.timeout = timeout
        self.max_retries = max_retries
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=_default_headers(self.api_key),
            timeout=timeout,
        )

    # -- lifecycle ---------------------------------------------------------

    async def close(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncAetherLabClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.close()

    # -- transport ---------------------------------------------------------

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        request_timeout = merge_timeout(timeout, self.timeout)
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.request(
                    method,
                    path,
                    json=json,
                    data=data,
                    files=files,
                    timeout=request_timeout,
                )
            except httpx.TransportError as exc:
                if attempt >= self.max_retries:
                    raise APIConnectionError(
                        f"Could not reach the AetherLab API after "
                        f"{self.max_retries + 1} attempts: {exc}"
                    ) from exc
                await asyncio.sleep(backoff_delay(attempt + 1))
                continue
            if should_retry_response(response) and attempt < self.max_retries:
                retry_after = parse_retry_after(response.headers.get("Retry-After"))
                await asyncio.sleep(backoff_delay(attempt + 1, retry_after))
                continue
            raise_for_response(response)
            return parse_json_response(response)
        raise AssertionError("unreachable")  # pragma: no cover

    # -- API methods -------------------------------------------------------

    async def check_prompt(
        self,
        prompt: str,
        *,
        whitelisted_keywords: KeywordList = None,
        blacklisted_keywords: KeywordList = None,
        reasoning_mode: str = "low",
        risk_tolerance: str | None = None,
        environment: str = "production",
        timeout: float | None = None,
    ) -> ComplianceResult:
        """Async version of :meth:`AetherLabClient.check_prompt`."""
        payload = build_prompt_payload(
            prompt,
            whitelisted_keywords=whitelisted_keywords,
            blacklisted_keywords=blacklisted_keywords,
            reasoning_mode=reasoning_mode,
            risk_tolerance=risk_tolerance,
            environment=environment,
        )
        response = await self._request(
            "POST", "/v1/guardrails/prompt", json=payload, timeout=timeout
        )
        return ComplianceResult.from_response(response)

    async def check_media(
        self,
        file: FileSource,
        *,
        input_type: str,
        output_type: str = "json",
        whitelisted_keywords: KeywordList = None,
        blacklisted_keywords: KeywordList = None,
        reasoning_mode: str | None = None,
        risk_tolerance: str | None = None,
        environment: str | None = None,
        timeout: float | None = None,
    ) -> MediaComplianceResult:
        """Async version of :meth:`AetherLabClient.check_media`."""
        form = build_media_form(
            input_type=input_type,
            output_type=output_type,
            whitelisted_keywords=whitelisted_keywords,
            blacklisted_keywords=blacklisted_keywords,
            reasoning_mode=reasoning_mode,
            risk_tolerance=risk_tolerance,
            environment=environment,
        )
        parts = _media_parts(file, input_type=input_type, form=form)
        response = await self._request(
            "POST", "/v1/guardrails/media", timeout=timeout, **parts
        )
        return MediaComplianceResult.from_response(response)
