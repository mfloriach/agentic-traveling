from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Protocol

from .chunks import Chunk, Document


class Database(Protocol):
    def insert(self, chunks: Iterable[Chunk], batch_size: int) -> None: ...


class Loader(Protocol):
    def load(self, path: Path) -> Iterator[Path]: ...


class Splitter(Protocol):
    def split(self, doc: Document) -> Iterator[Chunk]: ...


class Parser(Protocol):
    def parse(self, file_path: Path) -> Document | None: ...


class Pipeline:
    def __init__(
        self,
        database: Database,
        parser: Parser,
        splitter: Splitter,
        loader: Loader,
    ):
        self.database = database
        self.parser = parser
        self.splitter = splitter
        self.loader = loader

    def load_data(self, path: Path) -> Iterator[Path]:
        yield from self.loader.load(path)

    def extract_data(self, paths: Iterable[Path]) -> Iterator[Document]:
        for path in paths:
            document = self.parser.parse(file_path=path)
            if not document:
                continue

            yield document

    def split_data(self, documents: Iterable[Document]) -> Iterator[Chunk]:
        for doc in documents:
            yield from self.splitter.split(doc)

    def dlp(self, chunks: Iterable[Chunk]) -> Iterator[Chunk]:
        yield from chunks

    def run(self, path: Path) -> None:
        paths = self.load_data(path)
        documents = self.extract_data(paths)
        chunks = self.split_data(documents)
        self.database.insert(chunks, batch_size=100)

        print("finished")
