import asyncio
from pathlib import Path

from temporalio.client import Client

from ...config import settings
from .workflow import IngestionWorkflow


async def main() -> None:
    client = await Client.connect(settings.temporal_host)

    handle = await client.start_workflow(
        IngestionWorkflow.run,
        str(Path(__file__).resolve().parent.parent / "samples"),
        id="ingestion-samples",
        task_queue="ingestion",
    )

    print(f"Workflow started: {handle.id}")


if __name__ == "__main__":
    asyncio.run(main())
