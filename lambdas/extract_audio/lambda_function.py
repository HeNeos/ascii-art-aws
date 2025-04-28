import logging
import os
from typing import TypedDict, cast

import boto3

from lambdas.utils.custom_types import VideoFile
from lambdas.utils.utils import download_from_s3, find_media_type
from lambdas.utils.ffmpeg import extract_audio

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client("s3")


AUDIO_BUCKET = os.environ["AUDIO_BUCKET"]
MEDIA_BUCKET = os.environ["MEDIA_BUCKET"]


class LambdaEvent(TypedDict):
    downsize_video: str
    random_id: str
    key: str
    warm: bool


def lambda_handler(event: LambdaEvent, _: dict) -> dict:
    logger.info(event)
    if event.get("warm", None):
        return {"warmed": True}
    file_path: str = event["downsize_video"]
    video_file: VideoFile = cast(VideoFile, find_media_type(file_path))
    local_file: str = download_from_s3(s3_client, MEDIA_BUCKET, file_path)

    audio_file_name = f"{video_file.file_name}-{video_file.random_id}"
    audio_path: str = f"/tmp/{audio_file_name}.mp3"
    extract_audio(local_file, audio_path)

    if audio_path is None:  # TODO: check if audio_path has a size
        processed_key = ""
    else:
        processed_key = f"{audio_file_name}/audio.mp3"
        with open(audio_path, "rb") as f:
            s3_client.upload_fileobj(f, AUDIO_BUCKET, processed_key)

    return {
        "key": event["key"],
        "audio_bucket": AUDIO_BUCKET,
        "audio_key": processed_key,
        "random_id": video_file.random_id,
    }
