"""Mocked contract tests for synchronous batch and file operations."""

import json
from threading import Event

import httpx
import pytest
import respx

from aetherlab import AetherLabClient, APIError, BatchFile, BatchJob, BatchResultsPage

BASE = "https://unit.test"


def batch_payload(
    *,
    batch_id="batch_123",
    endpoint="/v1/guardrails/prompt",
    status="queued",
):
    return {
        "id": batch_id,
        "endpoint": endpoint,
        "completion_window": "24h",
        "status": status,
        "input_file_id": None,
        "output_file_id": None,
        "error_file_id": None,
        "request_counts": {
            "total": 2,
            "pending": 2 if status == "queued" else 0,
            "in_progress": 0,
            "succeeded": 2 if status == "completed" else 0,
            "failed": 0,
            "cancelled": 0,
            "expired": 0,
        },
        "metadata": {},
        "errors": [],
        "created_at": 1,
        "expires_at": 2,
    }


def file_payload(*, purpose="batch"):
    return {
        "id": "file_123",
        "filename": "requests.jsonl" if purpose == "batch" else "image.png",
        "purpose": purpose,
        "bytes": 64,
        "created_at": 1,
        "expires_at": 2,
        "status": "processed",
    }


@pytest.fixture
def client():
    with AetherLabClient(api_key="unit-key", base_url=BASE) as value:
        yield value


@respx.mock
def test_upload_retrieve_and_delete_file(client, tmp_path):
    upload = respx.post(f"{BASE}/v1/files").mock(
        return_value=httpx.Response(201, json={"data": file_payload()})
    )
    retrieve = respx.get(f"{BASE}/v1/files/file_123").mock(
        return_value=httpx.Response(200, json=file_payload())
    )
    delete = respx.delete(f"{BASE}/v1/files/file_123").mock(
        return_value=httpx.Response(204)
    )

    source = b'{"custom_id":"one","body":{"user_prompt":"hello"}}\n'
    source_path = tmp_path / "requests.jsonl"
    source_path.write_bytes(source)
    uploaded = client.upload_file(source_path, purpose="batch")
    fetched = client.retrieve_file("file_123")
    result = client.delete_file("file_123")

    assert uploaded.id == fetched.id == "file_123"
    assert result is None
    body = upload.calls.last.request.read()
    assert b'name="purpose"' in body and b"batch" in body
    assert b'name="file"' in body and source.strip() in body
    assert b'filename="requests.jsonl"' in body
    assert upload.calls.last.request.headers["x-api-key"] == "unit-key"
    assert "authorization" not in upload.calls.last.request.headers
    assert retrieve.called and delete.called


@respx.mock
def test_upload_guardrail_media_does_not_apply_jsonl_validation(client):
    route = respx.post(f"{BASE}/v1/files").mock(
        return_value=httpx.Response(201, json=file_payload(purpose="guardrail_media"))
    )
    result = client.upload_file(b"\x89PNG", purpose="guardrail_media")
    assert result.purpose == "guardrail_media"
    assert b"guardrail_media" in route.calls.last.request.read()


@respx.mock
def test_create_inline_batch_sends_required_contract(client):
    route = respx.post(f"{BASE}/v1/batches").mock(
        return_value=httpx.Response(201, json={"data": batch_payload()})
    )
    result = client.create_batch(
        "/v1/guardrails/prompt",
        idempotency_key="idem-123",
        requests=[
            {"custom_id": "b", "body": {"user_prompt": "second"}},
            {"custom_id": "a", "body": {"user_prompt": "first"}},
        ],
        metadata={"source": "tests"},
    )

    assert isinstance(result, BatchJob)
    assert result.status == "queued"
    request = route.calls.last.request
    assert request.headers["idempotency-key"] == "idem-123"
    assert request.headers["x-api-key"] == "unit-key"
    body = json.loads(request.content)
    assert body == {
        "endpoint": "/v1/guardrails/prompt",
        "completion_window": "24h",
        "requests": [
            {"custom_id": "b", "body": {"user_prompt": "second"}},
            {"custom_id": "a", "body": {"user_prompt": "first"}},
        ],
        "metadata": {"source": "tests"},
    }


@respx.mock
def test_create_batch_from_input_file(client):
    route = respx.post(f"{BASE}/v1/batches").mock(
        return_value=httpx.Response(201, json=batch_payload())
    )
    client.create_batch(
        "/v1/guardrails/prompt",
        idempotency_key="idem-file",
        input_file_id="file_123",
    )
    assert json.loads(route.calls.last.request.content)["input_file_id"] == "file_123"


@respx.mock
@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {
            "requests": [{"custom_id": "a", "body": {"user_prompt": "x"}}],
            "input_file_id": "file_123",
        },
        {
            "requests": [
                {"custom_id": "same", "body": {"user_prompt": "x"}},
                {"custom_id": "same", "body": {"user_prompt": "y"}},
            ]
        },
        {"requests": [{"custom_id": "", "body": {"user_prompt": "x"}}]},
        {"requests": [{"custom_id": "x", "body": {"file_id": "file_media"}}]},
    ],
)
def test_create_batch_validation_happens_before_network(client, kwargs):
    route = respx.post(f"{BASE}/v1/batches").mock(
        return_value=httpx.Response(500)
    )
    with pytest.raises(ValueError):
        client.create_batch(
            "/v1/guardrails/prompt",
            idempotency_key="idem",
            **kwargs,
        )
    assert route.call_count == 0


@respx.mock
def test_create_batch_rejects_bad_endpoint_window_and_key(client):
    route = respx.post(f"{BASE}/v1/batches").mock(return_value=httpx.Response(500))
    request = [{"custom_id": "one", "body": {"user_prompt": "hello"}}]
    with pytest.raises(ValueError, match="endpoint"):
        client.create_batch("/scan", idempotency_key="x", requests=request)
    with pytest.raises(ValueError, match="completion_window"):
        client.create_batch(
            "/v1/guardrails/prompt",
            idempotency_key="x",
            requests=request,
            completion_window="1h",
        )
    with pytest.raises(ValueError, match="idempotency_key"):
        client.create_batch(
            "/v1/guardrails/prompt",
            idempotency_key="",
            requests=request,
        )
    assert route.call_count == 0


@respx.mock
def test_list_retrieve_cancel_and_delete_batch(client):
    listing = respx.get(f"{BASE}/v1/batches").mock(
        return_value=httpx.Response(200, json={"data": [batch_payload()]})
    )
    retrieve = respx.get(f"{BASE}/v1/batches/batch_123").mock(
        return_value=httpx.Response(200, json=batch_payload(status="in_progress"))
    )
    cancel = respx.post(f"{BASE}/v1/batches/batch_123/cancel").mock(
        return_value=httpx.Response(200, json=batch_payload(status="cancelling"))
    )
    delete = respx.delete(f"{BASE}/v1/batches/batch_done").mock(
        return_value=httpx.Response(204)
    )

    jobs = client.list_batches(limit=10, after="batch_prev", status="queued")
    current = client.retrieve_batch("batch_123")
    cancelling = client.cancel_batch(batch_id=current)
    done = BatchJob.from_response(
        batch_payload(batch_id="batch_done", status="completed")
    )
    client.delete_batch(batch_id=done)

    assert len(jobs) == 1
    assert listing.calls.last.request.url.params["limit"] == "10"
    assert listing.calls.last.request.url.params["after"] == "batch_prev"
    assert current.status == "in_progress"
    assert cancelling.status == "cancelling"
    assert retrieve.called and cancel.called and delete.called


@respx.mock
def test_invalid_terminal_operations_do_not_touch_network(client):
    cancel = respx.post(f"{BASE}/v1/batches/batch_done/cancel").mock(
        return_value=httpx.Response(500)
    )
    delete = respx.delete(f"{BASE}/v1/batches/batch_live").mock(
        return_value=httpx.Response(500)
    )
    completed = BatchJob.from_response(
        batch_payload(batch_id="batch_done", status="completed")
    )
    running = BatchJob.from_response(
        batch_payload(batch_id="batch_live", status="in_progress")
    )
    with pytest.raises(ValueError, match="cannot be cancelled"):
        client.cancel_batch(completed)
    with pytest.raises(ValueError, match="must be terminal"):
        client.delete_batch(running)
    assert cancel.call_count == delete.call_count == 0


@respx.mock
def test_paginated_and_ndjson_results(client):
    item = {
        "custom_id": "request-b",
        "status": "succeeded",
        "result": {
            "compliance_status": "Compliant",
            "avg_threat_level": 0.0,
            "confidence": 0.9,
            "rationale": "ok",
        },
    }
    route = respx.get(f"{BASE}/v1/batches/batch_123/results").mock(
        side_effect=[
            httpx.Response(
                200,
                json={
                    "data": [item],
                    "has_more": True,
                    "next_cursor": "cursor_2",
                },
            ),
            httpx.Response(200, content=json.dumps(item).encode() + b"\n"),
            httpx.Response(200, content=json.dumps(item).encode() + b"\n"),
        ]
    )

    page = client.list_batch_results("batch_123", limit=1, after="cursor_1")
    content = client.download_batch_results("batch_123")
    parsed = list(client.iter_batch_results("batch_123"))

    assert isinstance(page, BatchResultsPage)
    assert page.items[0].custom_id == "request-b"
    assert page.next_cursor == "cursor_2"
    assert content.endswith(b"\n")
    assert parsed[0].is_compliant is True
    assert route.calls[0].request.headers["accept"] == "application/json"
    assert route.calls[1].request.headers["accept"] == "application/x-ndjson"


@respx.mock
def test_wait_for_batch_polls_until_terminal(client):
    route = respx.get(f"{BASE}/v1/batches/batch_123").mock(
        side_effect=[
            httpx.Response(200, json=batch_payload(status="in_progress")),
            httpx.Response(200, json=batch_payload(status="completed")),
        ]
    )
    result = client.wait_for_batch(
        batch_id="batch_123",
        timeout=5,
        poll_interval=0.01,
        max_poll_interval=0.02,
    )
    assert result.status == "completed"
    assert route.call_count == 2


@respx.mock
def test_wait_for_batch_honours_pre_set_cancellation(client):
    route = respx.get(f"{BASE}/v1/batches/batch_123").mock(
        return_value=httpx.Response(500)
    )
    event = Event()
    event.set()
    with pytest.raises(InterruptedError):
        client.wait_for_batch("batch_123", cancel_event=event)
    assert route.call_count == 0


@respx.mock
def test_wait_for_batch_enforces_overall_timeout(client, monkeypatch):
    route = respx.get(f"{BASE}/v1/batches/batch_123").mock(
        return_value=httpx.Response(200, json=batch_payload(status="in_progress"))
    )
    ticks = iter([0.0, 0.1, 2.0])
    monkeypatch.setattr("aetherlab.client.time.monotonic", lambda: next(ticks))
    with pytest.raises(TimeoutError, match="within 1"):
        client.wait_for_batch(
            "batch_123",
            timeout=1,
            poll_interval=0.1,
            max_poll_interval=0.2,
        )
    assert route.call_count == 1


@respx.mock
def test_prompt_convenience_uses_one_batch_call_and_stable_ids(client):
    batch = respx.post(f"{BASE}/v1/guardrails/prompt/batches").mock(
        return_value=httpx.Response(201, json=batch_payload())
    )
    generic = respx.post(f"{BASE}/v1/batches").mock(
        return_value=httpx.Response(500)
    )
    scalar = respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        return_value=httpx.Response(500)
    )
    prompts = [
        "hello",
        {
            "custom_id": "chosen",
            "body": {"user_prompt": "world", "reasoning_mode": "high"},
        },
    ]
    first = client.check_prompt_batch(
        prompts,
        blacklisted_keywords=["weapons"],
        defaults={"risk_tolerance": "medium"},
    )
    first_key = batch.calls.last.request.headers["idempotency-key"]
    first_body = json.loads(batch.calls.last.request.content)
    second = client.check_prompt_batch(
        requests=prompts,
        blacklisted_keywords=["weapons"],
        defaults={"risk_tolerance": "medium"},
    )
    second_key = batch.calls.last.request.headers["idempotency-key"]
    second_body = json.loads(batch.calls.last.request.content)

    assert first.status == second.status == "queued"
    assert scalar.call_count == 0
    assert generic.call_count == 0
    assert batch.call_count == 2
    assert first_key == second_key
    first_items = first_body["items"]
    assert first_items[0]["custom_id"] == second_body["items"][0]["custom_id"]
    assert first_body["settings"]["blacklisted_keyword"] == "weapons"
    assert first_body["settings"]["risk_tolerance"] == "medium"
    assert "environment" not in first_body["settings"]
    assert first_items[1]["custom_id"] == "chosen"
    assert first_items[1]["reasoning_mode"] == "high"


@respx.mock
def test_simplest_prompt_batch_call_is_stable_and_uses_facade(client):
    route = respx.post(f"{BASE}/v1/guardrails/prompt/batches").mock(
        return_value=httpx.Response(201, json=batch_payload())
    )

    client.check_prompt_batch(["first", "second"])
    first_request = route.calls.last.request
    client.check_prompt_batch(["first", "second"])
    second_request = route.calls.last.request

    first_body = json.loads(first_request.content)
    second_body = json.loads(second_request.content)
    assert [item["input"] for item in first_body["items"]] == ["first", "second"]
    assert first_body["items"] == second_body["items"]
    assert (
        first_request.headers["idempotency-key"]
        == second_request.headers["idempotency-key"]
    )


@respx.mock
def test_prompt_convenience_accepts_documented_input_alias(client):
    route = respx.post(f"{BASE}/v1/guardrails/prompt/batches").mock(
        return_value=httpx.Response(201, json=batch_payload())
    )

    client.check_prompt_batch(
        [
            {
                "custom_id": "documented-input",
                "input": "Review this mapped prompt.",
                "reasoning_mode": "high",
            }
        ]
    )

    body = json.loads(route.calls.last.request.content)
    assert body["items"] == [
        {
            "custom_id": "documented-input",
            "input": "Review this mapped prompt.",
            "reasoning_mode": "high",
        }
    ]
    with pytest.raises(ValueError, match="exactly one"):
        client.check_prompt_batch(
            [{"input": "first source", "prompt": "second source"}]
        )
    assert route.call_count == 1


@respx.mock
def test_media_convenience_accepts_https_and_file_ids_only(client):
    route = respx.post(f"{BASE}/v1/guardrails/media/batches").mock(
        return_value=httpx.Response(
            201,
            json=batch_payload(endpoint="/v1/guardrails/media"),
        )
    )
    uploaded = BatchFile.from_response(
        {
            "id": "c62f8af0-a76c-4cdf-97ad-6f1498f00669",
            "filename": "stored.png",
            "purpose": "guardrail_media",
            "bytes": 5,
        }
    )
    client.check_media_batch(
        items=[
            "https://example.com/image.png",
            {
                "custom_id": "stored",
                "file_id": "50fd109f-4c3a-42b7-92be-14c1d8f89111",
            },
            uploaded,
        ],
        idempotency_key="media-idem",
        blacklisted_keywords=["violence"],
    )
    body = json.loads(route.calls.last.request.content)
    assert body["items"][0]["url"].startswith("https://")
    assert body["items"][1]["file_id"] == "50fd109f-4c3a-42b7-92be-14c1d8f89111"
    assert body["items"][2]["file_id"] == uploaded.id
    assert "environment" not in body["settings"]
    assert "output_type" not in body["settings"]
    assert body["settings"]["blacklisted_keyword"] == "violence"

    with pytest.raises(ValueError, match="HTTPS"):
        client.check_media_batch(["http://example.com/image.png"], idempotency_key="bad")
    with pytest.raises(ValueError, match="base64"):
        client.check_media_batch(
            [{"body": {"input_type": "base64", "image": "abc"}}],
            idempotency_key="bad-base64",
        )
    assert route.call_count == 1


@respx.mock
def test_convenience_rejects_single_string_and_malformed_ndjson(client):
    create = respx.post(f"{BASE}/v1/batches").mock(return_value=httpx.Response(500))
    results = respx.get(f"{BASE}/v1/batches/batch_123/results").mock(
        return_value=httpx.Response(200, content=b"not json\n")
    )
    with pytest.raises(TypeError, match="iterable"):
        client.check_prompt_batch("one prompt", idempotency_key="bad")
    with pytest.raises(APIError, match="invalid NDJSON"):
        list(client.iter_batch_results("batch_123"))
    assert create.call_count == 0
    assert results.call_count == 1


def test_batch_jsonl_duplicate_ids_rejected_before_client_request(client):
    content = (
        b'{"custom_id":"same","body":{"user_prompt":"one"}}\n'
        b'{"custom_id":"same","body":{"user_prompt":"two"}}\n'
    )
    with pytest.raises(ValueError, match="duplicate custom_id"):
        client.upload_file(content, purpose="batch")


def test_batch_jsonl_rejects_embedded_base64(client):
    content = (
        b'{"custom_id":"media","body":{"input_type":"base64","image":"abc"}}\n'
    )
    with pytest.raises(ValueError, match="base64"):
        client.upload_file(content, purpose="batch")


def test_inline_request_count_limit(client):
    requests = [
        {"custom_id": f"item-{index}", "body": {"user_prompt": "x"}}
        for index in range(1001)
    ]
    with pytest.raises(ValueError, match="1000"):
        client.create_batch(
            "/v1/guardrails/prompt",
            idempotency_key="too-many",
            requests=requests,
        )
