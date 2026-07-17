"""Unit tests for the async client. All HTTP is mocked with respx."""

import json

import httpx
import pytest
import respx

from aetherlab import (
    APIConnectionError,
    AsyncAetherLabClient,
    AuthenticationError,
    MissingPolicyError,
    RateLimitError,
)

BASE = "https://unit.test"

PROMPT_OK = {
    "status": 200,
    "message": "Prompt Guard Response",
    "data": {
        "compliance_status": "Compliant",
        "avg_threat_level": 0.0,
        "confidence": 0.71,
        "rationale": "ok",
    },
}

MEDIA_OK = {
    "status": 200,
    "message": "Media Guard Response",
    "data": {
        "compliance_status": "Compliant",
        "avg_threat_level": 0.0,
        "confidence": 0.99,
        "rationale": None,
    },
}


@respx.mock
async def test_async_check_prompt_success():
    route = respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        return_value=httpx.Response(200, json=PROMPT_OK)
    )
    async with AsyncAetherLabClient(api_key="k", base_url=BASE) as client:
        result = await client.check_prompt("Hi", blacklisted_keywords=["weapons"])
    assert result.is_compliant is True
    body = json.loads(route.calls.last.request.content)
    assert body["user_prompt"] == "Hi"
    assert body["blacklisted_keyword"] == "weapons"


@respx.mock
async def test_async_check_media():
    route = respx.post(f"{BASE}/v1/guardrails/media").mock(
        return_value=httpx.Response(200, json=MEDIA_OK)
    )
    async with AsyncAetherLabClient(api_key="k", base_url=BASE) as client:
        result = await client.check_media(b"bytes", input_type="file")
    assert result.is_compliant is True
    assert route.calls.last.request.headers["content-type"].startswith("multipart/form-data")


@respx.mock
async def test_async_check_media_sends_industry():
    route = respx.post(f"{BASE}/v1/guardrails/media").mock(
        return_value=httpx.Response(200, json=MEDIA_OK)
    )
    async with AsyncAetherLabClient(api_key="k", base_url=BASE) as client:
        result = await client.check_media(
            "https://example.com/cat.png",
            input_type="url",
            industry="nsfw",
        )
    assert result.is_compliant is True
    body = route.calls.last.request.read()
    assert b'name="industry"' in body
    assert b"nsfw" in body


@respx.mock
async def test_async_error_mapping():
    respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        side_effect=[
            httpx.Response(401, json={"error_code": "ERR_0100", "message": "Invalid API key"}),
            httpx.Response(400, json={"error_code": "ERR_0202", "message": "no policies"}),
            httpx.Response(429, headers={"Retry-After": "3"}, json={"message": "slow down"}),
        ]
    )
    client = AsyncAetherLabClient(api_key="k", base_url=BASE, max_retries=0)
    with pytest.raises(AuthenticationError):
        await client.check_prompt("Hi")
    with pytest.raises(MissingPolicyError):
        await client.check_prompt("Hi")
    with pytest.raises(RateLimitError) as excinfo:
        await client.check_prompt("Hi")
    assert excinfo.value.retry_after == 3.0
    await client.close()


@respx.mock
async def test_async_retries_then_succeeds():
    route = respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        side_effect=[
            httpx.Response(503, json={"message": "unavailable"}),
            httpx.ConnectError("net down"),
            httpx.Response(200, json=PROMPT_OK),
        ]
    )
    async with AsyncAetherLabClient(api_key="k", base_url=BASE) as client:
        result = await client.check_prompt("Hi")
    assert result.is_compliant
    assert route.call_count == 3


@respx.mock
async def test_async_connection_errors_exhausted():
    respx.post(f"{BASE}/v1/guardrails/prompt").mock(side_effect=httpx.ConnectError("down"))
    async with AsyncAetherLabClient(api_key="k", base_url=BASE, max_retries=1) as client:
        with pytest.raises(APIConnectionError):
            await client.check_prompt("Hi")
