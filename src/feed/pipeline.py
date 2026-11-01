import logging
import uuid
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any, TypedDict, cast

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import (
    Language,
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
from tika import parser  # type: ignore[import-untyped]

COLLECTION_NAME = "my_collection"

TIKA_SERVER = "http://localhost:9998"

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

splitters = {
    "text/x-go": RecursiveCharacterTextSplitter.from_language(
        language=Language.GO,
        chunk_size=1000,
        chunk_overlap=100,
    ),
    "text/markdown": MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
        ]
    ),
    "text/plain": RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50),
}


class TikaResult(TypedDict):
    metadata: dict[str, Any]
    content: str | None


logger = logging.getLogger(__name__)

EXTENSION_SPLITTERS = {
    ".go": "text/x-go",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
}


class Pipeline:
    def __init__(self, metadata: dict[str, str] = {}, batch_size: int = 100):
        self.metadata = metadata
        self.batch_size = batch_size
        self.client = QdrantClient(url="http://localhost:6333")
        # self.client.create_collection(
        #     collection_name=COLLECTION_NAME,
        #     vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        # )

    def load_data(self, path: Path) -> Iterator[Path]:
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")

        for file_path in path.iterdir():
            if not file_path.is_file():
                continue

            yield file_path

    def extract_data(self, paths: Iterable[Path]) -> Iterator[Document]:
        for path in paths:
            parsed = cast(
                TikaResult,
                parser.from_file(
                    filename=str(path),
                    serverEndpoint=TIKA_SERVER,
                ),
            )

            content = parsed["metadata"]["tk:content"]
            if not content:
                continue

            metadata = parsed["metadata"]

            yield Document(
                page_content=content,
                metadata={
                    "id": str(uuid.uuid4()),
                    "source": str(path),
                    "title": metadata.get("dc:title") or path.stem,
                    "extension": path.suffix.lower(),
                    "author": metadata.get("dc:creator"),
                    "content_type": metadata.get("Content-Type"),
                    "created": metadata.get("dcterms:created"),
                    "modified": metadata.get("dcterms:modified"),
                    **self.metadata,
                },
            )

    def split_data(self, documents: Iterable[Document]) -> Iterator[dict[str, Any]]:
        for doc in documents:
            extension = doc.metadata.get("extension", "").lower()
            splitter_name = EXTENSION_SPLITTERS.get(extension, "text/plain")
            splitter = splitters.get(splitter_name)

            texts = cast(MarkdownHeaderTextSplitter, splitter).split_text(
                doc.page_content
            )

            for index, text in enumerate(texts):
                yield {
                    "chunk_id": str(uuid.uuid4()),
                    "document_id": doc.id,
                    "chunk_index": index,
                    "content": text,
                    "source": doc.metadata["source"],
                    "title": doc.metadata["title"],
                }

    def feed_database(self, chunks: Iterable[dict[str, Any]]) -> None:
        batch: list[dict[str, Any]] = []

        for chunk in chunks:
            batch.append(chunk)

            if len(batch) >= self.batch_size:
                self._insert_batch(batch)
                batch.clear()

        if batch:
            self._insert_batch(batch)

    def _insert_batch(self, batch: list[dict[str, Any]]) -> None:
        texts = [chunk["content"] for chunk in batch]

        print(texts)

        vectors = embeddings.embed_documents(texts)

        points = [
            PointStruct(
                id=chunk["chunk_id"],
                vector=vector,
                payload={
                    **chunk,
                    "content": chunk["content"],
                },
            )
            for chunk, vector in zip(batch, vectors)
        ]

        print(points)

        self.client.upsert(
            collection_name=COLLECTION_NAME,
            points=points,
            wait=True,
        )

        logger.info("Inserted %d chunks into Qdrant", len(points))

    def run(self, path: str) -> None:
        paths = self.load_data(Path(path))
        documents = self.extract_data(paths)
        chunks = self.split_data(documents)
        self.feed_database(chunks)

        print("finished")
