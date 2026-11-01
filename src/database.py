from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

COLLECTION_NAME = "my_collection"


class Database:
    def __init__(self):
        self.client = QdrantClient(url="http://localhost:6333")
        self.client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=4, distance=Distance.COSINE),
        )

    def insert(self, chunks: Any) -> None:
        batch = 100
        points = [
            PointStruct(
                id=chunk["chunk_id"],
                vector=vector,
                payload={
                    "document_id": chunk["document_id"],
                    "chunk_index": chunk["chunk_index"],
                    "content": chunk["content"],
                },
            )
            for chunk, vector in zip(batch, chunks)
        ]

        self.client.upsert(
            collection_name="documents",
            points=points,
        )
