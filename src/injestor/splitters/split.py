import csv
from io import StringIO
from typing import Protocol

from langchain_text_splitters import (  # type: ignore[import-not-found, import-untyped]
    HTMLHeaderTextSplitter,
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)


class TextSplitter(Protocol):
    def split(self, text: str) -> list[str]: ...


class MarkdownSplitter:
    def __init__(self) -> None:
        self.splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "h1"),
                ("##", "h2"),
                ("###", "h3"),
            ]
        )

    def split(self, text: str) -> list[str]:
        documents = self.splitter.split_text(text)
        return [doc.page_content for doc in documents]


class RecursiveSplitter:
    def __init__(self) -> None:
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
        )

    def split(self, text: str) -> list[str]:
        documents = self.splitter.split_text(text)
        return [doc for doc in documents]


class HTMLSplitter:
    def __init__(self) -> None:
        self.splitter = HTMLHeaderTextSplitter(
            headers_to_split_on=[
                ("h1", "h1"),
                ("h2", "h2"),
                ("h3", "h3"),
            ]
        )

    def split(self, text: str) -> list[str]:
        return [doc.page_content for doc in self.splitter.split_text(text)]


class CSVSplitter:
    def __init__(self) -> None:
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=100,
        )

    def split(self, text: str) -> list[str]:
        reader = csv.DictReader(StringIO(text))

        if not reader.fieldnames:
            return []

        headers = reader.fieldnames
        rows = []

        for row in reader:
            content = " | ".join(
                f"{header}: {row.get(header, '') or ''}" for header in headers
            )
            rows.append(content)

        return self.splitter.split_text("\n".join(rows))


splitters: dict[str, TextSplitter] = {
    "text/markdown": MarkdownSplitter(),
    "text/plain": RecursiveSplitter(),
    "text/html": HTMLSplitter(),
    "text/csv": CSVSplitter(),
}
