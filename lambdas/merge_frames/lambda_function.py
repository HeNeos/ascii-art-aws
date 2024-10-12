import logging
import os

import boto3

from moviepy.editor import (
    CompositeAudioClip,
    AudioFileClip,
    concatenate_videoclips,
)
from lambdas.utils import (
    download_from_s3,
    save_video,
    split_file_name,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")

MEDIA_BUCKET = os.environ["MEDIA_BUCKET"]
ASCII_ART_BUCKET = os.environ["ASCII_ART_BUCKET"]
AUDIO_BUCKET = os.environ["AUDIO_BUCKET"]


def lambda_handler(event: dict, _) -> dict:
    logger.info(event)
    initial_key: str = event["key"]
    audio_key: str = event["audio_key"]
    splitted_videos_key: list[str] = event["videos_key"]

    audio_local_path: str = download_from_s3(s3_client, AUDIO_BUCKET, audio_key)
    audio_clip: AudioFileClip = AudioFileClip(audio_local_path)
    audio: list[AudioFileClip] = CompositeAudioClip([audio_clip])

    videos_local_path: list[str] = [
        download_from_s3(s3_client, ASCII_ART_BUCKET, video_key)
        for video_key in splitted_videos_key
    ]

    video_name, video_extension = split_file_name(initial_key)

    video = concatenate_videoclips(videos_local_path)
    video.audio = audio
    video.write_videofile(f"/tmp/video.{video_extension}")

    video_key = save_video(
        s3_client,
        ASCII_ART_BUCKET,
        f"/tmp/video.{video_extension}",
        f"{video_name}/{video_name}.{video_extension}",
    )

    return {"bucket": ASCII_ART_BUCKET, "output": video_key}
