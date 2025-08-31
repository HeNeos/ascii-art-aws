import logging
import os
from json import dumps
from shutil import rmtree
from typing import TypedDict, cast

import boto3
from cv2 import COLOR_BGR2RGB, cvtColor, imread
from mypy_boto3_dynamodb import DynamoDBClient
from mypy_boto3_s3.client import S3Client
from numpy import uint8
from numpy.typing import NDArray

from lambdas.clients.dynamodb_client import AsciiArtDynamoDbClient
from lambdas.clients.s3_client import AsciiArtS3Client
from lambdas.models.media_file import (
    ImageExtension,
    MediaFile,
)
from lambdas.models.r2 import R2Credentials
from lambdas.models.state_table import AsciiArtTableStatus
from lambdas.process.dithering import DitheringStrategy
from lambdas.process.dithering.utils import get_dithering_strategy
from lambdas.process.utils import (
    ascii_convert,
    create_char_array,
    get_ascii_dict,
)
from lambdas.utils.save_image import ImageCairo
from lambdas.utils.utils import (
    find_media_type,
    get_r2_credentials,
    split_file_name,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

DEFAULT_DITHERING: str = os.environ["DEFAULT_DITHERING"]
ASCII_ART_BUCKET: str = os.environ["ASCII_ART_BUCKET"]
MEDIA_BUCKET: str = os.environ["MEDIA_BUCKET"]
R2_SECRETS_BUCKET: str = os.environ["R2_SECRETS_BUCKET"]
STATUS_TABLE_NAME: str = os.environ["STATUS_TABLE_NAME"]

s3_client: S3Client = boto3.client("s3")
ascii_art_media_s3_client: AsciiArtS3Client = AsciiArtS3Client(
    s3_client=s3_client,
    bucket_name=MEDIA_BUCKET,
)
dynamo_db_client: DynamoDBClient = boto3.client("dynamodb")
ascii_dynamo_db_client: AsciiArtDynamoDbClient = AsciiArtDynamoDbClient(
    dynamo_db_client,
    STATUS_TABLE_NAME,
)


r2_credentials: R2Credentials | None = None


class LambdaEvent(TypedDict):
    key: str
    processed_key: str
    is_video: bool
    random_id: str
    dithering: str
    edge_detection: bool
    output: str
    warm: bool


def lambda_handler(event: LambdaEvent, _: str) -> dict[str, int | str]:
    if event.get("warm", None):
        return {"warmed": True}
    global r2_credentials

    if r2_credentials is None:
        r2_credentials = get_r2_credentials(s3_client, R2_SECRETS_BUCKET)

    initial_key: str = event["key"]
    _, _, random_id = split_file_name(initial_key)
    file_path: str = event["processed_key"]
    dithering: str = event.get("dithering", DEFAULT_DITHERING)
    output: str = event.get("output", "COLOR")
    dithering_strategy: type[DitheringStrategy] = get_dithering_strategy(dithering)
    edge_detection: bool = event.get("edge_detection", False)

    media_file: MediaFile = find_media_type(file_path)
    local_file: str = ascii_art_media_s3_client.download_to_local(s3_key=file_path)

    image: NDArray[uint8] = cast(
        "NDArray[uint8]",
        cvtColor(imread(local_file), COLOR_BGR2RGB),
    )

    height, width = image.shape[:2]
    ascii_dict = get_ascii_dict(width, height, output)

    char_array = create_char_array(ascii_dict)
    ascii_image = ascii_convert(
        image,
        char_array,
        dithering_strategy,
        output,
        edge_detection,
    )
    image_object: ImageCairo = ImageCairo(
        ascii_image,
        ImageExtension(media_file.extension),
    )
    # TODO: fix, this line apply the postprocessing and save it to local file.
    post_processed_local_file: str = f"/tmp/{random_id}/{media_file.file_name}_ascii.jpg"
    output_dir = os.path.join("/tmp", random_id)
    if os.path.exists(output_dir):
        rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)

    image_object.write_to_disk(post_processed_local_file)

    object_key: str = (
        f"{random_id}/{media_file.file_name}_ascii.{media_file.extension.value}"
    )

    ascii_art_r2_client: AsciiArtS3Client = AsciiArtS3Client.get_r2_client(
        credentials=r2_credentials,
    )
    ascii_art_r2_client.save_from_local(
        local_path=post_processed_local_file,
        key=object_key,
    )

    url: str = ascii_art_r2_client.s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": r2_credentials.ascii_art_bucket_name,
            "Key": object_key,
        },
        ExpiresIn=300,
    )

    ascii_dynamo_db_client.put_item(
        unique_id=random_id,
        status=AsciiArtTableStatus.FINISHED,
        url=url,
    )

    return {
        "statusCode": 200,
        "ascii_art_key": object_key,
        "body": dumps({"url": url}),
    }
