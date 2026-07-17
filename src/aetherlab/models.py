"""Response models for the AetherLab SDK."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Union, cast

BatchEndpoint = Literal["/v1/guardrails/prompt", "/v1/guardrails/media"]
BatchFilePurpose = Literal[
    "batch",
    "guardrail_media",
    "batch_output",
    "batch_error",
]
BatchUploadPurpose = Literal["batch", "guardrail_media"]
BatchStatus = Literal[
    "validating",
    "queued",
    "in_progress",
    "finalizing",
    "completed",
    "failed",
    "cancelling",
    "cancelled",
    "expired",
]
BatchItemStatus = Literal[
    "pending",
    "in_progress",
    "succeeded",
    "failed",
    "cancelled",
    "expired",
]
Timestamp = Union[str, int, float]

__all__ = [
    "BatchEndpoint",
    "BatchFilePurpose",
    "BatchUploadPurpose",
    "BatchStatus",
    "BatchItemStatus",
    "ComplianceResult",
    "MediaComplianceResult",
    "BatchFile",
    "BatchRequestCounts",
    "BatchJob",
    "BatchItemError",
    "BatchResultItem",
    "BatchResultsPage",
]

_BATCH_ENDPOINTS = frozenset({"/v1/guardrails/prompt", "/v1/guardrails/media"})
_BATCH_FILE_PURPOSES = frozenset(
    {"batch", "guardrail_media", "batch_output", "batch_error"}
)
_BATCH_STATUSES = frozenset(
    {
        "validating",
        "queued",
        "in_progress",
        "finalizing",
        "completed",
        "failed",
        "cancelling",
        "cancelled",
        "expired",
    }
)
_BATCH_ITEM_STATUSES = frozenset(
    {"pending", "in_progress", "succeeded", "failed", "cancelled", "expired"}
)


def _data_of(response: dict[str, Any]) -> dict[str, Any]:
    """Return the ``data`` object of an API envelope, tolerating a flat dict."""
    data = response.get("data")
    if isinstance(data, dict):
        return data
    return response


def _required_string(data: dict[str, Any], key: str) -> str:
    value = data.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"response field {key!r} must be a non-empty string")
    return value


def _optional_string(data: dict[str, Any], key: str) -> str | None:
    value = data.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"response field {key!r} must be a string or null")
    return value


def _optional_timestamp(data: dict[str, Any], key: str) -> Timestamp | None:
    value = data.get(key)
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, bool):
        raise ValueError(f"response field {key!r} must be a timestamp or null")
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return value
    raise ValueError(f"response field {key!r} must be a timestamp or null")


def _nonnegative_int(data: dict[str, Any], key: str, default: int = 0) -> int:
    value = data.get(key, default)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"response field {key!r} must be a non-negative integer")
    return int(value)


def _optional_nonnegative_int(data: dict[str, Any], key: str) -> int | None:
    if data.get(key) is None:
        return None
    return _nonnegative_int(data, key)


def _literal(
    data: dict[str, Any],
    key: str,
    allowed: frozenset[str],
) -> str:
    value = _required_string(data, key)
    if value not in allowed:
        choices = ", ".join(sorted(allowed))
        raise ValueError(f"response field {key!r} must be one of {choices}; got {value!r}")
    return value


@dataclass
class ComplianceResult:
    """Result of a prompt guardrail check (``POST /v1/guardrails/prompt``).

    Every field is taken verbatim from the API response; nothing is computed
    client-side except :attr:`is_compliant`, which is derived from
    :attr:`compliance_status`.

    Attributes:
        compliance_status: ``"Compliant"`` or ``"Non-Compliant"`` as returned
            by the API.
        is_compliant: ``True`` when ``compliance_status`` equals
            ``"Compliant"`` (case-insensitive).
        avg_threat_level: Average threat level in ``[0.0, 1.0]``; higher means
            more likely to violate the configured policies.
        confidence: The model's confidence in the verdict, in ``[0.0, 1.0]``,
            exactly as returned by the API.
        rationale: Free-text explanation of the verdict; may be ``None``.
        raw: The complete, unmodified JSON response body.
    """

    compliance_status: str
    avg_threat_level: float | None
    confidence: float | None
    rationale: str | None
    raw: dict[str, Any] = field(repr=False)

    @property
    def is_compliant(self) -> bool:
        return self.compliance_status.strip().lower() == "compliant"

    @classmethod
    def from_response(cls, response: dict[str, Any]) -> ComplianceResult:
        data = _data_of(response)
        return cls(
            compliance_status=str(data.get("compliance_status", "")),
            avg_threat_level=data.get("avg_threat_level"),
            confidence=data.get("confidence"),
            rationale=data.get("rationale"),
            raw=response,
        )


@dataclass
class MediaComplianceResult(ComplianceResult):
    """Result of a media guardrail check (``POST /v1/guardrails/media``).

    Same fields as :class:`ComplianceResult`; the API returns the identical
    ``data`` shape for media checks.
    """

    @classmethod
    def from_response(cls, response: dict[str, Any]) -> MediaComplianceResult:
        data = _data_of(response)
        return cls(
            compliance_status=str(data.get("compliance_status", "")),
            avg_threat_level=data.get("avg_threat_level"),
            confidence=data.get("confidence"),
            rationale=data.get("rationale"),
            raw=response,
        )


@dataclass
class BatchFile:
    """A file stored for batch input or batch-safe media references."""

    id: str
    object: str | None
    filename: str
    purpose: BatchFilePurpose
    bytes: int
    created_at: Timestamp | None
    expires_at: Timestamp | None
    status: str | None
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_response(cls, response: dict[str, Any]) -> BatchFile:
        data = _data_of(response)
        purpose = cast(
            BatchFilePurpose,
            _literal(data, "purpose", _BATCH_FILE_PURPOSES),
        )
        filename = data.get("filename", data.get("name"))
        if not isinstance(filename, str) or not filename:
            raise ValueError("response field 'filename' must be a non-empty string")
        size = data.get("bytes", data.get("size_bytes", data.get("size", 0)))
        if isinstance(size, bool) or not isinstance(size, int) or size < 0:
            raise ValueError("response file size must be a non-negative integer")
        return cls(
            id=_required_string(data, "id"),
            object=_optional_string(data, "object"),
            filename=filename,
            purpose=purpose,
            bytes=size,
            created_at=_optional_timestamp(data, "created_at"),
            expires_at=_optional_timestamp(data, "expires_at"),
            status=_optional_string(data, "status"),
            raw=response,
        )


@dataclass
class BatchRequestCounts:
    """Counts of requests in each batch item state."""

    total: int
    pending: int
    in_progress: int
    succeeded: int
    failed: int
    cancelled: int
    expired: int
    completed: int
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_response(cls, response: dict[str, Any]) -> BatchRequestCounts:
        data = _data_of(response)
        succeeded = _nonnegative_int(data, "succeeded")
        failed = _nonnegative_int(data, "failed")
        cancelled = _nonnegative_int(data, "cancelled")
        expired = _nonnegative_int(data, "expired")
        completed_default = succeeded
        return cls(
            total=_nonnegative_int(data, "total"),
            pending=_nonnegative_int(data, "pending"),
            in_progress=_nonnegative_int(data, "in_progress"),
            succeeded=succeeded,
            failed=failed,
            cancelled=cancelled,
            expired=expired,
            completed=_nonnegative_int(data, "completed", completed_default),
            raw=response,
        )


@dataclass
class BatchItemError:
    """Structured error attached to a batch or one of its result items."""

    code: str
    message: str
    custom_id: str | None
    param: str | None
    type: str | None
    line: int | None
    raw: dict[str, Any] = field(repr=False)

    @classmethod
    def from_response(cls, response: dict[str, Any]) -> BatchItemError:
        data = _data_of(response)
        code = data.get("code", data.get("error_code", ""))
        message = data.get("message", data.get("error", ""))
        if not isinstance(code, str):
            code = str(code)
        if not isinstance(message, str):
            message = str(message)
        return cls(
            code=code,
            message=message,
            custom_id=_optional_string(data, "custom_id"),
            param=_optional_string(data, "param"),
            type=_optional_string(data, "type"),
            line=_optional_nonnegative_int(data, "line"),
            raw=response,
        )


def _batch_errors(data: dict[str, Any]) -> list[BatchItemError]:
    errors_value = data.get("errors")
    if errors_value is None:
        return []
    if isinstance(errors_value, dict):
        nested = errors_value.get("data", errors_value.get("items"))
        if nested is None and ("message" in errors_value or "code" in errors_value):
            nested = [errors_value]
        errors_value = nested
    if not isinstance(errors_value, list):
        raise ValueError("response field 'errors' must contain a list")
    errors: list[BatchItemError] = []
    for error in errors_value:
        if not isinstance(error, dict):
            raise ValueError("each batch error must be an object")
        errors.append(BatchItemError.from_response(error))
    return errors


@dataclass
class BatchJob:
    """Server-side batch job returned by ``/v1/batches``."""

    id: str
    object: str | None
    endpoint: BatchEndpoint
    completion_window: Literal["24h"]
    status: BatchStatus
    input_file_id: str | None
    output_file_id: str | None
    error_file_id: str | None
    request_counts: BatchRequestCounts | None
    metadata: dict[str, Any]
    errors: list[BatchItemError]
    created_at: Timestamp | None
    expires_at: Timestamp | None
    validating_at: Timestamp | None
    queued_at: Timestamp | None
    in_progress_at: Timestamp | None
    finalizing_at: Timestamp | None
    completed_at: Timestamp | None
    failed_at: Timestamp | None
    cancelling_at: Timestamp | None
    cancelled_at: Timestamp | None
    expired_at: Timestamp | None
    raw: dict[str, Any] = field(repr=False)

    @property
    def is_terminal(self) -> bool:
        """Whether the server will no longer transition this job."""
        return self.status in {"completed", "failed", "cancelled", "expired"}

    @classmethod
    def from_response(cls, response: dict[str, Any]) -> BatchJob:
        data = _data_of(response)
        endpoint = cast(BatchEndpoint, _literal(data, "endpoint", _BATCH_ENDPOINTS))
        status = cast(BatchStatus, _literal(data, "status", _BATCH_STATUSES))
        completion_window = _required_string(data, "completion_window")
        if completion_window != "24h":
            raise ValueError(
                "response field 'completion_window' must be '24h', "
                f"got {completion_window!r}"
            )
        counts_value = data.get("request_counts")
        if counts_value is not None and not isinstance(counts_value, dict):
            raise ValueError("response field 'request_counts' must be an object or null")
        metadata_value = data.get("metadata")
        if metadata_value is None:
            metadata: dict[str, Any] = {}
        elif isinstance(metadata_value, dict):
            metadata = metadata_value
        else:
            raise ValueError("response field 'metadata' must be an object or null")
        return cls(
            id=_required_string(data, "id"),
            object=_optional_string(data, "object"),
            endpoint=endpoint,
            completion_window="24h",
            status=status,
            input_file_id=_optional_string(data, "input_file_id"),
            output_file_id=_optional_string(data, "output_file_id"),
            error_file_id=_optional_string(data, "error_file_id"),
            request_counts=(
                BatchRequestCounts.from_response(counts_value)
                if isinstance(counts_value, dict)
                else None
            ),
            metadata=metadata,
            errors=_batch_errors(data),
            created_at=_optional_timestamp(data, "created_at"),
            expires_at=_optional_timestamp(data, "expires_at"),
            validating_at=_optional_timestamp(data, "validating_at"),
            queued_at=_optional_timestamp(data, "queued_at"),
            in_progress_at=_optional_timestamp(data, "in_progress_at"),
            finalizing_at=_optional_timestamp(data, "finalizing_at"),
            completed_at=_optional_timestamp(data, "completed_at"),
            failed_at=_optional_timestamp(data, "failed_at"),
            cancelling_at=_optional_timestamp(data, "cancelling_at"),
            cancelled_at=_optional_timestamp(data, "cancelled_at"),
            expired_at=_optional_timestamp(data, "expired_at"),
            raw=response,
        )


def _result_payload(data: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    response_value = data.get("response")
    response = response_value if isinstance(response_value, dict) else None
    result_value = data.get("result")
    if isinstance(result_value, dict):
        return response, result_value
    if response is not None:
        body = response.get("body")
        if isinstance(body, dict):
            return response, body
        if isinstance(response.get("data"), dict) or "compliance_status" in response:
            return response, response
    body_value = data.get("body")
    if isinstance(body_value, dict):
        return response, body_value
    if "compliance_status" in data:
        return response, data
    return response, None


@dataclass
class BatchResultItem:
    """One unordered result, correlated to input by :attr:`custom_id`."""

    id: str | None
    custom_id: str
    status: BatchItemStatus
    result: ComplianceResult | MediaComplianceResult | None
    response: dict[str, Any] | None
    error: BatchItemError | None
    raw: dict[str, Any] = field(repr=False)

    @property
    def is_succeeded(self) -> bool:
        return self.status == "succeeded"

    @property
    def is_compliant(self) -> bool | None:
        """Return the verdict for succeeded items, otherwise ``None``."""
        if self.status != "succeeded" or self.result is None:
            return None
        return self.result.is_compliant

    @classmethod
    def from_response(
        cls,
        response: dict[str, Any],
        *,
        endpoint: BatchEndpoint | None = None,
    ) -> BatchResultItem:
        data = _data_of(response)
        status = cast(
            BatchItemStatus,
            _literal(data, "status", _BATCH_ITEM_STATUSES),
        )
        response_payload, result_payload = _result_payload(data)
        result: ComplianceResult | MediaComplianceResult | None = None
        if result_payload is not None:
            result = (
                MediaComplianceResult.from_response(result_payload)
                if endpoint == "/v1/guardrails/media"
                else ComplianceResult.from_response(result_payload)
            )
        error_value = data.get("error")
        if error_value is not None and not isinstance(error_value, dict):
            raise ValueError("response field 'error' must be an object or null")
        return cls(
            id=_optional_string(data, "id"),
            custom_id=_required_string(data, "custom_id"),
            status=status,
            result=result,
            response=response_payload,
            error=(
                BatchItemError.from_response(error_value)
                if isinstance(error_value, dict)
                else None
            ),
            raw=response,
        )


def _page_data(response: dict[str, Any]) -> tuple[list[Any], dict[str, Any]]:
    data_value = response.get("data")
    if isinstance(data_value, list):
        return data_value, response
    if isinstance(data_value, dict):
        for key in ("items", "results", "data"):
            items = data_value.get(key)
            if isinstance(items, list):
                return items, data_value
    for key in ("items", "results"):
        items = response.get(key)
        if isinstance(items, list):
            return items, response
    raise ValueError("batch results response does not contain an items list")


@dataclass
class BatchResultsPage:
    """One cursor-paginated page of unordered batch results."""

    object: str | None
    items: list[BatchResultItem]
    has_more: bool
    next_cursor: str | None
    first_id: str | None
    last_id: str | None
    raw: dict[str, Any] = field(repr=False)

    @property
    def results(self) -> list[BatchResultItem]:
        """Alias for :attr:`items` matching the REST response terminology."""
        return self.items

    @property
    def data(self) -> list[BatchResultItem]:
        """Alias for :attr:`items` matching list-style API envelopes."""
        return self.items

    @classmethod
    def from_response(
        cls,
        response: dict[str, Any],
        *,
        endpoint: BatchEndpoint | None = None,
    ) -> BatchResultsPage:
        raw_items, page = _page_data(response)
        items: list[BatchResultItem] = []
        for item in raw_items:
            if not isinstance(item, dict):
                raise ValueError("each batch result must be an object")
            items.append(BatchResultItem.from_response(item, endpoint=endpoint))
        has_more_value = page.get("has_more", response.get("has_more", False))
        if not isinstance(has_more_value, bool):
            raise ValueError("response field 'has_more' must be a boolean")
        cursor_value = page.get(
            "next_cursor",
            page.get(
                "next_after",
                page.get(
                    "next",
                    response.get("next_cursor", response.get("next_after")),
                ),
            ),
        )
        if cursor_value is not None and not isinstance(cursor_value, str):
            raise ValueError("response field 'next_cursor' must be a string or null")
        first_id = page.get("first_id", response.get("first_id"))
        last_id = page.get("last_id", response.get("last_id"))
        if first_id is not None and not isinstance(first_id, str):
            raise ValueError("response field 'first_id' must be a string or null")
        if last_id is not None and not isinstance(last_id, str):
            raise ValueError("response field 'last_id' must be a string or null")
        if cursor_value is None and has_more_value and isinstance(last_id, str):
            cursor_value = last_id
        return cls(
            object=_optional_string(page, "object")
            or _optional_string(response, "object"),
            items=items,
            has_more=has_more_value,
            next_cursor=cursor_value,
            first_id=first_id,
            last_id=last_id,
            raw=response,
        )
