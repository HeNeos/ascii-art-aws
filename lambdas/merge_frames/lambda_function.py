import json
import logging
import os
from typing import TypedDict, cast

import boto3
from mypy_boto3_dynamodb import DynamoDBClient
from mypy_boto3_s3.client import S3Client

from lambdas.clients.dynamodb_client import AsciiArtDynamoDbClient
from lambdas.clients.s3_client import AsciiArtS3Client
from lambdas.models.lambda_warm import LambdaEventWarm, LambdaResponseWarm
from lambdas.models.r2 import R2Credentials
from lambdas.models.state_table import AsciiArtTableStatus
from lambdas.utils.ffmpeg import add_audio_to_video, merge_videos
from lambdas.utils.utils import (
    get_r2_credentials,
    split_file_name,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

MEDIA_BUCKET: str = os.environ["MEDIA_BUCKET"]
ASCII_ART_BUCKET: str = os.environ["ASCII_ART_BUCKET"]
AUDIO_BUCKET: str = os.environ["AUDIO_BUCKET"]
R2_SECRETS_BUCKET: str = os.environ["R2_SECRETS_BUCKET"]
STATUS_TABLE_NAME: str = os.environ["STATUS_TABLE_NAME"]

s3_client: S3Client = cast("S3Client", boto3.client("s3"))
ascii_art_ascii_s3_client: AsciiArtS3Client = AsciiArtS3Client(
    s3_client=s3_client,
    bucket_name=ASCII_ART_BUCKET,
)
ascii_art_audio_s3_client: AsciiArtS3Client = AsciiArtS3Client(
    s3_client=s3_client,
    bucket_name=AUDIO_BUCKET,
)
dynamo_db_client: DynamoDBClient = cast("DynamoDBClient", boto3.client("dynamodb"))
ascii_dynamo_db_client: AsciiArtDynamoDbClient = AsciiArtDynamoDbClient(
    dynamo_db_client,
    STATUS_TABLE_NAME,
)

r2_credentials: R2Credentials | None = None


class LambdaEvent(TypedDict):
    key: str
    audio_key: str
    videos_key: list[str]
    random_id: str
    warm: bool


class LambdaResponse(TypedDict):
    statusCode: int
    ascii_art_key: str
    body: str


def lambda_handler(
    event: LambdaEvent | LambdaEventWarm,
    _: None,
) -> LambdaResponse | LambdaResponseWarm:
    global r2_credentials

    logger.info(event)

    if event.get("warm", None):
        return {"warmed": True}

    event = cast("LambdaEvent", event)

    if r2_credentials is None:
        r2_credentials = get_r2_credentials(
            s3_client=s3_client,
            bucket_name=R2_SECRETS_BUCKET,
        )

    initial_key: str = event["key"]
    audio_key: str = event["audio_key"]
    splitted_videos_key: list[str] = event["videos_key"]
    has_audio: bool = len(audio_key) > 0

    videos_local_path: list[str] = [
        ascii_art_ascii_s3_client.download_to_local(s3_key=video_key)
        for video_key in splitted_videos_key
    ]

    video_name, video_extension, random_id = split_file_name(initial_key)

    merged_video_path: str = f"/tmp/video_merged-{random_id}.{video_extension}"
    merge_videos(videos_local_path, merged_video_path)

    final_video_path: str = merged_video_path
    if has_audio:
        audio_local_path: str = ascii_art_audio_s3_client.download_to_local(
            s3_key=audio_key,
        )
        final_video_path = f"/tmp/video_with_audio-{random_id}.{video_extension}"
        add_audio_to_video(
            video_path=merged_video_path,
            audio_path=audio_local_path,
            output_path=final_video_path,
        )

    ascii_art_r2_client: AsciiArtS3Client = AsciiArtS3Client.get_r2_client(
        credentials=r2_credentials,
    )

    video_key: str = ascii_art_r2_client.save_from_local(
        local_path=final_video_path,
        key=f"{random_id}/{video_name}/{video_name}_ascii.{video_extension}",
    )

    url: str = ascii_art_r2_client.s3_client.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": r2_credentials.ascii_art_bucket_name, "Key": video_key},
        ExpiresIn=300,
    )

    ascii_dynamo_db_client.put_item(
        unique_id=random_id,
        status=AsciiArtTableStatus.FINISHED,
        url=url,
    )

    return {
        "statusCode": 200,
        "ascii_art_key": video_key,
        "body": json.dumps({"url": url}),
    }
