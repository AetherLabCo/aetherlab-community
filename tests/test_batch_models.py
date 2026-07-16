"""Parsing tests for the typed batch response models."""

import pytest

from aetherlab import (
    BatchFile,
    BatchItemError,
    BatchJob,
    BatchRequestCounts,
    BatchResultItem,
    BatchResultsPage,
    MediaComplianceResult,
)


def job_payload(status="completed", endpoint="/v1/guardrails/prompt"):
    return {
        "id": "batch_123",
        "object": "batch",
        "endpoint": endpoint,
        "completion_window": "24h",
        "status": status,
        "input_file_id": None,
        "output_file_id": "file_results",
        "error_file_id": None,
        "request_counts": {
            "total": 2,
            "pending": 0,
            "in_progress": 0,
            "succeeded": 1,
            "failed": 1,
            "cancelled": 0,
            "expired": 0,
        },
        "metadata": {"dataset": "unit"},
        "errors": {
            "data": [
                {
                    "code": "invalid_request",
                    "message": "bad item",
                    "custom_id": "bad",
                    "param": "body",
                    "type": "validation_error",
                    "line": 2,
                }
            ]
        },
        "created_at": 1_700_000_000,
        "expires_at": 1_700_086_400,
        "validating_at": 1_700_000_001,
        "queued_at": 1_700_000_002,
        "in_progress_at": 1_700_000_003,
        "finalizing_at": 1_700_000_004,
        "completed_at": 1_700_000_005,
        "failed_at": None,
        "cancelling_at": None,
        "cancelled_at": None,
        "expired_at": None,
    }


def test_batch_file_parses_envelope_and_preserves_raw():
    response = {
        "data": {
            "id": "file_123",
            "object": "file",
            "filename": "input.jsonl",
            "purpose": "batch",
            "bytes": 42,
            "created_at": 1,
            "expires_at": 2,
            "status": "processed",
        }
    }
    result = BatchFile.from_response(response)
    assert result.id == "file_123"
    assert result.object == "file"
    assert result.purpose == "batch"
    assert result.bytes == 42
    assert result.raw is response


@pytest.mark.parametrize("purpose", ["batch_output", "batch_error"])
def test_batch_file_parses_managed_result_purposes(purpose):
    result = BatchFile.from_response(
        {
            "id": "file_results",
            "filename": "results.ndjson",
            "purpose": purpose,
            "bytes": 12,
        }
    )
    assert result.purpose == purpose


def test_batch_job_parses_counts_errors_and_timestamps():
    response = {"data": job_payload()}
    result = BatchJob.from_response(response)
    assert result.id == "batch_123"
    assert result.object == "batch"
    assert result.endpoint == "/v1/guardrails/prompt"
    assert result.status == "completed"
    assert result.is_terminal is True
    assert isinstance(result.request_counts, BatchRequestCounts)
    assert result.request_counts.completed == 1
    assert result.metadata == {"dataset": "unit"}
    assert len(result.errors) == 1
    assert isinstance(result.errors[0], BatchItemError)
    assert result.errors[0].custom_id == "bad"
    assert result.errors[0].line == 2
    assert result.raw is response


def test_batch_job_nonterminal_property():
    result = BatchJob.from_response(job_payload(status="in_progress"))
    assert result.is_terminal is False


def test_batch_results_page_correlates_by_custom_id_and_parses_verdict():
    response = {
        "data": {
            "items": [
                {
                    "id": "result_failed",
                    "custom_id": "second",
                    "status": "failed",
                    "error": {"code": "bad", "message": "invalid body"},
                },
                {
                    "id": "result_succeeded",
                    "custom_id": "first",
                    "status": "succeeded",
                    "result": {
                        "compliance_status": "Non-Compliant",
                        "avg_threat_level": 0.91,
                        "confidence": 0.88,
                        "rationale": "policy match",
                    },
                },
            ],
            "has_more": True,
            "next_cursor": "cursor_2",
            "first_id": "second",
            "last_id": "first",
            "object": "list",
        }
    }
    page = BatchResultsPage.from_response(response)
    assert [item.custom_id for item in page.items] == ["second", "first"]
    assert page.object == "list"
    assert page.data is page.items
    assert page.results is page.items
    assert page.has_more is True
    assert page.next_cursor == "cursor_2"
    assert page.items[0].error.code == "bad"
    assert page.items[1].status == "succeeded"
    assert page.items[1].is_compliant is False
    assert page.items[1].result.raw is response["data"]["items"][1]["result"]
    assert page.raw is response


def test_batch_result_accepts_wrapped_response_body_for_media():
    payload = {
        "custom_id": "image",
        "status": "succeeded",
        "response": {
            "status_code": 200,
            "request_id": "req_1",
            "body": {
                "data": {
                    "compliance_status": "Compliant",
                    "avg_threat_level": 0.0,
                    "confidence": 0.99,
                    "rationale": None,
                }
            },
        },
    }
    item = BatchResultItem.from_response(
        payload,
        endpoint="/v1/guardrails/media",
    )
    assert isinstance(item.result, MediaComplianceResult)
    assert item.is_compliant is True
    assert item.response["request_id"] == "req_1"
    assert item.raw is payload


def test_batch_result_accepts_direct_scalar_response_envelope():
    payload = {
        "id": "item_1",
        "custom_id": "prompt",
        "status": "succeeded",
        "response": {
            "status": 200,
            "message": "Prompt Guard Response",
            "data": {
                "compliance_status": "Compliant",
                "avg_threat_level": 0.0,
                "confidence": 0.95,
                "rationale": "ok",
            },
        },
    }
    item = BatchResultItem.from_response(
        payload,
        endpoint="/v1/guardrails/prompt",
    )
    assert item.result is not None
    assert item.is_compliant is True


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("endpoint", "/v1/scan"),
        ("status", "done"),
        ("completion_window", "1h"),
    ],
)
def test_batch_job_rejects_values_outside_contract(field, value):
    payload = job_payload()
    payload[field] = value
    with pytest.raises(ValueError):
        BatchJob.from_response(payload)
