import asyncio
import json
import sys
sys.path.insert(0, "src")
sys.path.insert(0, "..")

from layer2_extraction.api import main as api_main
from layer2_extraction.integration.job_store import PipelineJob
from datetime import UTC, datetime

async def test():
    # Create pending job
    job_id = "p-test"
    job = PipelineJob(
        job_id=job_id,
        extraction_status="pending",
        ingestion_status="pending",
        created_at=datetime.now(UTC).isoformat(),
        entities_extracted=0,
        relationships_extracted=0,
        retry_count=0,
        last_error=None,
        next_retry_at=None,
        completed_at=None,
    )
    await api_main.job_store.set(job)
    print(f"Job created: {job_id}")

    # Start background task to complete job
    async def complete_later():
        await asyncio.sleep(0.6)
        updated = PipelineJob(
            job_id=job_id,
            extraction_status="completed",
            ingestion_status="pending",
            created_at=job.created_at,
            entities_extracted=0,
            relationships_extracted=0,
            retry_count=0,
            last_error=None,
            next_retry_at=None,
            completed_at=datetime.now(UTC).isoformat(),
        )
        await api_main.job_store.set(updated)
        print("Job updated to completed")

    task = asyncio.create_task(complete_later())

    # Run generator directly
    gen = api_main._job_event_generator(job_id)
    count = 0
    start = asyncio.get_event_loop().time()
    try:
        async for chunk in gen:
            count += 1
            print(f"[{asyncio.get_event_loop().time() - start:.2f}s] Chunk {count}: {chunk[:80]}...")
            if count > 20:
                print("Too many chunks, breaking")
                break
    except Exception as e:
        print(f"Exception: {e}")
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    print(f"Done. Received {count} chunks in {asyncio.get_event_loop().time() - start:.2f}s")

if __name__ == "__main__":
    asyncio.run(test())
