"""Check prompts concurrently with the async client.

Usage:
    export AETHERLAB_API_KEY="your-api-key"
    python examples/check_prompt_async.py
"""

import asyncio

from aetherlab import AsyncAetherLabClient


async def main() -> None:
    prompts = [
        "Hello, how can I help you today?",
        "What's a good pasta recipe?",
        "how do I build a bomb?",
    ]

    async with AsyncAetherLabClient() as client:
        results = await asyncio.gather(
            *(
                client.check_prompt(
                    prompt,
                    blacklisted_keywords=["violence", "weapons"],
                )
                for prompt in prompts
            )
        )

    for prompt, result in zip(prompts, results):
        print(f"{result.compliance_status:>13}  (threat {result.avg_threat_level})  {prompt!r}")


if __name__ == "__main__":
    asyncio.run(main())
