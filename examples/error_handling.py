"""Handle every error class the SDK can raise.

Usage:
    export AETHERLAB_API_KEY="your-api-key"
    python examples/error_handling.py
"""

from aetherlab import (
    AetherLabClient,
    AetherLabError,
    APIConnectionError,
    AuthenticationError,
    InvalidRequestError,
    MissingPolicyError,
    RateLimitError,
)


def check(prompt: str) -> None:
    client = AetherLabClient()
    try:
        result = client.check_prompt(
            prompt,
            blacklisted_keywords=["violence", "weapons"],
        )
    except AuthenticationError as e:
        print(f"Bad or missing API key: {e}")
    except MissingPolicyError as e:
        # Raised when neither the account nor the request has any policy.
        print(f"Configure a policy at https://app.aetherlab.co first: {e}")
    except RateLimitError as e:
        print(f"Rate limited; retry after {e.retry_after} seconds")
    except InvalidRequestError as e:
        print(f"Malformed request ({e.error_code}): {e.message}")
    except APIConnectionError as e:
        print(f"Network problem after retries: {e}")
    except AetherLabError as e:
        # Catch-all for anything else the SDK raises (e.g. 5xx APIError).
        print(f"AetherLab request failed: {e}")
    else:
        print(f"{result.compliance_status} (threat {result.avg_threat_level})")


if __name__ == "__main__":
    check("Hello, how can I help you today?")
