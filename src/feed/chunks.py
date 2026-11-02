import hashlib
import uuid
from dataclasses import dataclass

NAMESPACE = uuid.UUID("b7c7d8b2-47c1-4e8a-aad4-4e85b3c7f921")


def stable_document_id(source: str) -> str:
    return str(uuid.uuid5(NAMESPACE, source))


def stable_chunk_id(document_id: str, chunk_index: int) -> str:
    return str(uuid.uuid5(NAMESPACE, f"{document_id}:{chunk_index}"))


def content_hash(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


@dataclass
class Chunk:
    chunk_id: str
    document_id: str
    chunk_index: int
    content: str
    source_uri: str
    source_type: str
    # embedding_model: str
    content_hash: str
    document_hash: str
    schema_version: int
    created_at: str
    updated_at: str
    tenant_id: str


@dataclass
class Document:
    id: str
    source_uri: str
    content: str
    author: str | None
    content_type: str | None
    document_hash: str
    title: str
    created: str | None
    modified: str | None
    extension: str
