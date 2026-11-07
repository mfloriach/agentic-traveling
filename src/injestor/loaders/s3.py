from collections.abc import Iterator
from pathlib import Path
from tempfile import TemporaryDirectory

import boto3


class LoaderS3:
    def __init__(self, bucket_name: str, region: str) -> None:
        session = boto3.Session(region_name=region)
        self.bucket = session.resource("s3").Bucket(bucket_name)

    def load(self, path: Path) -> Iterator[Path]:
        prefix = str(path).strip("/")

        with TemporaryDirectory() as temp_dir:
            for obj in self.bucket.objects.filter(Prefix=prefix):
                if obj.key.endswith("/"):
                    continue

                filename = Path(obj.key).name
                local_path = Path(temp_dir) / filename

                self.bucket.download_file(
                    obj.key,
                    str(local_path),
                )

                yield local_path
