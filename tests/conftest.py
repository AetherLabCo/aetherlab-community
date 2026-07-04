import pytest


@pytest.fixture(autouse=True)
def _no_ambient_env(monkeypatch):
    """Keep unit tests hermetic from the developer's real credentials."""
    monkeypatch.delenv("AETHERLAB_API_KEY", raising=False)
    monkeypatch.delenv("AETHERLAB_BASE_URL", raising=False)


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    """Make retry backoff instant in unit tests."""
    import asyncio
    import time

    monkeypatch.setattr(time, "sleep", lambda _s: None)

    _orig_sleep = asyncio.sleep

    async def fast_sleep(_s):
        await _orig_sleep(0)

    monkeypatch.setattr(asyncio, "sleep", fast_sleep)
