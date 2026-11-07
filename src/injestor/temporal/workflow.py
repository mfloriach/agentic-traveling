from dataclasses import asdict
from datetime import timedelta
from pathlib import Path

from temporalio import activity, workflow
from temporalio.common import RetryPolicy

from ..chunks import Chunk, Document
from ..pipeline import Pipeline


@workflow.defn
class IngestionWorkflow:
    @workflow.run
    async def run(self, path: str) -> None:
        retry_policy = RetryPolicy(maximum_attempts=3)

        paths = await workflow.execute_activity(
            "load_data",
            path,
            result_type=list[str],
            start_to_close_timeout=timedelta(minutes=5),
            retry_policy=retry_policy,
        )

        documents = await workflow.execute_activity(
            "extract_data",
            paths,
            result_type=list[dict],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        chunks = await workflow.execute_activity(
            "split_data",
            documents,
            result_type=list[dict],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        chunks = await workflow.execute_activity(
            "dlp",
            chunks,
            result_type=list[dict],
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )

        await workflow.execute_activity(
            "insert_data",
            chunks,
            start_to_close_timeout=timedelta(minutes=10),
            retry_policy=retry_policy,
        )


class IngestionActivities:
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline

    @activity.defn(name="load_data")
    def load_data(self, path: str) -> list[str]:
        return [str(p) for p in self.pipeline.load_data(Path(path))]

    @activity.defn(name="extract_data")
    def extract_data(self, paths: list[str]) -> list[dict]:
        documents = self.pipeline.extract_data(Path(p) for p in paths)
        return [asdict(doc) for doc in documents]

    @activity.defn(name="split_data")
    def split_data(self, documents: list[dict]) -> list[dict]:
        chunks = self.pipeline.split_data(Document(**doc) for doc in documents)
        return [asdict(chunk) for chunk in chunks]

    @activity.defn(name="dlp")
    def dlp(self, chunks: list[dict]) -> list[dict]:
        processed = self.pipeline.apply_dlp(Chunk(**chunk) for chunk in chunks)
        return [asdict(chunk) for chunk in processed]

    @activity.defn(name="insert_data")
    def insert_data(self, chunks: list[dict]) -> None:
        self.pipeline.database.insert(
            (Chunk(**chunk) for chunk in chunks),
            batch_size=100,
        )
