from tika import parser
from langchain_core.documents import Document
from pathlib import Path
from collections.abc import Iterator
from .config import splitters
from collections.abc import Iterable
import logging
from ..database import Database

logger = logging.getLogger(__name__)

EXTENSION_SPLITTERS = {
    ".go": "code",
    ".md": "markdown",
    ".markdown": "markdown",
}

class Pipeline:
    def __init__(self, metadata: dict[str, str], batch_size: int = 100):
        self.metadata = metadata
        self.batch_size = batch_size
        self.database = Database()
    
    def load_data(self, path: Path) -> Iterator[Document]:
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")
        
        for file_path in path.iterdir():
            if not file_path.is_file():
                continue
            
            try:
                parsed = parser.from_file(str(file_path))
                
                content = (parsed.get("content") or "").strip()
                if not content:
                    return None

                tika_metadata = parsed.get("metadata", {})
                
                yield Document(
                    page_content=content,
                    metadata={
                        "source": str(file_path),
                        "title": tika_metadata.get("dc:title") or file_path.stem,
                        "extension": file_path.suffix.lower(),
                        "author": tika_metadata.get("dc:creator"),
                        "content_type": tika_metadata.get("Content-Type"),
                        "created": tika_metadata.get("dcterms:created"),
                        "modified": tika_metadata.get("dcterms:modified"),
                        **self.metadata,
                    },
                )
            except Exception:
                logger.exception("Failed to load document: %s", file_path)
                continue

    def split_data(self, documents: Iterable[Document]) -> Iterator[Document]:
        for doc in documents:
            extension = doc.metadata.get("extension", "").lower()
            splitter_name = EXTENSION_SPLITTERS.get(extension, "plain")
            splitter = splitters.get(splitter_name)

            if splitter is None:
                logger.error(
                    "Splitter %r is not configured for %s",
                    splitter_name,
                    doc.metadata.get("source", "unknown"),
                )
                continue

            try:
                yield from splitter.split_documents([doc])
            except (ValueError, TypeError, KeyError):
                logger.exception(
                    "Failed to split document: %s",
                    doc.metadata.get("source", "unknown"),
                )
                continue

    def feed_database(self, chunks: Iterable[Document]) -> None:
        batch: list[Document] = []

        for chunk in chunks:
            batch.append(chunk)

            if len(batch) >= self.batch_size:
                self.database.insert(batch)
                batch.clear()

        # Insert the remaining chunks (fewer than 100).
        if batch:
            self.database.insert(batch)
    
    def run(self, path: str):
        documents = self.load_data(Path(path))
        chunks = self.split_data(documents)
        self.feed_database(list(chunks))