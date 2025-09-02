import logging
import os
from typing import TypedDict, cast

import boto3
from cv2 import (
    IMWRITE_JPEG_QUALITY,
    INTER_AREA,
    imencode,
    imread,
    resize,
)
from mypy_boto3_dynamodb import DynamoDBClient
from mypy_boto3_s3.client import S3Client
from numpy import uint8
from numpy.typing import NDArray

from lambdas.clients.dynamodb_client import AsciiArtDynamoDbClient
from lambdas.models.font import Font
from lambdas.models.lambda_warm import LambdaEventWarm, LambdaResponseWarm
from lambdas.models.media_file import ImageFile
from lambdas.models.state_table import AsciiArtTableItem, AsciiArtTableStatus
from lambdas.utils.utils import download_from_s3, find_media_type

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MAX_HEIGHT: int = int(os.environ["MAX_HEIGHT"])
STATUS_TABLE_NAME: str = os.environ["STATUS_TABLE_NAME"]

s3_client: S3Client = cast("S3Client", boto3.client("s3"))
# ascii_art_ascii_s3_client: AsciiArtS3Client = AsciiArtS3Client(
#     s3_client=s3_client,
#     bucket_name=ASCII_ART_BUCKET,
# )
dynamo_db_client: DynamoDBClient = cast("DynamoDBClient", boto3.client("dynamodb"))
ascii_dynamo_db_client: AsciiArtDynamoDbClient = AsciiArtDynamoDbClient(
    dynamo_db_client,
    STATUS_TABLE_NAME,
)


class LambdaEvent(TypedDict):
    key: str
    bucket_name: str
    warm: bool


class LambdaResponse(TypedDict):
    key: str
    is_video: bool
    is_image: bool
    bucket_name: str
    processed_key: str
    random_id: str
    dithering: str
    edge_detection: bool
    resolution: int
    output: str


def rescale_image(image: NDArray[uint8], height_to_resize: int) -> NDArray[uint8]:
    height, width = image.shape[:2]

    resized_height: int = height_to_resize // Font.Height.value
    resized_width: int = int(
        resized_height * width * Font.Height.value / (Font.Width.value * height),
    )

    resized_image: NDArray[uint8] = cast(
        "NDArray[uint8]",
        resize(image, (resized_width, resized_height), interpolation=INTER_AREA),
    )
    return resized_image


def lambda_handler(
    event: LambdaEvent | LambdaEventWarm,
    _: None,
) -> LambdaResponse | LambdaResponseWarm:
    logger.info(event)

    if event.get("warm", None):
        return {"warmed": True}

    event = cast("LambdaEvent", event)

    file_path: str = event["key"]
    bucket_name: str = event["bucket_name"]

    image_file: ImageFile = cast("ImageFile", find_media_type(file_path))

    item: AsciiArtTableItem | None = ascii_dynamo_db_client.get_item(
        unique_id=image_file.random_id,
        status=AsciiArtTableStatus.PENDING,
    )
    if item is None:
        raise ValueError("No item found in DynamoDB")

    resolution: int = min(int(item.resolution), MAX_HEIGHT)

    local_file: str = download_from_s3(s3_client, bucket_name, file_path)
    image: NDArray[uint8] = cast("NDArray[uint8]", imread(local_file))

    resized_image: NDArray[uint8] = rescale_image(image, resolution)
    resized_image_name: str = f"{image_file.random_id}/{image_file.file_name}_resized.jpg"
    success, encoded_image_buffer = imencode(
        ".jpg",
        resized_image,
        [IMWRITE_JPEG_QUALITY, 90],
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
        "dithering": item.dithering,
        "edge_detection": item.edge_detection,
        "resolution": resolution,
        "output": item.output,
    }
