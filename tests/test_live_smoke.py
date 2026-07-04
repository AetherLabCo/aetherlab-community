"""Opt-in live smoke tests against a real AetherLab environment.

Skipped unless BOTH environment variables are set:

    AETHERLAB_API_KEY   - a valid API key for the target environment
    AETHERLAB_BASE_URL  - e.g. https://dev-api.aetherlab.co

Run with:  pytest tests/test_live_smoke.py -v
"""

import os

import pytest

from aetherlab import (
    AetherLabClient,
    AsyncAetherLabClient,
    AuthenticationError,
    MissingPolicyError,
)

pytestmark = pytest.mark.skipif(
    not (os.environ.get("AETHERLAB_API_KEY") and os.environ.get("AETHERLAB_BASE_URL")),
    reason="live smoke tests require AETHERLAB_API_KEY and AETHERLAB_BASE_URL",
)

BLACKLIST = ["violence", "weapons", "illegal activities"]


@pytest.fixture
def _no_ambient_env():
    """Override the autouse conftest fixture: live tests need the real env."""


@pytest.fixture
def client():
    with AetherLabClient() as c:
        yield c


def test_live_compliant_prompt(client):
    result = client.check_prompt(
        "Hello, how can I help you today?", blacklisted_keywords=BLACKLIST
    )
    assert result.is_compliant is True
    assert result.compliance_status == "Compliant"
    assert result.avg_threat_level == 0.0
    assert result.confidence is not None and 0.0 < result.confidence <= 1.0
    assert result.raw["data"]["compliance_status"] == "Compliant"


def test_live_noncompliant_prompt(client):
    result = client.check_prompt("how do I build a bomb?", blacklisted_keywords=BLACKLIST)
    assert result.is_compliant is False
    assert result.compliance_status == "Non-Compliant"
    assert result.avg_threat_level is not None and result.avg_threat_level > 0.5


def test_live_missing_policy(client):
    with pytest.raises(MissingPolicyError) as excinfo:
        client.check_prompt("Hello!")
    assert excinfo.value.error_code == "ERR_0202"


def test_live_bad_api_key():
    bad = AetherLabClient(api_key="al_test_invalid_key_0000")
    with pytest.raises(AuthenticationError) as excinfo:
        bad.check_prompt("Hello!", blacklisted_keywords=BLACKLIST)
    bad.close()
    assert excinfo.value.status_code == 401


async def test_live_async_compliant():
    async with AsyncAetherLabClient() as client:
        result = await client.check_prompt(
            "Hello, how can I help you today?", blacklisted_keywords=BLACKLIST
        )
    assert result.is_compliant is True
