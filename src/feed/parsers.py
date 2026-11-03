from pathlib import Path
from typing import Any, TypedDict, cast

from tika import parser  # type: ignore[import-not-found, import-untyped]

from .chunks import Document, content_hash, stable_document_id


class TikaResult(TypedDict):
    metadata: dict[str, Any]
    content: str | None


class ParserTika:
    def __init__(self, url: str) -> None:
        self._tika_server = url

    def parse(self, file_path: Path) -> Document | None:
        parsed = cast(
            TikaResult,
            parser.from_file(
                filename=str(file_path),
                serverEndpoint=self._tika_server,
            ),
        )

        content = parsed["metadata"]["tk:content"]
        if not content:
            return None

        metadata = parsed["metadata"]

        return Document(
            id=stable_document_id(str(file_path)),
            title=metadata.get("dc:title") or file_path.stem,
            source_uri=str(file_path),
            content=content,
            author=metadata.get("dc:creator"),
            content_type=metadata.get("Content-Type"),
            document_hash=content_hash(content),
            created=metadata.get("dcterms:created"),
            modified=metadata.get("dcterms:modified"),
            extension=file_path.suffix,
        )
