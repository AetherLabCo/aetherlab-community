"""Mocked contract tests for asynchronous batch and file operations."""

import asyncio
import json

import httpx
import pytest
import respx

from aetherlab import AsyncAetherLabClient, BatchJob

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
            "total": 1,
            "pending": int(status == "queued"),
            "in_progress": int(status == "in_progress"),
            "succeeded": int(status == "completed"),
            "failed": 0,
            "cancelled": 0,
            "expired": 0,
        },
        "metadata": {},
        "errors": [],
        "created_at": 1,
        "expires_at": 2,
    }


def file_payload():
    return {
        "id": "file_123",
        "filename": "input.jsonl",
        "purpose": "batch",
        "bytes": 50,
        "created_at": 1,
        "expires_at": 2,
        "status": "processed",
    }


@respx.mock
async def test_async_file_methods():
    upload = respx.post(f"{BASE}/v1/files").mock(
        return_value=httpx.Response(201, json=file_payload())
    )
    retrieve = respx.get(f"{BASE}/v1/files/file_123").mock(
        return_value=httpx.Response(200, json=file_payload())
    )
    delete = respx.delete(f"{BASE}/v1/files/file_123").mock(
        return_value=httpx.Response(204)
    )
    source = b'{"custom_id":"one","body":{"user_prompt":"hello"}}\n'

    async with AsyncAetherLabClient(api_key="k", base_url=BASE) as client:
        stored = await client.upload_file(source, purpose="batch")
        fetched = await client.retrieve_file("file_123")
        removed = await client.delete_file("file_123")

    assert stored.id == fetched.id == "file_123"
    assert removed is None
    assert source.strip() in upload.calls.last.request.read()
    assert retrieve.called and delete.called


@respx.mock
async def test_async_batch_lifecycle_methods():
    create = respx.post(f"{BASE}/v1/batches").mock(
        return_value=httpx.Response(201, json=batch_payload())
    )
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

    async with AsyncAetherLabClient(api_key="k", base_url=BASE) as client:
        created = await client.create_batch(
            "/v1/guardrails/prompt",
            idempotency_key="async-idem",
            requests=[{"custom_id": "one", "body": {"user_prompt": "hello"}}],
        )
        jobs = await client.list_batches(limit=5)
        current = await client.retrieve_batch("batch_123")
        cancelling = await client.cancel_batch(batch_id=current)
        done = BatchJob.from_response(
            batch_payload(batch_id="batch_done", status="completed")
        )
        await client.delete_batch(batch_id=done)

    assert created.status == "queued"
    assert create.calls.last.request.headers["idempotency-key"] == "async-idem"
    assert len(jobs) == 1
    assert current.status == "in_progress"
    assert cancelling.status == "cancelling"
    assert listing.called and retrieve.called and cancel.called and delete.called


@respx.mock
async def test_async_results_page_download_and_iteration():
    item = {
        "custom_id": "one",
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
            httpx.Response(200, json={"data": [item], "has_more": False}),
            httpx.Response(200, content=json.dumps(item).encode() + b"\n"),
            httpx.Response(200, content=json.dumps(item).encode() + b"\n"),
        ]
    )

    async with AsyncAetherLabClient(api_key="k", base_url=BASE) as client:
        page = await client.get_batch_results("batch_123")
        content = await client.download_batch_results("batch_123")
        parsed = [result async for result in client.iter_batch_results("batch_123")]

    assert page.items[0].custom_id == "one"
    assert content.endswith(b"\n")
    assert parsed[0].is_compliant is True
    assert route.calls[0].request.headers["accept"] == "application/json"
    assert route.calls[1].request.headers["accept"] == "application/x-ndjson"


@respx.mock
async def test_async_wait_for_batch_and_cancellation():
    route = respx.get(f"{BASE}/v1/batches/batch_123").mock(
        side_effect=[
            httpx.Response(200, json=batch_payload(status="in_progress")),
            httpx.Response(200, json=batch_payload(status="completed")),
        ]
    )
    async with AsyncAetherLabClient(api_key="k", base_url=BASE) as client:
        result = await client.wait_for_batch(
            batch_id="batch_123",
            timeout=5,
            poll_interval=0.01,
            max_poll_interval=0.02,
        )
        event = asyncio.Event()
        event.set()
        with pytest.raises(asyncio.CancelledError):
            await client.wait_for_batch("not_polled", cancel_event=event)

    assert result.status == "completed"
    assert route.call_count == 2


@respx.mock
async def test_async_prompt_and_media_convenience_methods():
    route = respx.post(f"{BASE}/v1/batches").mock(
        side_effect=[
            httpx.Response(201, json=batch_payload()),
            httpx.Response(
                201,
                json=batch_payload(
                    batch_id="batch_media",
                    endpoint="/v1/guardrails/media",
                ),
            ),
        ]
    )
    async with AsyncAetherLabClient(api_key="k", base_url=BASE) as client:
        prompt_job = await client.check_prompt_batch(
            [{"custom_id": "p", "prompt": "hello"}],
            idempotency_key="prompt",
            blacklisted_keywords=["weapons"],
        )
        prompt_body = json.loads(route.calls[0].request.content)
        media_job = await client.check_media_batch(
            ["https://example.com/image.png", {"file_id": "file_media"}],
            idempotency_key="media",
        )
        media_body = json.loads(route.calls[1].request.content)

    assert prompt_job.endpoint == "/v1/guardrails/prompt"
    assert prompt_body["requests"][0]["body"]["user_prompt"] == "hello"
    assert media_job.endpoint == "/v1/guardrails/media"
    assert media_body["requests"][0]["body"]["input_type"] == "url"
    assert media_body["requests"][1]["body"]["file_id"] == "file_media"


@respx.mock
async def test_async_validation_prevents_network_io():
    route = respx.post(f"{BASE}/v1/batches").mock(return_value=httpx.Response(500))
    async with AsyncAetherLabClient(api_key="k", base_url=BASE) as client:
        with pytest.raises(ValueError, match="exactly one"):
            await client.create_batch(
                "/v1/guardrails/prompt",
                idempotency_key="bad",
            )
        completed = BatchJob.from_response(batch_payload(status="completed"))
        with pytest.raises(ValueError, match="cannot be cancelled"):
            await client.cancel_batch(completed)
        with pytest.raises(ValueError, match="base64"):
            await client.check_media_batch(
                [{"body": {"input_type": "base64", "image": "abc"}}],
                idempotency_key="base64",
            )
    assert route.call_count == 0
