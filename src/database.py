from typing import Iterable

from langchain_community.embeddings import HuggingFaceEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from feed.chunks import Chunk

COLLECTION_NAME = "my_collection"
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


class QdrantDatabase:
    def __init__(self, collection_name: str = COLLECTION_NAME, batch_size: int = 100):
        self.collection_name = collection_name
        self.batch_size = batch_size
        self.client = QdrantClient(url="http://localhost:6333")
        if not self.client.collection_exists(collection_name=collection_name):
            self.client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

    def get_embedding_model(self) -> str:
        return embeddings.model_name

    def insert(self, chunks: Iterable[Chunk]) -> None:
        batch: list[Chunk] = []

        for chunk in chunks:
            batch.append(chunk)

            if len(batch) >= self.batch_size:
                self._insert(batch)
                batch.clear()

        if batch:
            self._insert(batch)

    def _insert(self, batch: list[Chunk]) -> None:
        texts = [chunk.content for chunk in batch]

        vectors = embeddings.embed_documents(texts)

        points = [
            PointStruct(
                id=chunk.chunk_id,
                vector=vector,
                payload={
                    **chunk.__dict__,
                    "content": chunk.content,
                },
            )
            for chunk, vector in zip(batch, vectors)
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )
