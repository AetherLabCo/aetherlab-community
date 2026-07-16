"""Submit and consume a server-side media batch asynchronously."""

import asyncio
import os
from typing import Any

from aetherlab import AsyncAetherLabClient


async def main() -> None:
    media: list[str | dict[str, Any]] = [
        "https://example.com/public-image.png",
    ]
    # Set this to an ID returned by upload_file(..., purpose="guardrail_media").
    uploaded_file_id = os.environ.get("AETHERLAB_MEDIA_FILE_ID")
    if uploaded_file_id:
        media.append({"custom_id": "uploaded-image", "file_id": uploaded_file_id})

    async with AsyncAetherLabClient() as client:
        job = await client.check_media_batch(
            media,
            idempotency_key="example-media-batch-v1",
            blacklisted_keywords=["violence"],
            metadata={"example": "batch_media_async"},
        )
        job = await client.wait_for_batch(job, timeout=900)
        print(f"{job.id}: {job.status}")

        async for item in client.iter_batch_results(job.id):
            if item.result is not None:
                print(item.custom_id, item.result.compliance_status)
            else:
                print(item.custom_id, item.status, item.error)


if __name__ == "__main__":
    asyncio.run(main())
