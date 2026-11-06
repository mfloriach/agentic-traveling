import uuid

import numpy as np
import valkey
from langchain_huggingface import HuggingFaceEmbeddings
from valkey.client import Pipeline
from valkey.commands.search.field import TagField, VectorField
from valkey.commands.search.indexDefinition import IndexDefinition, IndexType
from valkey.commands.search.query import Query
from valkey.exceptions import ResponseError


class SemanticCacheValkey:
    INDEX_NAME = "semantic_cache_idx"
    PREFIX = "semantic_cache:"
    DIMENSIONS = 384

    def __init__(
        self,
        embeddings: HuggingFaceEmbeddings,
        host: str,
        port: int,
        password: str,
        database: int,
    ):
        self.redis = valkey.Valkey(
            host=host,
            port=port,
            db=database,
            decode_responses=True,
            password=password,
        )
        self.embeddings = embeddings
        self._create_index()

    def _create_index(self) -> None:
        try:
            self.redis.ft(self.INDEX_NAME).info()
            return
        except ResponseError:
            pass

        schema = (
            TagField("tenant_id"),
            VectorField(
                "embedding",
                "HNSW",
                {
                    "TYPE": "FLOAT32",
                    "DIM": self.DIMENSIONS,
                    "DISTANCE_METRIC": "COSINE",
                },
            ),
        )

        definition = IndexDefinition(
            prefix=[self.PREFIX],
            index_type=IndexType.HASH,
        )

        self.redis.ft(self.INDEX_NAME).create_index(
            fields=schema,
            definition=definition,
        )

    def get(
        self,
        query: str,
        tenant_id: str,
        threshold: float = 0.95,
        limit: int = 5,
    ) -> str | None:

        embedding = np.asarray(
            self.embeddings.embed_query(query),
            dtype=np.float32,
        ).tobytes()

        search_query = (
            Query(
                f"(@tenant_id:{{{tenant_id}}})"
                f"=>[KNN {limit} @embedding $vec AS distance]"
            )
            .sort_by("distance")
            .return_fields("answer", "distance")
            .paging(0, limit)
            .dialect(2)
        )

        results = self.redis.ft(self.INDEX_NAME).search(
            search_query,
            {"vec": embedding},
        )

        if isinstance(results, Pipeline):
            return None

        if not results.docs:
            return None

        best_match = results.docs[0]
        distance = float(best_match.distance)

        similarity = 1.0 - distance

        if similarity < threshold:
            return None

        return best_match.answer

    def set(
        self,
        query: str,
        answer: str,
        tenant_id: str,
        ttl: int = 3600,
    ) -> None:

        embedding = np.asarray(
            self.embeddings.embed_query(query),
            dtype=np.float32,
        ).tobytes()

        key = f"{self.PREFIX}{uuid.uuid4()}"

        self.redis.hset(
            key,
            mapping={
                "query": query,
                "answer": answer,
                "tenant_id": tenant_id,
                "embedding": embedding,
            },
        )

        self.redis.expire(key, ttl)
