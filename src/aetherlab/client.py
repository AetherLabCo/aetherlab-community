"""Synchronous and asynchronous clients for the AetherLab Guardrails API."""

from __future__ import annotations

import asyncio
import math
import os
import time
import warnings
from collections.abc import AsyncIterator, Iterable, Iterator, Mapping
from threading import Event
from types import TracebackType
from typing import Any, Literal

import httpx

from ._batch import (
    BATCH_CANCELLABLE_STATUSES,
    BATCH_TERMINAL_STATUSES,
    build_batch_payload,
    build_media_batch_requests,
    build_prompt_batch_requests,
    parse_batch_list,
    parse_ndjson_results,
    parse_results_page,
    validate_batch_jsonl,
    validate_file_purpose,
    validate_idempotency_key,
    validate_resource_id,
)
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
from .models import (
    BatchEndpoint,
    BatchFile,
    BatchJob,
    BatchResultItem,
    BatchResultsPage,
    BatchStatus,
    BatchUploadPurpose,
    ComplianceResult,
    MediaComplianceResult,
)

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


def _prompt_batch_defaults(
    *,
    defaults: Mapping[str, Any] | None,
    whitelisted_keywords: KeywordList,
    blacklisted_keywords: KeywordList,
    reasoning_mode: str | None,
    risk_tolerance: str | None,
    environment: str | None,
) -> dict[str, Any]:
    shared = build_prompt_payload(
        "",
        whitelisted_keywords=whitelisted_keywords,
        blacklisted_keywords=blacklisted_keywords,
        reasoning_mode=reasoning_mode,
        risk_tolerance=risk_tolerance,
        environment=environment,
    )
    shared.pop("user_prompt")
    if defaults is not None:
        shared.update(defaults)
    # Batch environment is selected by the x-api-key, not an item body field.
    shared.pop("environment", None)
    return shared


def _media_batch_defaults(
    *,
    defaults: Mapping[str, Any] | None,
    output_type: str,
    whitelisted_keywords: KeywordList,
    blacklisted_keywords: KeywordList,
    reasoning_mode: str | None,
    risk_tolerance: str | None,
    environment: str | None,
) -> dict[str, Any]:
    shared = build_media_form(
        input_type="url",
        output_type=output_type,
        whitelisted_keywords=whitelisted_keywords,
        blacklisted_keywords=blacklisted_keywords,
        reasoning_mode=reasoning_mode,
        risk_tolerance=risk_tolerance,
        environment=environment,
    )
    shared.pop("input_type")
    if defaults is not None:
        shared.update(defaults)
    # Batch items return compliance decisions only. Environment comes from
    # x-api-key and output_type is a scalar MediaGuard compatibility field.
    shared.pop("environment", None)
    shared.pop("output_type", None)
    return shared


def _validate_wait_arguments(
    *,
    timeout: float,
    poll_interval: float,
    max_poll_interval: float,
    poll_backoff: float,
) -> None:
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("timeout must be finite and greater than zero")
    if not math.isfinite(poll_interval) or poll_interval <= 0:
        raise ValueError("poll_interval must be finite and greater than zero")
    if not math.isfinite(max_poll_interval) or max_poll_interval < poll_interval:
        raise ValueError("max_poll_interval must be at least poll_interval")
    if not math.isfinite(poll_backoff) or poll_backoff < 1:
        raise ValueError("poll_backoff must be at least 1")


def _validate_cursor(value: object, name: str = "after") -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value:
        raise ValueError(f"{name} must be a non-empty cursor")
    return value


def _select_batch_items(
    primary: Iterable[str | Mapping[str, Any]] | None,
    *,
    requests: Iterable[str | Mapping[str, Any]] | None,
    items: Iterable[str | Mapping[str, Any]] | None,
    primary_name: str,
) -> Iterable[str | Mapping[str, Any]]:
    supplied = sum(value is not None for value in (primary, requests, items))
    if supplied != 1:
        raise ValueError(
            f"provide exactly one of {primary_name}, requests, or items"
        )
    if primary is not None:
        return primary
    if requests is not None:
        return requests
    assert items is not None
    return items


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
        self._batch_jobs: dict[str, BatchJob] = {}
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

    def _request_response(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        request_timeout = merge_timeout(timeout, self.timeout)
        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.request(
                    method,
                    path,
                    json=json,
                    data=data,
                    files=files,
                    params=params,
                    headers=headers,
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
            return response
        raise AssertionError("unreachable")  # pragma: no cover

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        response = self._request_response(
            method,
            path,
            json=json,
            data=data,
            files=files,
            params=params,
            headers=headers,
            timeout=timeout,
        )
        return parse_json_response(response)

    def _request_bytes(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> bytes:
        return self._request_response(
            method,
            path,
            headers=headers,
            timeout=timeout,
        ).content

    def _request_no_content(
        self,
        method: str,
        path: str,
        *,
        timeout: float | None = None,
    ) -> None:
        self._request_response(method, path, timeout=timeout)

    def _iter_ndjson_lines(
        self,
        path: str,
        *,
        timeout: float | None = None,
    ) -> Iterator[bytes]:
        request_timeout = merge_timeout(timeout, self.timeout)
        yielded = False
        for attempt in range(self.max_retries + 1):
            try:
                with self._client.stream(
                    "GET",
                    path,
                    headers={"Accept": "application/x-ndjson"},
                    timeout=request_timeout,
                ) as response:
                    if should_retry_response(response) and attempt < self.max_retries:
                        retry_after = parse_retry_after(
                            response.headers.get("Retry-After")
                        )
                        time.sleep(backoff_delay(attempt + 1, retry_after))
                        continue
                    raise_for_response(response)
                    for line in response.iter_lines():
                        if line.strip():
                            yielded = True
                            yield line.encode("utf-8")
                return
            except httpx.TransportError as exc:
                if yielded or attempt >= self.max_retries:
                    raise APIConnectionError(
                        f"Batch result stream ended before completion: {exc}"
                    ) from exc
                time.sleep(backoff_delay(attempt + 1))
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

    # -- files and server-side batches ------------------------------------

    def _remember_batch(self, job: BatchJob) -> BatchJob:
        self._batch_jobs[job.id] = job
        return job

    def _batch_reference(self, batch: str | BatchJob) -> tuple[str, BatchJob | None]:
        if isinstance(batch, BatchJob):
            batch_id = validate_resource_id(batch.id, "batch_id")
            self._batch_jobs[batch_id] = batch
            return batch_id, batch
        batch_id = validate_resource_id(batch, "batch_id")
        return batch_id, None

    def upload_file(
        self,
        file: FileSource,
        *,
        purpose: BatchUploadPurpose,
        timeout: float | None = None,
    ) -> BatchFile:
        """Upload a JSONL batch input or media file to ``POST /v1/files``."""
        checked_purpose = validate_file_purpose(purpose)
        filename, content = coerce_file(file)
        if not content:
            raise ValueError("file must not be empty")
        if checked_purpose == "batch":
            validate_batch_jsonl(content)
        response = self._request(
            "POST",
            "/v1/files",
            data={"purpose": checked_purpose},
            files={"file": (filename, content)},
            timeout=timeout,
        )
        return BatchFile.from_response(response)

    def retrieve_file(
        self,
        file_id: str,
        *,
        timeout: float | None = None,
    ) -> BatchFile:
        """Retrieve file metadata from ``GET /v1/files/{id}``."""
        checked_id = validate_resource_id(file_id, "file_id")
        response = self._request("GET", f"/v1/files/{checked_id}", timeout=timeout)
        return BatchFile.from_response(response)

    def delete_file(
        self,
        file_id: str,
        *,
        timeout: float | None = None,
    ) -> None:
        """Delete a stored file."""
        checked_id = validate_resource_id(file_id, "file_id")
        self._request_no_content("DELETE", f"/v1/files/{checked_id}", timeout=timeout)

    def create_batch(
        self,
        endpoint: BatchEndpoint,
        *,
        idempotency_key: str,
        requests: Iterable[Mapping[str, Any]] | None = None,
        input_file_id: str | None = None,
        completion_window: Literal["24h"] = "24h",
        metadata: Mapping[str, Any] | None = None,
        timeout: float | None = None,
    ) -> BatchJob:
        """Create a server-side prompt or media batch.

        Exactly one of ``requests`` and ``input_file_id`` is required.
        """
        key = validate_idempotency_key(idempotency_key)
        _checked_endpoint, payload = build_batch_payload(
            endpoint,
            requests=requests,
            input_file_id=input_file_id,
            completion_window=completion_window,
            metadata=metadata,
        )
        response = self._request(
            "POST",
            "/v1/batches",
            json=payload,
            headers={"Idempotency-Key": key},
            timeout=timeout,
        )
        return self._remember_batch(BatchJob.from_response(response))

    def list_batches(
        self,
        *,
        limit: int | None = None,
        after: str | None = None,
        status: BatchStatus | None = None,
        timeout: float | None = None,
    ) -> list[BatchJob]:
        """List batch jobs from ``GET /v1/batches``."""
        params: dict[str, Any] = {}
        if limit is not None:
            if limit <= 0:
                raise ValueError("limit must be greater than zero")
            params["limit"] = limit
        if after is not None:
            params["after"] = _validate_cursor(after)
        if status is not None:
            allowed = BATCH_TERMINAL_STATUSES | BATCH_CANCELLABLE_STATUSES | {"cancelling"}
            if status not in allowed:
                raise ValueError(f"invalid batch status {status!r}")
            params["status"] = status
        response = self._request(
            "GET",
            "/v1/batches",
            params=params or None,
            timeout=timeout,
        )
        jobs = parse_batch_list(response)
        for job in jobs:
            self._batch_jobs[job.id] = job
        return jobs

    def retrieve_batch(
        self,
        batch_id: str,
        *,
        timeout: float | None = None,
    ) -> BatchJob:
        """Retrieve a batch job."""
        checked_id = validate_resource_id(batch_id, "batch_id")
        response = self._request("GET", f"/v1/batches/{checked_id}", timeout=timeout)
        return self._remember_batch(BatchJob.from_response(response))

    def cancel_batch(
        self,
        batch_id: str | BatchJob,
        *,
        timeout: float | None = None,
    ) -> BatchJob:
        """Request cancellation of a non-terminal batch."""
        checked_id, known = self._batch_reference(batch_id)
        if known is not None and known.status not in BATCH_CANCELLABLE_STATUSES:
            raise ValueError(
                f"batch {checked_id!r} in state {known.status!r} cannot be cancelled"
            )
        response = self._request(
            "POST",
            f"/v1/batches/{checked_id}/cancel",
            timeout=timeout,
        )
        return self._remember_batch(BatchJob.from_response(response))

    def delete_batch(
        self,
        batch_id: str | BatchJob,
        *,
        timeout: float | None = None,
    ) -> None:
        """Delete a terminal batch."""
        checked_id, known = self._batch_reference(batch_id)
        if known is not None and known.status not in BATCH_TERMINAL_STATUSES:
            raise ValueError(
                f"batch {checked_id!r} must be terminal before deletion; "
                f"current state is {known.status!r}"
            )
        self._request_no_content("DELETE", f"/v1/batches/{checked_id}", timeout=timeout)
        self._batch_jobs.pop(checked_id, None)

    def list_batch_results(
        self,
        batch_id: str,
        *,
        limit: int | None = None,
        after: str | None = None,
        timeout: float | None = None,
    ) -> BatchResultsPage:
        """Retrieve one cursor-paginated JSON results page."""
        checked_id = validate_resource_id(batch_id, "batch_id")
        params: dict[str, Any] = {}
        if limit is not None:
            if limit <= 0:
                raise ValueError("limit must be greater than zero")
            params["limit"] = limit
        if after is not None:
            params["after"] = _validate_cursor(after)
        response = self._request(
            "GET",
            f"/v1/batches/{checked_id}/results",
            params=params or None,
            headers={"Accept": "application/json"},
            timeout=timeout,
        )
        known = self._batch_jobs.get(checked_id)
        endpoint: BatchEndpoint | None = known.endpoint if known is not None else None
        return parse_results_page(response, endpoint=endpoint)

    def get_batch_results(
        self,
        batch_id: str,
        *,
        limit: int | None = None,
        after: str | None = None,
        timeout: float | None = None,
    ) -> BatchResultsPage:
        """Alias for :meth:`list_batch_results`."""
        return self.list_batch_results(
            batch_id,
            limit=limit,
            after=after,
            timeout=timeout,
        )

    def download_batch_results(
        self,
        batch_id: str,
        *,
        timeout: float | None = None,
    ) -> bytes:
        """Download all currently available results as NDJSON bytes."""
        checked_id = validate_resource_id(batch_id, "batch_id")
        return self._request_bytes(
            "GET",
            f"/v1/batches/{checked_id}/results",
            headers={"Accept": "application/x-ndjson"},
            timeout=timeout,
        )

    def iter_batch_results(
        self,
        batch_id: str,
        *,
        timeout: float | None = None,
    ) -> Iterator[BatchResultItem]:
        """Iterate parsed items from the NDJSON results representation."""
        checked_id = validate_resource_id(batch_id, "batch_id")
        known = self._batch_jobs.get(checked_id)
        endpoint: BatchEndpoint | None = known.endpoint if known is not None else None
        path = f"/v1/batches/{checked_id}/results"
        for line in self._iter_ndjson_lines(path, timeout=timeout):
            yield from parse_ndjson_results(line, endpoint=endpoint)

    def wait_for_batch(
        self,
        batch_id: str | BatchJob,
        *,
        timeout: float = 600.0,
        poll_interval: float = 1.0,
        max_poll_interval: float = 30.0,
        poll_backoff: float = 2.0,
        cancel_event: Event | None = None,
        request_timeout: float | None = None,
    ) -> BatchJob:
        """Poll with bounded backoff until a batch reaches a terminal state."""
        _validate_wait_arguments(
            timeout=timeout,
            poll_interval=poll_interval,
            max_poll_interval=max_poll_interval,
            poll_backoff=poll_backoff,
        )
        if request_timeout is not None and (
            not math.isfinite(request_timeout) or request_timeout <= 0
        ):
            raise ValueError("request_timeout must be finite and greater than zero")
        checked_id, known = self._batch_reference(batch_id)
        if known is not None and known.is_terminal:
            return known
        deadline = time.monotonic() + timeout
        interval = poll_interval
        while True:
            if cancel_event is not None and cancel_event.is_set():
                raise InterruptedError(f"waiting for batch {checked_id!r} was cancelled")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"batch {checked_id!r} did not reach a terminal state within {timeout}s"
                )
            per_request_timeout = (
                self.timeout if request_timeout is None else request_timeout
            )
            job = self.retrieve_batch(
                checked_id,
                timeout=min(per_request_timeout, remaining),
            )
            if job.is_terminal:
                return job
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"batch {checked_id!r} did not reach a terminal state within {timeout}s"
                )
            sleep_for = min(interval, remaining)
            if cancel_event is not None:
                if cancel_event.wait(sleep_for):
                    raise InterruptedError(
                        f"waiting for batch {checked_id!r} was cancelled"
                    )
            else:
                time.sleep(sleep_for)
            interval = min(max_poll_interval, interval * poll_backoff)

    def check_prompt_batch(
        self,
        prompts: Iterable[str | Mapping[str, Any]] | None = None,
        *,
        idempotency_key: str,
        requests: Iterable[str | Mapping[str, Any]] | None = None,
        items: Iterable[str | Mapping[str, Any]] | None = None,
        defaults: Mapping[str, Any] | None = None,
        whitelisted_keywords: KeywordList = None,
        blacklisted_keywords: KeywordList = None,
        reasoning_mode: str | None = "low",
        risk_tolerance: str | None = None,
        environment: str | None = "production",
        metadata: Mapping[str, Any] | None = None,
        completion_window: Literal["24h"] = "24h",
        timeout: float | None = None,
    ) -> BatchJob:
        """Create one prompt batch without issuing scalar requests."""
        shared = _prompt_batch_defaults(
            defaults=defaults,
            whitelisted_keywords=whitelisted_keywords,
            blacklisted_keywords=blacklisted_keywords,
            reasoning_mode=reasoning_mode,
            risk_tolerance=risk_tolerance,
            environment=environment,
        )
        batch_items = _select_batch_items(
            prompts,
            requests=requests,
            items=items,
            primary_name="prompts",
        )
        batch_requests = build_prompt_batch_requests(batch_items, defaults=shared)
        return self.create_batch(
            "/v1/guardrails/prompt",
            idempotency_key=idempotency_key,
            requests=batch_requests,
            completion_window=completion_window,
            metadata=metadata,
            timeout=timeout,
        )

    def check_media_batch(
        self,
        media: Iterable[str | Mapping[str, Any]] | None = None,
        *,
        idempotency_key: str,
        requests: Iterable[str | Mapping[str, Any]] | None = None,
        items: Iterable[str | Mapping[str, Any]] | None = None,
        defaults: Mapping[str, Any] | None = None,
        output_type: str = "json",
        whitelisted_keywords: KeywordList = None,
        blacklisted_keywords: KeywordList = None,
        reasoning_mode: str | None = None,
        risk_tolerance: str | None = None,
        environment: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        completion_window: Literal["24h"] = "24h",
        timeout: float | None = None,
    ) -> BatchJob:
        """Create a media batch from HTTPS URLs and uploaded file IDs."""
        shared = _media_batch_defaults(
            defaults=defaults,
            output_type=output_type,
            whitelisted_keywords=whitelisted_keywords,
            blacklisted_keywords=blacklisted_keywords,
            reasoning_mode=reasoning_mode,
            risk_tolerance=risk_tolerance,
            environment=environment,
        )
        batch_items = _select_batch_items(
            media,
            requests=requests,
            items=items,
            primary_name="media",
        )
        batch_requests = build_media_batch_requests(batch_items, defaults=shared)
        return self.create_batch(
            "/v1/guardrails/media",
            idempotency_key=idempotency_key,
            requests=batch_requests,
            completion_window=completion_window,
            metadata=metadata,
            timeout=timeout,
        )

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
        self._batch_jobs: dict[str, BatchJob] = {}
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

    async def _request_response(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        request_timeout = merge_timeout(timeout, self.timeout)
        for attempt in range(self.max_retries + 1):
            try:
                response = await self._client.request(
                    method,
                    path,
                    json=json,
                    data=data,
                    files=files,
                    params=params,
                    headers=headers,
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
            return response
        raise AssertionError("unreachable")  # pragma: no cover

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        response = await self._request_response(
            method,
            path,
            json=json,
            data=data,
            files=files,
            params=params,
            headers=headers,
            timeout=timeout,
        )
        return parse_json_response(response)

    async def _request_bytes(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
    ) -> bytes:
        response = await self._request_response(
            method,
            path,
            headers=headers,
            timeout=timeout,
        )
        return response.content

    async def _request_no_content(
        self,
        method: str,
        path: str,
        *,
        timeout: float | None = None,
    ) -> None:
        await self._request_response(method, path, timeout=timeout)

    async def _iter_ndjson_lines(
        self,
        path: str,
        *,
        timeout: float | None = None,
    ) -> AsyncIterator[bytes]:
        request_timeout = merge_timeout(timeout, self.timeout)
        yielded = False
        for attempt in range(self.max_retries + 1):
            try:
                async with self._client.stream(
                    "GET",
                    path,
                    headers={"Accept": "application/x-ndjson"},
                    timeout=request_timeout,
                ) as response:
                    if should_retry_response(response) and attempt < self.max_retries:
                        retry_after = parse_retry_after(
                            response.headers.get("Retry-After")
                        )
                        await asyncio.sleep(backoff_delay(attempt + 1, retry_after))
                        continue
                    raise_for_response(response)
                    async for line in response.aiter_lines():
                        if line.strip():
                            yielded = True
                            yield line.encode("utf-8")
                return
            except httpx.TransportError as exc:
                if yielded or attempt >= self.max_retries:
                    raise APIConnectionError(
                        f"Batch result stream ended before completion: {exc}"
                    ) from exc
                await asyncio.sleep(backoff_delay(attempt + 1))
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

    # -- files and server-side batches ------------------------------------

    def _remember_batch(self, job: BatchJob) -> BatchJob:
        self._batch_jobs[job.id] = job
        return job

    def _batch_reference(self, batch: str | BatchJob) -> tuple[str, BatchJob | None]:
        if isinstance(batch, BatchJob):
            batch_id = validate_resource_id(batch.id, "batch_id")
            self._batch_jobs[batch_id] = batch
            return batch_id, batch
        batch_id = validate_resource_id(batch, "batch_id")
        return batch_id, None

    async def upload_file(
        self,
        file: FileSource,
        *,
        purpose: BatchUploadPurpose,
        timeout: float | None = None,
    ) -> BatchFile:
        """Upload a JSONL batch input or media file to ``POST /v1/files``."""
        checked_purpose = validate_file_purpose(purpose)
        filename, content = coerce_file(file)
        if not content:
            raise ValueError("file must not be empty")
        if checked_purpose == "batch":
            validate_batch_jsonl(content)
        response = await self._request(
            "POST",
            "/v1/files",
            data={"purpose": checked_purpose},
            files={"file": (filename, content)},
            timeout=timeout,
        )
        return BatchFile.from_response(response)

    async def retrieve_file(
        self,
        file_id: str,
        *,
        timeout: float | None = None,
    ) -> BatchFile:
        """Retrieve file metadata from ``GET /v1/files/{id}``."""
        checked_id = validate_resource_id(file_id, "file_id")
        response = await self._request("GET", f"/v1/files/{checked_id}", timeout=timeout)
        return BatchFile.from_response(response)

    async def delete_file(
        self,
        file_id: str,
        *,
        timeout: float | None = None,
    ) -> None:
        """Delete a stored file."""
        checked_id = validate_resource_id(file_id, "file_id")
        await self._request_no_content("DELETE", f"/v1/files/{checked_id}", timeout=timeout)

    async def create_batch(
        self,
        endpoint: BatchEndpoint,
        *,
        idempotency_key: str,
        requests: Iterable[Mapping[str, Any]] | None = None,
        input_file_id: str | None = None,
        completion_window: Literal["24h"] = "24h",
        metadata: Mapping[str, Any] | None = None,
        timeout: float | None = None,
    ) -> BatchJob:
        """Create a server-side prompt or media batch."""
        key = validate_idempotency_key(idempotency_key)
        _checked_endpoint, payload = build_batch_payload(
            endpoint,
            requests=requests,
            input_file_id=input_file_id,
            completion_window=completion_window,
            metadata=metadata,
        )
        response = await self._request(
            "POST",
            "/v1/batches",
            json=payload,
            headers={"Idempotency-Key": key},
            timeout=timeout,
        )
        return self._remember_batch(BatchJob.from_response(response))

    async def list_batches(
        self,
        *,
        limit: int | None = None,
        after: str | None = None,
        status: BatchStatus | None = None,
        timeout: float | None = None,
    ) -> list[BatchJob]:
        """List batch jobs from ``GET /v1/batches``."""
        params: dict[str, Any] = {}
        if limit is not None:
            if limit <= 0:
                raise ValueError("limit must be greater than zero")
            params["limit"] = limit
        if after is not None:
            params["after"] = _validate_cursor(after)
        if status is not None:
            allowed = BATCH_TERMINAL_STATUSES | BATCH_CANCELLABLE_STATUSES | {"cancelling"}
            if status not in allowed:
                raise ValueError(f"invalid batch status {status!r}")
            params["status"] = status
        response = await self._request(
            "GET",
            "/v1/batches",
            params=params or None,
            timeout=timeout,
        )
        jobs = parse_batch_list(response)
        for job in jobs:
            self._batch_jobs[job.id] = job
        return jobs

    async def retrieve_batch(
        self,
        batch_id: str,
        *,
        timeout: float | None = None,
    ) -> BatchJob:
        """Retrieve a batch job."""
        checked_id = validate_resource_id(batch_id, "batch_id")
        response = await self._request("GET", f"/v1/batches/{checked_id}", timeout=timeout)
        return self._remember_batch(BatchJob.from_response(response))

    async def cancel_batch(
        self,
        batch_id: str | BatchJob,
        *,
        timeout: float | None = None,
    ) -> BatchJob:
        """Request cancellation of a non-terminal batch."""
        checked_id, known = self._batch_reference(batch_id)
        if known is not None and known.status not in BATCH_CANCELLABLE_STATUSES:
            raise ValueError(
                f"batch {checked_id!r} in state {known.status!r} cannot be cancelled"
            )
        response = await self._request(
            "POST",
            f"/v1/batches/{checked_id}/cancel",
            timeout=timeout,
        )
        return self._remember_batch(BatchJob.from_response(response))

    async def delete_batch(
        self,
        batch_id: str | BatchJob,
        *,
        timeout: float | None = None,
    ) -> None:
        """Delete a terminal batch."""
        checked_id, known = self._batch_reference(batch_id)
        if known is not None and known.status not in BATCH_TERMINAL_STATUSES:
            raise ValueError(
                f"batch {checked_id!r} must be terminal before deletion; "
                f"current state is {known.status!r}"
            )
        await self._request_no_content(
            "DELETE",
            f"/v1/batches/{checked_id}",
            timeout=timeout,
        )
        self._batch_jobs.pop(checked_id, None)

    async def list_batch_results(
        self,
        batch_id: str,
        *,
        limit: int | None = None,
        after: str | None = None,
        timeout: float | None = None,
    ) -> BatchResultsPage:
        """Retrieve one cursor-paginated JSON results page."""
        checked_id = validate_resource_id(batch_id, "batch_id")
        params: dict[str, Any] = {}
        if limit is not None:
            if limit <= 0:
                raise ValueError("limit must be greater than zero")
            params["limit"] = limit
        if after is not None:
            params["after"] = _validate_cursor(after)
        response = await self._request(
            "GET",
            f"/v1/batches/{checked_id}/results",
            params=params or None,
            headers={"Accept": "application/json"},
            timeout=timeout,
        )
        known = self._batch_jobs.get(checked_id)
        endpoint: BatchEndpoint | None = known.endpoint if known is not None else None
        return parse_results_page(response, endpoint=endpoint)

    async def get_batch_results(
        self,
        batch_id: str,
        *,
        limit: int | None = None,
        after: str | None = None,
        timeout: float | None = None,
    ) -> BatchResultsPage:
        """Alias for :meth:`list_batch_results`."""
        return await self.list_batch_results(
            batch_id,
            limit=limit,
            after=after,
            timeout=timeout,
        )

    async def download_batch_results(
        self,
        batch_id: str,
        *,
        timeout: float | None = None,
    ) -> bytes:
        """Download all currently available results as NDJSON bytes."""
        checked_id = validate_resource_id(batch_id, "batch_id")
        return await self._request_bytes(
            "GET",
            f"/v1/batches/{checked_id}/results",
            headers={"Accept": "application/x-ndjson"},
            timeout=timeout,
        )

    async def iter_batch_results(
        self,
        batch_id: str,
        *,
        timeout: float | None = None,
    ) -> AsyncIterator[BatchResultItem]:
        """Iterate parsed items from the NDJSON results representation."""
        checked_id = validate_resource_id(batch_id, "batch_id")
        known = self._batch_jobs.get(checked_id)
        endpoint: BatchEndpoint | None = known.endpoint if known is not None else None
        path = f"/v1/batches/{checked_id}/results"
        async for line in self._iter_ndjson_lines(path, timeout=timeout):
            for result in parse_ndjson_results(line, endpoint=endpoint):
                yield result

    async def wait_for_batch(
        self,
        batch_id: str | BatchJob,
        *,
        timeout: float = 600.0,
        poll_interval: float = 1.0,
        max_poll_interval: float = 30.0,
        poll_backoff: float = 2.0,
        cancel_event: asyncio.Event | None = None,
        request_timeout: float | None = None,
    ) -> BatchJob:
        """Poll with bounded backoff until a batch reaches a terminal state."""
        _validate_wait_arguments(
            timeout=timeout,
            poll_interval=poll_interval,
            max_poll_interval=max_poll_interval,
            poll_backoff=poll_backoff,
        )
        if request_timeout is not None and (
            not math.isfinite(request_timeout) or request_timeout <= 0
        ):
            raise ValueError("request_timeout must be finite and greater than zero")
        checked_id, known = self._batch_reference(batch_id)
        if known is not None and known.is_terminal:
            return known
        deadline = time.monotonic() + timeout
        interval = poll_interval
        while True:
            if cancel_event is not None and cancel_event.is_set():
                raise asyncio.CancelledError(
                    f"waiting for batch {checked_id!r} was cancelled"
                )
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"batch {checked_id!r} did not reach a terminal state within {timeout}s"
                )
            per_request_timeout = (
                self.timeout if request_timeout is None else request_timeout
            )
            job = await self.retrieve_batch(
                checked_id,
                timeout=min(per_request_timeout, remaining),
            )
            if job.is_terminal:
                return job
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError(
                    f"batch {checked_id!r} did not reach a terminal state within {timeout}s"
                )
            sleep_for = min(interval, remaining)
            if cancel_event is None:
                await asyncio.sleep(sleep_for)
            else:
                try:
                    await asyncio.wait_for(cancel_event.wait(), timeout=sleep_for)
                except TimeoutError:
                    pass
                else:
                    raise asyncio.CancelledError(
                        f"waiting for batch {checked_id!r} was cancelled"
                    )
            interval = min(max_poll_interval, interval * poll_backoff)

    async def check_prompt_batch(
        self,
        prompts: Iterable[str | Mapping[str, Any]] | None = None,
        *,
        idempotency_key: str,
        requests: Iterable[str | Mapping[str, Any]] | None = None,
        items: Iterable[str | Mapping[str, Any]] | None = None,
        defaults: Mapping[str, Any] | None = None,
        whitelisted_keywords: KeywordList = None,
        blacklisted_keywords: KeywordList = None,
        reasoning_mode: str | None = "low",
        risk_tolerance: str | None = None,
        environment: str | None = "production",
        metadata: Mapping[str, Any] | None = None,
        completion_window: Literal["24h"] = "24h",
        timeout: float | None = None,
    ) -> BatchJob:
        """Create one prompt batch without issuing scalar requests."""
        shared = _prompt_batch_defaults(
            defaults=defaults,
            whitelisted_keywords=whitelisted_keywords,
            blacklisted_keywords=blacklisted_keywords,
            reasoning_mode=reasoning_mode,
            risk_tolerance=risk_tolerance,
            environment=environment,
        )
        batch_items = _select_batch_items(
            prompts,
            requests=requests,
            items=items,
            primary_name="prompts",
        )
        batch_requests = build_prompt_batch_requests(batch_items, defaults=shared)
        return await self.create_batch(
            "/v1/guardrails/prompt",
            idempotency_key=idempotency_key,
            requests=batch_requests,
            completion_window=completion_window,
            metadata=metadata,
            timeout=timeout,
        )

    async def check_media_batch(
        self,
        media: Iterable[str | Mapping[str, Any]] | None = None,
        *,
        idempotency_key: str,
        requests: Iterable[str | Mapping[str, Any]] | None = None,
        items: Iterable[str | Mapping[str, Any]] | None = None,
        defaults: Mapping[str, Any] | None = None,
        output_type: str = "json",
        whitelisted_keywords: KeywordList = None,
        blacklisted_keywords: KeywordList = None,
        reasoning_mode: str | None = None,
        risk_tolerance: str | None = None,
        environment: str | None = None,
        metadata: Mapping[str, Any] | None = None,
        completion_window: Literal["24h"] = "24h",
        timeout: float | None = None,
    ) -> BatchJob:
        """Create a media batch from HTTPS URLs and uploaded file IDs."""
        shared = _media_batch_defaults(
            defaults=defaults,
            output_type=output_type,
            whitelisted_keywords=whitelisted_keywords,
            blacklisted_keywords=blacklisted_keywords,
            reasoning_mode=reasoning_mode,
            risk_tolerance=risk_tolerance,
            environment=environment,
        )
        batch_items = _select_batch_items(
            media,
            requests=requests,
            items=items,
            primary_name="media",
        )
        batch_requests = build_media_batch_requests(batch_items, defaults=shared)
        return await self.create_batch(
            "/v1/guardrails/media",
            idempotency_key=idempotency_key,
            requests=batch_requests,
            completion_window=completion_window,
            metadata=metadata,
            timeout=timeout,
        )
