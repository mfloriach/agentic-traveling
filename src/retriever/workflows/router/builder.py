from langchain_huggingface import HuggingFaceEmbeddings

from src.config import settings
from src.infrastructure.redis import SemanticCacheValkey
from src.infrastructure.semantic_database import QdrantDatabase
from src.retriever.workflows.planner.graph import app as planner_graph
from src.retriever.workflows.router.router import Router, RouterDeps

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

router = Router(
    deps=RouterDeps(
        graph=planner_graph,
        database=QdrantDatabase(
            url=settings.qdrant.host,
            collection_name=settings.qdrant.collection,
            embeddings=embeddings,
        ),
        cache=SemanticCacheValkey(
            embeddings=embeddings,
            host=settings.valkey.host,
            port=settings.valkey.port,
            password=settings.valkey.password,
            database=settings.valkey.database,
        ),
        # reranker=DocumentReranker(
        #     model_name="BAAI/bge-reranker-v2-m3",
        #     top_k=5,
        # ),
    )
)
