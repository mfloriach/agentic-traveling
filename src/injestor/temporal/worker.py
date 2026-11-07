import asyncio

from langchain_huggingface import HuggingFaceEmbeddings
from temporalio.client import Client
from temporalio.worker import Worker

from injestor.pipeline import Pipeline
from src.infrastructure.semantic_database import QdrantDatabase
from src.injestor.dlps.default import DlpDefault
from src.injestor.loaders.local import LoaderLocal
from src.injestor.parsers.tika import ParserTika
from src.injestor.splitters.splitter import Splitter

from ...config import settings
from .workflow import IngestionActivities, IngestionWorkflow


async def main() -> None:
    client = await Client.connect(settings.temporal_host)

    pipeline = Pipeline(
        database=QdrantDatabase(
            url=settings.qdrant.host,
            collection_name=settings.qdrant.collection,
            embeddings=HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            ),
        ),
        parser=ParserTika(url=settings.tika_server_endpoint),
        splitter=Splitter(),
        loader=LoaderLocal(),
        dlp=DlpDefault(),
    )

    activities = IngestionActivities(pipeline)

    worker = Worker(
        client,
        task_queue="ingestion",
        workflows=[IngestionWorkflow],
        activities=[
            activities.load_data,
            activities.extract_data,
            activities.split_data,
            activities.dlp,
            activities.insert_data,
        ],
    )

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
