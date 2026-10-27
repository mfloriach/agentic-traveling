
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from .feed.config import embeddings

COLLECTION = "document"

class VectorDB:
    def __init__(self, collection: str, embeddings: Embeddings, url: str = "http://localhost:6333"):
        self.collection = collection
        self.embeddings = embeddings
        self.client = QdrantClient(url=url)

        self.store = QdrantVectorStore(
            client=self.client,
            collection_name=collection,
            embedding=embeddings,
        ) if self.client.collection_exists(collection) else None

    def insert(self, chunks: list[Document]) -> None:
        self.store.add_documents(chunks)

    def retrieve(self, query: str, k: int = 3,) -> list[Document]:
        return self.store.similarity_search(query, k=k)

    def close(self) -> None:
        self.client.close()



database = VectorDB(collection=COLLECTION, embeddings=embeddings)