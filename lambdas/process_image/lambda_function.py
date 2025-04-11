import logging
import os

import boto3

from typing import TypedDict, cast
from json import dumps
from time import time

from PIL import Image
from mypy_boto3_s3.client import S3Client

from lambdas.utils.custom_types import (
    ImageExtension,
    MediaFile,
    R2Credentials,
)
from lambdas.process.utils import (
    create_char_array,
    get_ascii_dict,
    ascii_convert,
)
from lambdas.process.dithering import DitheringStrategy
from lambdas.process.dithering.utils import get_dithering_strategy
from lambdas.utils.utils import (
    download_from_s3,
    find_media_type,
    get_r2_credentials,
    split_file_name,
    get_r2_client,
)
from lambdas.utils.save import ImageCairo


logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")
dynamo_client = boto3.client("dynamodb")

DEFAULT_DITHERING: str = os.environ["DEFAULT_DITHERING"]
ASCII_ART_BUCKET: str = os.environ["ASCII_ART_BUCKET"]
MEDIA_BUCKET: str = os.environ["MEDIA_BUCKET"]
R2_SECRETS_BUCKET: str = os.environ["R2_SECRETS_BUCKET"]
STATUS_TABLE_NAME: str = os.environ["STATUS_TABLE_NAME"]

r2_credentials: R2Credentials | None = None
r2_client: S3Client | None = None


class LambdaEvent(TypedDict):
    key: str
    processed_key: str
    is_video: bool
    random_id: str
    dithering: str
    output: str


def lambda_handler(event: LambdaEvent, _: str) -> dict[str, int | str]:
    logger.info(event)
    global r2_credentials

    if r2_credentials is None:
        r2_credentials = get_r2_credentials(s3_client, R2_SECRETS_BUCKET)

    initial_key: str = event["key"]
    _, _, random_id = split_file_name(initial_key)
    file_path: str = event["processed_key"]
    dithering: str = event.get("dithering", DEFAULT_DITHERING)
    output: str = event.get("output", "COLOR")
    dithering_strategy: type[DitheringStrategy] = get_dithering_strategy(dithering)

    media_file: MediaFile = find_media_type(file_path)
    local_file: str = download_from_s3(s3_client, MEDIA_BUCKET, file_path)

    image: Image.Image = Image.open(local_file).convert("RGB")
    width, height = image.size
    ascii_dict = get_ascii_dict(width, height, output)

    char_array = create_char_array(ascii_dict)
    ascii_image = ascii_convert(image, char_array, dithering_strategy, output)
    image_object: ImageCairo = ImageCairo(
        ascii_image, ImageExtension(media_file.extension)
    )
    image_object.write_to_buffer()
    # key = image_object.save_image(
    #     s3_client,
    #     ASCII_ART_BUCKET,
    #     f"{random_id}/{media_file.file_name}_ascii.{media_file.extension.value}",
    # )
    # url: str = s3_client.generate_presigned_url(
    #     "get_object",
    #     Params={
    #         "Bucket": ASCII_ART_BUCKET,
    #         "Key": key,
    #     },
    #     ExpiresIn=300,
    # )
    key = image_object.save_image(
        get_r2_client(r2_credentials, r2_client),
        r2_credentials.ascii_art_bucket_name,
        f"{random_id}/{media_file.file_name}_ascii.{media_file.extension.value}",
    )
    url: str = get_r2_client(r2_credentials, r2_client).generate_presigned_url(
        "get_object",
        Params={
            "Bucket": r2_credentials.ascii_art_bucket_name,
            "Key": key,
        },
        ExpiresIn=300,
    )
    dynamo_client.put_item(
        TableName=STATUS_TABLE_NAME,
        Item={
            "status": {"S": "FINISHED"},
            "id": {"S": random_id},
            "url": {"S": url},
            "ttl": {"N": str(int(time() + 300))},
        },
    )
    return {
        "statusCode": 200,
        "ascii_art_key": key,
        "body": dumps(cast(dict[str, str], {"url": url})),
    }
