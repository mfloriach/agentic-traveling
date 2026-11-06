from collections.abc import Iterator
from datetime import datetime
from typing import cast

from langchain_text_splitters import (  # type: ignore[import-not-found, import-untyped]
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from src.injestor.utils import scrub_pii

from .chunks import Chunk, Document, content_hash, stable_chunk_id

splitters = {
    "text/markdown": MarkdownHeaderTextSplitter(
        headers_to_split_on=[
            ("#", "h1"),
            ("##", "h2"),
            ("###", "h3"),
        ]
    ),
    "text/plain": RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100),
}

EXTENSION_SPLITTERS = {
    ".go": "text/x-go",
    ".md": "text/markdown",
    ".markdown": "text/markdown",
}


class Splitter:
    def split(self, doc: Document) -> Iterator[Chunk]:
        splitter_name = EXTENSION_SPLITTERS.get(doc.extension, "text/plain")
        splitter = splitters.get(splitter_name)

        texts = cast(MarkdownHeaderTextSplitter, splitter).split_text(doc.content)
        for index, text in enumerate(texts):
            content, detected = scrub_pii(text.page_content)

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
