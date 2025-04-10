import logging
import os
from typing import TypedDict, cast

import boto3
from mypy_boto3_s3.client import S3Client
from PIL import Image

from lambdas.utils.custom_types import ImageFile
from lambdas.utils.font import Font
from lambdas.utils.utils import download_from_s3, find_media_type

from lambdas.utils.save import ImagePillow

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client: S3Client = boto3.client("s3")
dynamo_client = boto3.client("dynamodb")

MAX_HEIGHT: int = int(os.environ["MAX_HEIGHT"])
STATUS_TABLE_NAME: str = os.environ["STATUS_TABLE_NAME"]


class LambdaEvent(TypedDict):
    key: str
    bucket_name: str


def rescale_image(image: Image.Image, height_to_resize: int) -> Image.Image:
    width, height = image.size

    resized_height: int = height_to_resize // Font.Height.value
    resized_width: int = int(
        resized_height * width * Font.Height.value / (Font.Width.value * height)
    )

    resized_image = image.resize((resized_width, resized_height))
    return resized_image


def lambda_handler(event: LambdaEvent, _: dict) -> dict:
    logger.info(event)
    file_path: str = event["key"]
    bucket_name: str = event["bucket_name"]

    image_file: ImageFile = cast(ImageFile, find_media_type(file_path))

    response: dict | None = dynamo_client.get_item(
        TableName=STATUS_TABLE_NAME,
        Key={"id": {"S": image_file.random_id}, "status": {"S": "PENDING"}},
    ).get("Item")

    if response is None:
        raise ValueError("No item found in DynamoDB")

    resolution: int = min(int(response["resolution"]["S"]), MAX_HEIGHT)
    dithering: str = response["dithering"]["S"]
    output: str = response["output"]["S"]

    local_file: str = download_from_s3(s3_client, bucket_name, file_path)
    image: Image.Image = Image.open(local_file).convert("RGB")

    resized_image = rescale_image(image, resolution)
    resized_image_name = f"{image_file.random_id}/{image_file.file_name}_resized.{image_file.extension.value}"

    image_object: ImagePillow = ImagePillow(resized_image, image_file.extension)
    image_object.write_to_buffer()

    processed_key: str = image_object.save_image(
        s3_client,
        bucket_name,
        f"processed/{resized_image_name}",
    )
    return {
        "key": file_path,
        "is_video": False,
        "is_image": True,
        "bucket_name": bucket_name,
        "processed_key": processed_key,
        "random_id": image_file.random_id,
        "dithering": dithering,
        "resolution": resolution,
        "output": output,
    }
