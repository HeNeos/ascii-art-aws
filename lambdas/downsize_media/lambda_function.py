import logging
from typing import TypedDict, cast
from uuid import uuid4

import boto3
from mypy_boto3_s3.client import S3Client
from PIL import Image

from lambdas.custom_types import ImageFile
from lambdas.font import Font
from lambdas.utils import (calculate_scale, download_from_s3, find_media_type,
                           save_image)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client: S3Client = boto3.client("s3")


class LambdaEvent(TypedDict):
    key: str
    bucket_name: str


def rescale_image(image: Image.Image) -> Image.Image:
    width, height = image.size
    rescale: int = calculate_scale(height)
    resized_width: int = int(width * (Font.Height.value / Font.Width.value) // rescale)
    resized_height: int = height // rescale
    resized_image = image.resize((resized_width, resized_height))
    return resized_image


def lambda_handler(event: LambdaEvent, _: dict) -> dict:
    logger.info(event)
    file_path: str = event["key"]
    bucket_name: str = event["bucket_name"]
    random_id: str = uuid4().hex

    image_file: ImageFile = cast(ImageFile, find_media_type(file_path))
    local_file: str = download_from_s3(s3_client, bucket_name, file_path)
    image: Image.Image = Image.open(local_file).convert("RGB")
    resized_image = rescale_image(image)
    resized_image_name = (
        f"{image_file.file_name}_resized-{random_id}.{image_file.extension.value}"
    )

    processed_key: str = save_image(
        s3_client,
        bucket_name,
        resized_image,
        image_file.extension,
        f"processed/{resized_image_name}",
    )
    return {
        "key": file_path,
        "is_video": False,
        "is_image": True,
        "bucket_name": bucket_name,
        "processed_key": processed_key,
        "random_id": random_id,
    }
