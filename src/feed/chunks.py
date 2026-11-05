import hashlib
import uuid
from dataclasses import dataclass

DOCUMENT_NAMESPACE = uuid.UUID("b7c7d8b2-47c1-4e8a-aad4-4e85b3c7f921")

CHUNK_NAMESPACE = uuid.UUID("f41e7c8a-9b32-4d61-a812-7e5c3f902b46")


def stable_document_id(source: str) -> str:
    return str(uuid.uuid5(DOCUMENT_NAMESPACE, source))


def stable_chunk_id(document_id: str, chunk_index: int) -> str:
    return str(
        uuid.uuid5(
            CHUNK_NAMESPACE,
            f"{document_id}:{chunk_index}",
        )
    )


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
    content_hash: str
    document_hash: str
    schema_version: int
    created_at: str
    updated_at: str
    tenant_id: str
    pii_detected: bool
    version: int = 1
    pii_scrubbing_version: int = 1
    pii_categories: list[str] | None = None
    # document_id
    # source_system
    # document_version
    # effective_date
    # expiry_date
    # owner
    # department
    # security_classification
    # access_permissions
    # last_updated_at
    # document_status


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
