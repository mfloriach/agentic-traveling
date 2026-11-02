from pathlib import Path

from database import QdrantDatabase
from feed.loader import LoaderLocal
from feed.parsers import ParserTika
from feed.pipeline import Pipeline
from feed.splitter import Splitter

COLLECTION_NAME = "my_collection"


def main() -> None:
    pipeline = Pipeline(
        database=QdrantDatabase(collection_name=COLLECTION_NAME, batch_size=100),
        parser=ParserTika(),
        splitter=Splitter(),
        loader=LoaderLocal(),
    )
    pipeline.run(Path("./samples"))


if __name__ == "__main__":
    main()
