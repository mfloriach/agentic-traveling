from pathlib import Path

from langchain_huggingface import HuggingFaceEmbeddings

from database import QdrantDatabase
from feed.loader import LoaderLocal
from feed.parsers import ParserTika
from feed.pipeline import Pipeline
from feed.splitter import Splitter

from .config import settings


def main() -> None:
    pipeline = Pipeline(
        database=QdrantDatabase(
            url=settings.qdrant_host,
            collection_name=settings.collection_name,
            embeddings=HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            ),
        ),
        parser=ParserTika(url=settings.tika_server_endpoint),
        splitter=Splitter(),
        loader=LoaderLocal(),
    )
    pipeline.run(Path(__file__).resolve().parent.parent / "samples")


if __name__ == "__main__":
    main()
