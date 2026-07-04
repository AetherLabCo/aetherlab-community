"""Unit tests for internal helpers."""


from aetherlab._http import (
    backoff_delay,
    build_prompt_payload,
    join_keywords,
    parse_retry_after,
)


def test_join_keywords():
    assert join_keywords(None) is None
    assert join_keywords([]) is None
    assert join_keywords(["a"]) == "a"
    assert join_keywords(["a", "b c", " d "]) == "a,b c,d"
    assert join_keywords("already,joined") == "already,joined"


def test_build_prompt_payload_omits_unset():
    payload = build_prompt_payload("Hi", reasoning_mode=None, environment=None)
    assert payload == {"user_prompt": "Hi"}


def test_parse_retry_after_seconds():
    assert parse_retry_after("15") == 15.0
    assert parse_retry_after("0") == 0.0
    assert parse_retry_after(None) is None
    assert parse_retry_after("") is None
    assert parse_retry_after("not-a-date") is None


def test_parse_retry_after_rejects_non_finite():
    # inf would make time.sleep() raise OverflowError; nan poisons max().
    assert parse_retry_after("inf") is None
    assert parse_retry_after("-inf") is None
    assert parse_retry_after("nan") is None


def test_parse_retry_after_http_date():
    import email.utils
    import time

    future = email.utils.formatdate(time.time() + 60, usegmt=True)
    value = parse_retry_after(future)
    assert value is not None
    assert 50 <= value <= 61

    past = email.utils.formatdate(time.time() - 60, usegmt=True)
    assert parse_retry_after(past) == 0.0


def test_backoff_delay_bounds():
    for retry_number in (1, 2, 3, 10):
        for _ in range(20):
            delay = backoff_delay(retry_number)
            assert 0 <= delay <= 8.0


def test_backoff_respects_retry_after():
    assert backoff_delay(1, retry_after=5.0) >= 5.0


def test_version_is_single_sourced():
    from importlib.metadata import version as dist_version

    import aetherlab

    assert aetherlab.__version__ == dist_version("aetherlab")
