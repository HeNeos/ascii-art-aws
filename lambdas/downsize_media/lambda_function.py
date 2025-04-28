import logging
import os
from typing import TypedDict, cast

import boto3
from mypy_boto3_s3.client import S3Client
from numpy import uint8
from numpy.typing import NDArray
from cv2 import (
    IMWRITE_JPEG_QUALITY,
    INTER_AREA,
    imread,
    resize,
    imencode,
)

from lambdas.utils.custom_types import ImageFile
from lambdas.utils.font import Font
from lambdas.utils.utils import download_from_s3, find_media_type

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client: S3Client = boto3.client("s3")
dynamo_client = boto3.client("dynamodb")

MAX_HEIGHT: int = int(os.environ["MAX_HEIGHT"])
STATUS_TABLE_NAME: str = os.environ["STATUS_TABLE_NAME"]


class LambdaEvent(TypedDict):
    key: str
    bucket_name: str


def rescale_image(image: NDArray[uint8], height_to_resize: int) -> NDArray[uint8]:
    height, width = image.shape[:2]

    resized_height: int = height_to_resize // Font.Height.value
    resized_width: int = int(
        resized_height * width * Font.Height.value / (Font.Width.value * height)
    )

    resized_image: NDArray[uint8] = cast(
        NDArray[uint8],
        resize(image, (resized_width, resized_height), interpolation=INTER_AREA),
    )
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
    image: NDArray[uint8] = cast(NDArray[uint8], imread(local_file))

    resized_image = rescale_image(image, resolution)
    resized_image_name = f"{image_file.random_id}/{image_file.file_name}_resized.jpg"
    success, encoded_image_buffer = imencode(
        ".jpg", resized_image, [IMWRITE_JPEG_QUALITY, 90]
    )
    if not success:
        raise ValueError("Error: Failed to encode resized image")
    image_bytes = encoded_image_buffer.tobytes()
    s3_client.put_object(
        Bucket=bucket_name,
        Key=f"processed/{resized_image_name}",
        Body=image_bytes,
        ContentType="image/jpeg",
    )
    return {
        "key": file_path,
        "is_video": False,
        "is_image": True,
        "bucket_name": bucket_name,
        "processed_key": f"processed/{resized_image_name}",
        "random_id": image_file.random_id,
        "dithering": dithering,
        "resolution": resolution,
        "output": output,
    }
