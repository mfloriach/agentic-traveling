from pathlib import Path

from database import QdrantDatabase
from feed.loader import LoaderLocal
from feed.parsers import ParserTika
from feed.pipeline import Pipeline
from feed.splitter import Splitter

from .config import Settings

COLLECTION_NAME = "my_collection"

settings = Settings()


def main() -> None:
    pipeline = Pipeline(
        database=QdrantDatabase(
            url=settings.qdrant_host, collection_name=COLLECTION_NAME, batch_size=100
        ),
        parser=ParserTika(url=settings.tika_server_endpoint),
        splitter=Splitter(),
        loader=LoaderLocal(),
    )
    pipeline.run(Path(__file__).resolve().parent.parent / "samples")


if __name__ == "__main__":
    main()
