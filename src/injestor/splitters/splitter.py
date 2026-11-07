from collections.abc import Iterator
from datetime import datetime

from ..chunks import Chunk, Document, content_hash, stable_chunk_id
from .split import splitters
from .utils import scrub_pii


class Splitter:
    def split(self, doc: Document) -> Iterator[Chunk]:
        texts = splitters.get(doc.content_type, "text/plain").split(doc.content)
        for index, text in enumerate(texts):
            content, detected = scrub_pii(text)

            yield Chunk(
                chunk_id=stable_chunk_id(doc.id, index),
                document_id=doc.id,
                chunk_index=index,
                content=content,
                source_uri=doc.source_uri,
                source_type="file",
                content_hash=content_hash(content),
                document_hash=doc.document_hash,
                schema_version=1,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
                tenant_id="default",
                pii_detected=detected,
                pii_categories=["EMAIL", "ID_NUMBER"] if detected else None,
            )
