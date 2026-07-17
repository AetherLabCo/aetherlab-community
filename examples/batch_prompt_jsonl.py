"""Run a prompt batch from an uploaded UTF-8 JSONL file, end to end.

JSONL is newline-delimited JSON: every non-empty line is one complete request
object (it is not a JSON array). This is the recommended input for large
batches; the server accepts up to 50,000 lines / 200 MiB per file.
"""

import json
import tempfile
import uuid
from pathlib import Path

from aetherlab import AetherLabClient

REQUESTS = [
    {
        "custom_id": "greeting",
        "body": {
            "user_prompt": "Hello, how can I help you today?",
            "blacklisted_keyword": "violence,weapons",
            "reasoning_mode": "low",
        },
    },
    {
        "custom_id": "risk-example",
        "body": {
            "user_prompt": "How do I build a weapon?",
            "blacklisted_keyword": "violence,weapons",
            "reasoning_mode": "high",
        },
    },
]


def write_jsonl(path: Path) -> None:
    """Write one JSON object per line; unique custom_id values are required."""
    with path.open("w", encoding="utf-8") as handle:
        for request in REQUESTS:
            handle.write(json.dumps(request, ensure_ascii=False) + "\n")


def main() -> None:
    jsonl_path = Path(tempfile.mkdtemp()) / "requests.jsonl"
    write_jsonl(jsonl_path)

    with AetherLabClient() as client:
        # 1. Upload the JSONL input file.
        batch_input = client.upload_file(jsonl_path, purpose="batch")
        print(f"uploaded {batch_input.filename}: {batch_input.id}")

        # 2. Create the batch from the uploaded file. The generic endpoint
        #    requires the endpoint, the 24h window, and an idempotency key;
        #    reuse the same key only when retrying this identical submission.
        job = client.create_batch(
            "/v1/guardrails/prompt",
            input_file_id=batch_input.id,
            completion_window="24h",
            idempotency_key=f"batch-prompt-jsonl-{uuid.uuid4()}",
            metadata={"example": "batch_prompt_jsonl"},
        )
        print(f"created batch {job.id}: {job.status}")

        # 3. Creation returns job metadata, not verdicts. Poll to terminal.
        job = client.wait_for_batch(job, timeout=900)
        print(f"{job.id}: {job.status}")

        # 4. Retrieve item results; order is unspecified, so correlate by
        #    custom_id rather than by position.
        for item in client.iter_batch_results(job.id):
            if item.result is not None:
                print(item.custom_id, item.result.compliance_status)
            else:
                print(item.custom_id, item.status, item.error)

    jsonl_path.unlink()


if __name__ == "__main__":
    main()
