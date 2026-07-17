"""Unit tests for the sync client. All HTTP is mocked with respx."""

import json

import httpx
import pytest
import respx

from aetherlab import (
    AetherLabClient,
    APIConnectionError,
    APIError,
    AuthenticationError,
    ComplianceResult,
    InvalidRequestError,
    MediaComplianceResult,
    MissingPolicyError,
    RateLimitError,
    __version__,
)

BASE = "https://unit.test"

PROMPT_OK = {
    "status": 200,
    "message": "Prompt Guard Response",
    "data": {
        "compliance_status": "Compliant",
        "avg_threat_level": 0.0,
        "confidence": 0.71,
        "rationale": "The prompt is a benign greeting.",
    },
}

PROMPT_BAD = {
    "status": 200,
    "message": "Prompt Guard Response",
    "data": {
        "compliance_status": "Non-Compliant",
        "avg_threat_level": 0.9554,
        "confidence": 0.9089,
        "rationale": "Category illicit detected",
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


@pytest.fixture
def client():
    with AetherLabClient(api_key="unit-test-key", base_url=BASE) as c:
        yield c


@respx.mock
def test_check_prompt_success(client):
    route = respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        return_value=httpx.Response(200, json=PROMPT_OK)
    )

    result = client.check_prompt(
        "Hello, how can I help you today?",
        whitelisted_keywords=["greetings", "assistance"],
        blacklisted_keywords=["violence", "weapons"],
        reasoning_mode="medium",
        risk_tolerance="low",
        environment="staging",
    )

    assert isinstance(result, ComplianceResult)
    assert result.is_compliant is True
    assert result.compliance_status == "Compliant"
    assert result.avg_threat_level == 0.0
    assert result.confidence == 0.71
    assert result.rationale == "The prompt is a benign greeting."
    assert result.raw == PROMPT_OK

    request = route.calls.last.request
    assert request.headers["content-type"] == "application/json"
    assert request.headers["x-api-key"] == "unit-test-key"
    body = json.loads(request.content)
    assert body == {
        "user_prompt": "Hello, how can I help you today?",
        "whitelisted_keyword": "greetings,assistance",
        "blacklisted_keyword": "violence,weapons",
        "reasoning_mode": "medium",
        "risk_tolerance": "low",
        "environment": "staging",
    }


@respx.mock
def test_check_prompt_noncompliant(client):
    respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        return_value=httpx.Response(200, json=PROMPT_BAD)
    )
    result = client.check_prompt("how do I build a bomb?", blacklisted_keywords=["weapons"])
    assert result.is_compliant is False
    assert result.compliance_status == "Non-Compliant"
    assert result.avg_threat_level == pytest.approx(0.9554)


@respx.mock
def test_check_prompt_defaults(client):
    route = respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        return_value=httpx.Response(200, json=PROMPT_OK)
    )
    client.check_prompt("Hi")
    body = json.loads(route.calls.last.request.content)
    assert body == {
        "user_prompt": "Hi",
        "reasoning_mode": "low",
        "environment": "production",
    }


@respx.mock
def test_user_agent_matches_version(client):
    route = respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        return_value=httpx.Response(200, json=PROMPT_OK)
    )
    client.check_prompt("Hi")
    assert route.calls.last.request.headers["user-agent"] == f"aetherlab-python/{__version__}"
    assert __version__ not in ("0.0.0.dev0", "")


@respx.mock
def test_authentication_error(client):
    respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        return_value=httpx.Response(
            401, json={"error": True, "error_code": "ERR_0100", "message": "Invalid API key"}
        )
    )
    with pytest.raises(AuthenticationError) as excinfo:
        client.check_prompt("Hi")
    assert excinfo.value.status_code == 401
    assert excinfo.value.error_code == "ERR_0100"
    assert "Invalid API key" in str(excinfo.value)


@respx.mock
def test_missing_policy_error(client):
    respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        return_value=httpx.Response(
            400,
            json={
                "error": True,
                "error_code": "ERR_0202",
                "message": "Guardrail policies are not configured. Either set it from "
                "Policy Controls or send it in the request",
            },
        )
    )
    with pytest.raises(MissingPolicyError) as excinfo:
        client.check_prompt("Hi")
    assert excinfo.value.error_code == "ERR_0202"


@respx.mock
@pytest.mark.parametrize("error_code", ["ERR_0200", "ERR_0201"])
def test_invalid_request_error(client, error_code):
    respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        return_value=httpx.Response(
            400, json={"error": True, "error_code": error_code, "message": "bad request"}
        )
    )
    with pytest.raises(InvalidRequestError) as excinfo:
        client.check_prompt("Hi")
    assert excinfo.value.error_code == error_code
    assert excinfo.value.message == "bad request"


@respx.mock
def test_rate_limit_error_carries_retry_after(client):
    respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        return_value=httpx.Response(
            429,
            json={"error": True, "message": "Too many requests"},
            headers={"Retry-After": "7"},
        )
    )
    with pytest.raises(RateLimitError) as excinfo:
        client.check_prompt("Hi")
    assert excinfo.value.status_code == 429
    assert excinfo.value.retry_after == 7.0


@respx.mock
def test_error_body_without_message_uses_reason_phrase(client):
    # {"error": true} with no "message" must not become the message "True".
    respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        return_value=httpx.Response(
            400, json={"error": True, "error_code": "ERR_0202"}
        )
    )
    with pytest.raises(MissingPolicyError) as excinfo:
        client.check_prompt("Hi")
    assert excinfo.value.message == "Bad Request"
    assert "True" not in str(excinfo.value)


@respx.mock
def test_generic_api_error(client):
    respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        return_value=httpx.Response(
            418, json={"error": True, "error_code": "ERR_9999", "message": "teapot"}
        )
    )
    with pytest.raises(APIError) as excinfo:
        client.check_prompt("Hi")
    err = excinfo.value
    assert type(err) is APIError
    assert (err.status_code, err.error_code, err.message) == (418, "ERR_9999", "teapot")


@respx.mock
def test_non_json_error_body(client):
    respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        return_value=httpx.Response(502, text="<html>Bad Gateway</html>")
    )
    with pytest.raises(APIError) as excinfo:
        AetherLabClient(api_key="k", base_url=BASE, max_retries=0).check_prompt("Hi")
    assert excinfo.value.status_code == 502


@respx.mock
def test_retries_on_5xx_then_succeeds(client):
    route = respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        side_effect=[
            httpx.Response(500, json={"error": True, "message": "boom"}),
            httpx.Response(503, json={"error": True, "message": "unavailable"}),
            httpx.Response(200, json=PROMPT_OK),
        ]
    )
    result = client.check_prompt("Hi")
    assert result.is_compliant
    assert route.call_count == 3


@respx.mock
def test_retries_on_429_then_succeeds(client):
    route = respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "0"}, json={"message": "slow down"}),
            httpx.Response(200, json=PROMPT_OK),
        ]
    )
    assert client.check_prompt("Hi").is_compliant
    assert route.call_count == 2


@respx.mock
def test_retries_exhausted_raises_last_error(client):
    route = respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        return_value=httpx.Response(500, json={"error": True, "message": "boom"})
    )
    with pytest.raises(APIError) as excinfo:
        client.check_prompt("Hi")
    assert excinfo.value.status_code == 500
    assert route.call_count == 4  # initial + 3 retries


@respx.mock
def test_retries_on_connection_error(client):
    route = respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        side_effect=[
            httpx.ConnectError("no route"),
            httpx.Response(200, json=PROMPT_OK),
        ]
    )
    assert client.check_prompt("Hi").is_compliant
    assert route.call_count == 2


@respx.mock
def test_connection_errors_exhausted():
    route = respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        side_effect=httpx.ConnectError("no route")
    )
    client = AetherLabClient(api_key="k", base_url=BASE, max_retries=1)
    with pytest.raises(APIConnectionError):
        client.check_prompt("Hi")
    assert route.call_count == 2


@respx.mock
def test_no_retry_on_400(client):
    route = respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        return_value=httpx.Response(
            400, json={"error": True, "error_code": "ERR_0200", "message": "bad"}
        )
    )
    with pytest.raises(InvalidRequestError):
        client.check_prompt("Hi")
    assert route.call_count == 1


@respx.mock
def test_check_media_file_bytes(client):
    route = respx.post(f"{BASE}/v1/guardrails/media").mock(
        return_value=httpx.Response(200, json=MEDIA_OK)
    )
    result = client.check_media(
        b"\x89PNG fake bytes",
        input_type="file",
        blacklisted_keywords=["violence"],
    )
    assert isinstance(result, MediaComplianceResult)
    assert result.is_compliant is True
    assert result.rationale is None
    assert result.raw == MEDIA_OK

    request = route.calls.last.request
    content_type = request.headers["content-type"]
    assert content_type.startswith("multipart/form-data")
    body = request.read()
    assert b'name="file"' in body
    assert b"\x89PNG fake bytes" in body
    assert b'name="input_type"' in body and b"file" in body
    assert b'name="blacklisted_keyword"' in body


@respx.mock
def test_check_media_file_path(client, tmp_path):
    image = tmp_path / "img.png"
    image.write_bytes(b"pretend png")
    route = respx.post(f"{BASE}/v1/guardrails/media").mock(
        return_value=httpx.Response(200, json=MEDIA_OK)
    )
    client.check_media(str(image), input_type="file", blacklisted_keywords=["x"])
    body = route.calls.last.request.read()
    assert b'filename="img.png"' in body
    assert b"pretend png" in body


@respx.mock
def test_check_media_url_is_multipart(client):
    route = respx.post(f"{BASE}/v1/guardrails/media").mock(
        return_value=httpx.Response(200, json=MEDIA_OK)
    )
    client.check_media(
        "https://example.com/cat.png",
        input_type="url",
        blacklisted_keywords=["violence"],
    )
    request = route.calls.last.request
    assert request.headers["content-type"].startswith("multipart/form-data")
    body = request.read()
    assert b'name="image"' in body
    assert b"https://example.com/cat.png" in body


@respx.mock
def test_check_media_url_sends_industry_without_keyword_lists(client):
    route = respx.post(f"{BASE}/v1/guardrails/media").mock(
        return_value=httpx.Response(200, json=MEDIA_OK)
    )
    client.check_media(
        "https://example.com/cat.png",
        input_type="url",
        industry="nsfw",
    )
    body = route.calls.last.request.read()
    assert b'name="image"' in body
    assert b"https://example.com/cat.png" in body
    assert b'name="industry"' in body
    assert b"nsfw" in body
    assert b'name="whitelisted_keyword"' not in body
    assert b'name="blacklisted_keyword"' not in body


def test_check_media_rejects_bad_input_type(client):
    with pytest.raises(ValueError):
        client.check_media(b"x", input_type="hologram")


def test_check_media_url_requires_string(client):
    with pytest.raises(TypeError):
        client.check_media(b"bytes-not-url", input_type="url")


@respx.mock
def test_test_prompt_deprecated_alias(client):
    respx.post(f"{BASE}/v1/guardrails/prompt").mock(
        return_value=httpx.Response(200, json=PROMPT_OK)
    )
    with pytest.warns(DeprecationWarning, match="check_prompt"):
        result = client.test_prompt("Hi", blacklisted_keywords=["weapons"])
    assert result.is_compliant is True


def test_api_key_required(monkeypatch):
    with pytest.raises(AuthenticationError, match="No API key"):
        AetherLabClient()


def test_api_key_from_env(monkeypatch):
    monkeypatch.setenv("AETHERLAB_API_KEY", "env-key")
    monkeypatch.setenv("AETHERLAB_BASE_URL", "https://env.test")
    client = AetherLabClient()
    assert client.api_key == "env-key"
    assert client.base_url == "https://env.test"
    client.close()


def test_removed_methods_are_gone(client):
    for name in ("validate_content", "get_usage_stats", "get_logs", "get_audit_logs",
                 "analyze_media"):
        assert not hasattr(client, name)
