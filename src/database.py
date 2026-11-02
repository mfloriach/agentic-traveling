from typing import Iterable

from langchain_community.embeddings import (
    HuggingFaceEmbeddings,  # type: ignore[import-not-found, import-untyped]
)
from qdrant_client import QdrantClient  # type: ignore[import-not-found, import-untyped]
from qdrant_client.models import (  # type: ignore[import-not-found, import-untyped]
    Distance,
    Document,
    Modifier,
    PointStruct,
    SparseVectorParams,
    VectorParams,
)

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
                vectors_config={
                    "dense": VectorParams(
                        size=384,
                        distance=Distance.COSINE,
                    )
                },
                sparse_vectors_config={
                    "bm25": SparseVectorParams(
                        modifier=Modifier.IDF,  # Computes IDF score server-side
                    )
                },
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

        points = []
        for chunk, vector in zip(batch, vectors):
            points.append(
                PointStruct(
                    id=chunk.chunk_id,
                    vector={
                        "dense": vector,
                        "bm25": Document(
                            text=chunk.content,
                            model="Qdrant/bm25",
                        ),
                    },
                    payload={
                        **chunk.__dict__,
                        "embedding_model": self.get_embedding_model(),
                    },
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
        )
