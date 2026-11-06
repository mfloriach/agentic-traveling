from collections.abc import Iterable

from langchain_huggingface import HuggingFaceEmbeddings
from qdrant_client import QdrantClient  # type: ignore[import-not-found, import-untyped]
from qdrant_client.models import (  # type: ignore[import-not-found, import-untyped]
    Distance,
    Document,
    Fusion,
    FusionQuery,
    Modifier,
    PointStruct,
    Prefetch,
    ScoredPoint,
    SparseVectorParams,
    VectorParams,
)

from src.injestor.chunks import Chunk


class QdrantDatabase:
    def __init__(
        self, url: str, collection_name: str, embeddings: HuggingFaceEmbeddings
    ):
        self.collection_name = collection_name
        self.client = QdrantClient(url=url)
        self.embeddings = embeddings

        if self.client.collection_exists(self.collection_name):
            return

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
                    modifier=Modifier.IDF,
                )
            },
        )

        # # Create indexes for fields used by retrieval filters.
        # for field in ("tenant_id", "document_id", "version"):
        #     client.create_payload_index(
        #         collection_name=COLLECTION,
        #         field_name=field,
        #         field_schema=models.PayloadSchemaType.KEYWORD,
        #     )

    def _get_embedding_model(self) -> str:
        return self.embeddings.model_name

    def insert(self, chunks: Iterable[Chunk], batch_size: int = 100) -> None:
        batch: list[Chunk] = []

        for chunk in chunks:
            batch.append(chunk)

            if len(batch) >= batch_size:
                self._insert(batch)
                batch.clear()

        if batch:
            self._insert(batch)

    def _insert(self, batch: list[Chunk]) -> None:
        texts = [chunk.content for chunk in batch]
        vectors = self.embeddings.embed_documents(texts)

        points = []
        for chunk, vector in zip(batch, vectors, strict=False):
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
                        "embedding_model": self._get_embedding_model(),
                    },
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True,
            parallel=1,
            max_retries=3,
        )

    def search(self, query: str, limit: int = 5) -> list[ScoredPoint]:
        dense_vector = self.embeddings.embed_query(query)

        results = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                Prefetch(
                    query=dense_vector,
                    using="dense",
                    limit=50,
                ),
                Prefetch(
                    query=Document(
                        text=query,
                        model="Qdrant/bm25",
                    ),
                    using="bm25",
                    limit=50,
                ),
            ],
            query=FusionQuery(
                fusion=Fusion.RRF,
            ),
            limit=limit,
            with_payload=True,
        )

        return results.points
