from collections.abc import Iterator

from ..chunks import Chunk


class DlpDefault:
    def run(self, chunk: Chunk) -> Iterator[Chunk]:
        yield chunk
