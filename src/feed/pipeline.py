from abc import ABC, abstractmethod
from collections.abc import Iterable, Iterator
from pathlib import Path

from .chunks import Chunk, Document


class Database(ABC):
    @abstractmethod
    def get_embedding_model(self) -> str:
        pass

    @abstractmethod
    def insert(self, chunks: Iterable[Chunk]) -> None:
        pass


class Loader(ABC):
    @abstractmethod
    def load(self, path: Path) -> Iterator[Path]:
        pass


class Splitter(ABC):
    @abstractmethod
    def split(self, doc: Document) -> Iterator[Chunk]:
        pass


class Parser(ABC):
    @abstractmethod
    def parse(self, file_path: Path) -> Document | None:
        pass


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

    def run(self, path: Path) -> None:
        paths = self.load_data(path)
        documents = self.extract_data(paths)
        chunks = self.split_data(documents)
        self.database.insert(chunks)

        print("finished")
