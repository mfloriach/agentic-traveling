from collections.abc import Iterator
from pathlib import Path


class LoaderLocal:
    def load(self, path: Path) -> Iterator[Path]:
        if not path.is_dir():
            raise NotADirectoryError(f"Not a directory: {path}")

        for file_path in path.iterdir():
            if not file_path.is_file():
                continue

            yield file_path
