from langchain_huggingface import HuggingFaceEmbeddings

from src.config import settings
from src.redis import SemanticCacheValkey
from src.retriever.workflows.planner.graph import app as planner_graph
from src.retriever.workflows.router.router import Router, RouterDeps
from src.semantic_database import QdrantDatabase

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

router = Router(
    deps=RouterDeps(
        graph=planner_graph,
        database=QdrantDatabase(
            url=settings.qdrant_host,
            collection_name=settings.collection_name,
            embeddings=embeddings,
        ),
        cache=SemanticCacheValkey(embeddings=embeddings),
        # reranker=DocumentReranker(
        #     model_name="BAAI/bge-reranker-v2-m3",
        #     top_k=5,
        # ),
    )
)
