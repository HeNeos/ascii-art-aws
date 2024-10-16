import json
import logging
import os

import boto3

from typing import cast
from lambdas.utils import (
    download_from_s3,
    save_video,
    split_file_name,
)
from lambdas.ffmpeg import add_audio_to_video, merge_videos

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
    random_id = event["random_id"]
    has_audio: bool = len(audio_key) > 0

    videos_local_path: list[str] = [
        download_from_s3(s3_client, ASCII_ART_BUCKET, video_key)
        for video_key in splitted_videos_key
    ]

    video_name, video_extension = split_file_name(initial_key)

    merged_video_path = f"/tmp/video_merged-{random_id}.{video_extension}"
    merge_videos(videos_local_path, merged_video_path)

    if has_audio:
        audio_local_path: str = download_from_s3(s3_client, AUDIO_BUCKET, audio_key)
        final_video_path = f"/tmp/video_with_audio-{random_id}.{video_extension}"
        add_audio_to_video(merged_video_path, audio_local_path, final_video_path)
    else:
        final_video_path = merged_video_path

    video_key = save_video(
        s3_client,
        ASCII_ART_BUCKET,
        final_video_path,
        f"{video_name}-{random_id}/{video_name}_ascii.{video_extension}",
    )

    url: str = s3_client.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": ASCII_ART_BUCKET,
            "Key": video_key,
        },
        ExpiresIn=300,
    )

    return {
        "statusCode": 200,
        "ascii_art_key": video_key,
        "body": json.dumps(cast(dict[str, str], {"url": url})),
    }
