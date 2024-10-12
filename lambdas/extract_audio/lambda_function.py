import logging
import os

import boto3

from typing import cast
from moviepy.editor import VideoFileClip

from lambdas.custom_types import VideoFile
from lambdas.utils import download_from_s3, find_media_type

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client("s3")


AUDIO_BUCKET = os.environ["AUDIO_BUCKET"]
MEDIA_BUCKET = os.environ["MEDIA_BUCKET"]


def lambda_handler(event: dict, _) -> dict:
    logger.info(event)
    file_path: str = event["downsize_video"]

    video_file: VideoFile = cast(VideoFile, find_media_type(file_path))
    local_file: str = download_from_s3(s3_client, MEDIA_BUCKET, file_path)

    video = VideoFileClip(local_file)
    audio_clip = video.audio
    audio_clip.write_audiofile("/tmp/audio.mp3")

    processed_key = f"{video_file.file_name}/audio.mp3"

    with open("/tmp/audio.mp3", "rb") as f:
        s3_client.upload_fileobj(f, AUDIO_BUCKET, processed_key)

    return {
        "audio_bucket": AUDIO_BUCKET,
        "audio_key": processed_key,
    }
