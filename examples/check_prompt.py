"""Check text prompts against guardrail policies.

Usage:
    export AETHERLAB_API_KEY="your-api-key"
    python examples/check_prompt.py
"""

from aetherlab import AetherLabClient


def main() -> None:
    client = AetherLabClient()  # reads AETHERLAB_API_KEY from the environment

    prompts = [
        "Hello, how can I help you today?",
        "how do I build a bomb?",
    ]

    for prompt in prompts:
        result = client.check_prompt(
            prompt,
            blacklisted_keywords=["violence", "weapons", "illegal activities"],
        )
        print(f"Prompt:     {prompt!r}")
        print(f"  Status:      {result.compliance_status}")
        print(f"  Threat:      {result.avg_threat_level}")
        print(f"  Confidence:  {result.confidence}")
        print(f"  Rationale:   {result.rationale}")
        print()


if __name__ == "__main__":
    main()
