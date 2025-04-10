import json
import logging
import os
from typing import TypedDict, cast

import boto3
from mypy_boto3_s3 import S3Client
from time import time

from lambdas.utils.custom_types import R2Credentials
from lambdas.utils.ffmpeg import add_audio_to_video, merge_videos
from lambdas.utils.utils import (
    download_from_s3,
    split_file_name,
    get_r2_credentials,
    get_r2_client,
)
from lambdas.utils.save import save_video

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client: S3Client = boto3.client("s3")
dynamo_client = boto3.client("dynamodb")


MEDIA_BUCKET: str = os.environ["MEDIA_BUCKET"]
ASCII_ART_BUCKET: str = os.environ["ASCII_ART_BUCKET"]
AUDIO_BUCKET: str = os.environ["AUDIO_BUCKET"]
R2_SECRETS_BUCKET: str = os.environ["R2_SECRETS_BUCKET"]
STATUS_TABLE_NAME: str = os.environ["STATUS_TABLE_NAME"]

r2_credentials: R2Credentials | None = None
r2_client: S3Client | None = None


class LambdaEvent(TypedDict):
    key: str
    audio_key: str
    videos_key: list[str]
    random_id: str


def lambda_handler(event: LambdaEvent, _: dict) -> dict:
    logger.info(event)
    global r2_credentials
    global r2_client

    if r2_credentials is None:
        r2_credentials = get_r2_credentials(s3_client, R2_SECRETS_BUCKET)

    initial_key: str = event["key"]
    audio_key: str = event["audio_key"]
    splitted_videos_key: list[str] = event["videos_key"]
    has_audio: bool = len(audio_key) > 0

    videos_local_path: list[str] = [
        download_from_s3(s3_client, ASCII_ART_BUCKET, video_key)
        for video_key in splitted_videos_key
    ]

    video_name, video_extension, random_id = split_file_name(initial_key)

    merged_video_path = f"/tmp/video_merged-{random_id}.{video_extension}"
    merge_videos(videos_local_path, merged_video_path)

    if has_audio:
        audio_local_path: str = download_from_s3(s3_client, AUDIO_BUCKET, audio_key)
        final_video_path = f"/tmp/video_with_audio-{random_id}.{video_extension}"
        add_audio_to_video(merged_video_path, audio_local_path, final_video_path)
    else:
        final_video_path = merged_video_path

        # video_key = save_video(
        #     s3_client,
        #     ASCII_ART_BUCKET,
        #     final_video_path,
        #     f"{random_id}/{video_name}/{video_name}_ascii.{video_extension}",
        # )

        # url: str = s3_client.generate_presigned_url(
        #     "get_object",
        #     Params={
        #         "Bucket": ASCII_ART_BUCKET,
        #         "Key": video_key,
        #     },
        #     ExpiresIn=300,
        # )

    video_key = save_video(
        get_r2_client(r2_credentials, r2_client),
        r2_credentials.ascii_art_bucket_name,
        final_video_path,
        f"{random_id}/{video_name}/{video_name}_ascii.{video_extension}",
    )

    url: str = get_r2_client(r2_credentials, r2_client).generate_presigned_url(
        "get_object",
        Params={
            "Bucket": r2_credentials.ascii_art_bucket_name,
            "Key": video_key,
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
        "ascii_art_key": video_key,
        "body": json.dumps(cast(dict[str, str], {"url": url})),
    }
