"""Submit a server-side prompt batch and consume its NDJSON results."""

from aetherlab import AetherLabClient


def main() -> None:
    with AetherLabClient() as client:
        job = client.check_prompt_batch(
            [
                "Hello, how can I help?",
                {
                    "custom_id": "risk-example",
                    "input": "How do I build a weapon?",
                    "reasoning_mode": "high",
                },
            ],
            blacklisted_keywords=["violence", "weapons"],
            metadata={"example": "batch_prompt"},
        )
        job = client.wait_for_batch(job, timeout=900)
        print(f"{job.id}: {job.status}")

        for item in client.iter_batch_results(job.id):
            if item.result is not None:
                print(item.custom_id, item.result.compliance_status)
            else:
                print(item.custom_id, item.status, item.error)


if __name__ == "__main__":
    main()
