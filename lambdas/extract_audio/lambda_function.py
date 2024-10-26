import logging
import os
from typing import TypedDict, cast

import boto3
from moviepy.editor import AudioFileClip, VideoFileClip

from lambdas.custom_types import VideoFile
from lambdas.utils import download_from_s3, find_media_type

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client("s3")


AUDIO_BUCKET = os.environ["AUDIO_BUCKET"]
MEDIA_BUCKET = os.environ["MEDIA_BUCKET"]


class LambdaEvent(TypedDict):
    downsize_video: str
    random_id: str
    key: str


def lambda_handler(event: LambdaEvent, _: dict) -> dict:
    logger.info(event)
    file_path: str = event["downsize_video"]
    random_id: str = event["random_id"]

    video_file: VideoFile = cast(VideoFile, find_media_type(file_path))
    local_file: str = download_from_s3(s3_client, MEDIA_BUCKET, file_path)

    video = VideoFileClip(local_file)
    audio_clip: AudioFileClip | None = video.audio
    if audio_clip is None:
        processed_key = ""
    else:
        audio_clip.write_audiofile("/tmp/audio.mp3")
        processed_key = f"{video_file.file_name}-{random_id}/audio.mp3"
        with open("/tmp/audio.mp3", "rb") as f:
            s3_client.upload_fileobj(f, AUDIO_BUCKET, processed_key)

    return {
        "key": event["key"],
        "audio_bucket": AUDIO_BUCKET,
        "audio_key": processed_key,
        "random_id": random_id,
    }
