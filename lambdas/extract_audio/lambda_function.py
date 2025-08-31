import logging
import os
from typing import TypedDict, cast

import boto3
from mypy_boto3_s3.client import S3Client

from lambdas.clients.s3_client import AsciiArtS3Client
from lambdas.models.lambda_warm import LambdaEventWarm, LambdaResponseWarm
from lambdas.models.media_file import VideoFile
from lambdas.utils.ffmpeg import extract_audio
from lambdas.utils.utils import find_media_type

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AUDIO_BUCKET = os.environ["AUDIO_BUCKET"]
MEDIA_BUCKET = os.environ["MEDIA_BUCKET"]

s3_client: S3Client = boto3.client("s3")
ascii_art_media_s3_client: AsciiArtS3Client = AsciiArtS3Client(
    s3_client=s3_client,
    bucket_name=MEDIA_BUCKET,
)
ascii_art_audio_s3_client: AsciiArtS3Client = AsciiArtS3Client(
    s3_client=s3_client,
    bucket_name=AUDIO_BUCKET,
)


class LambdaEvent(TypedDict):
    downsize_video: str
    random_id: str
    key: str
    warm: bool


class LambdaResponse(TypedDict):
    key: str
    audio_bucket: str
    audio_key: str
    random_id: str


def lambda_handler(
    event: LambdaEvent | LambdaEventWarm,
    _: None,
) -> LambdaResponse | LambdaResponseWarm:
    logger.info(event)

    if event.get("warm", None):
        return {"warmed": True}

    event = cast("LambdaEvent", event)

    file_path: str = event["downsize_video"]
    video_file: VideoFile = cast("VideoFile", find_media_type(file_path))
    local_file: str = ascii_art_media_s3_client.download_to_local(s3_key=file_path)

    audio_file_name: str = f"{video_file.file_name}-{video_file.random_id}"
    audio_path: str = f"/tmp/{audio_file_name}.mp3"
    extract_audio(local_file, audio_path)

    # TODO: check if audio_path has a size
    if audio_path is None:
        processed_key = ""
    else:
        processed_key: str = f"{audio_file_name}/audio.mp3"
        ascii_art_audio_s3_client.save_from_local(
            local_path=audio_path,
            key=processed_key,
        )

    return {
        "key": event["key"],
        "audio_bucket": AUDIO_BUCKET,
        "audio_key": processed_key,
        "random_id": video_file.random_id,
    }
