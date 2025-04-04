import io
from typing import cast, Any

from mypy_boto3_s3.client import S3Client
from lambdas.utils.custom_types import ImageExtension
from abc import ABC, abstractmethod


class AbstractImage(ABC):
    def __init__(self, image: Any, image_format: ImageExtension) -> None:
        self.image = image
        self.buffer: io.BytesIO | None = None
        self.image_format: ImageExtension = image_format

    @abstractmethod
    def write_to_buffer(
        self,
    ) -> None:
        pass

    def save_image(self, s3_client: S3Client, bucket_name: str, key: str) -> str:
        assert self.buffer is not None
        self.buffer.seek(0)
        s3_client.put_object(
            Body=self.buffer.getvalue(),
            Bucket=bucket_name,
            ContentType=f"image/{self.image_format.value}",
            Key=key,
        )
        return key


class ImagePillow(AbstractImage):
    def write_to_buffer(
        self,
    ) -> None:
        from PIL import Image

        with io.BytesIO() as buffer:
            self.image = cast(Image.Image, self.image)
            self.image.save(buffer, format=self.image_format.value)
            self.buffer = buffer


class ImageCairo(AbstractImage):
    def write_to_buffer(
        self,
    ) -> None:
        from cairo import ImageSurface

        with io.BytesIO() as buffer:
            self.image = cast(ImageSurface, self.image)
            self.image_format = ImageExtension.PNG
            self.image.write_to_png(buffer)


def save_video(
    s3_client: S3Client, bucket_name: str, local_video_path: str, key: str
) -> str:
    with open(local_video_path, "rb") as f:
        s3_client.upload_fileobj(f, bucket_name, key)
        return key
