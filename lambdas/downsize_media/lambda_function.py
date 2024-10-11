import logging
import boto3

from typing import cast
from PIL import Image

from lambdas.font import Font
from lambdas.custom_types import (
    MediaFile,
    ImageFile,
    ImageExtension,
)
from lambdas.utils import (
    calculate_scale,
    download_from_s3,
    save_image,
    find_media_type,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client("s3")


def rescale_image(image: Image.Image, image_file: ImageFile, bucket_name: str) -> str:
    width, height = image.size
    image_name: str = image_file.file_name
    image_extension: ImageExtension = image_file.extension
    rescale: int = calculate_scale(height)
    resized_width: int = int(width * (Font.Height.value / Font.Width.value) // rescale)
    resized_height: int = height // rescale
    resized_image_name: str = f"{image_name}_resized.{image_extension.value}"
    resized_image = image.resize((resized_width, resized_height))
    return save_image(
        s3_client,
        bucket_name,
        resized_image,
        image_extension,
        f"processed/{resized_image_name}",
    )


def lambda_handler(event: dict, _) -> dict:
    logger.info(event)
    file_path: str = event["key"]
    bucket_name = event["bucket_name"]

    media_file: MediaFile = find_media_type(file_path)
    local_file: str = download_from_s3(s3_client, bucket_name, file_path)
    image: Image.Image = Image.open(local_file).convert("RGB")
    return {
        "key": file_path,
        "is_video": False,
        "is_image": True,
        "bucket_name": bucket_name,
        "processed_key": rescale_image(image, cast(ImageFile, media_file), bucket_name),
    }
