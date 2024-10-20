from dataclasses import dataclass
import logging
import os

import boto3

from lambda_multiprocessing import Pool
from multiprocessing import cpu_count
from typing import cast
from uuid import uuid4

from lambdas.font import Font
from lambdas.ffmpeg import (
    get_video_length,
    trim_video,
    get_video_resolution,
    resize_video,
)
from lambdas.custom_types import VideoExtension, VideoFile
from lambdas.utils import download_from_s3, save_video, find_media_type

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client("s3")

bucket_name: str = os.environ["MEDIA_BUCKET"]
downsize_video_path: str | None = None


@dataclass
class SplittedVideo:
    start_time: str
    duration: str | None
    local_path: str
    batch_id: int
    video_name: str
    video_extension: VideoExtension
    random_id: str


def convert_time(t: int) -> str:
    minutes = t // 60
    return f"00:{minutes:02d}:{(t%60):02d}"


def save_split_video(video_metadata: SplittedVideo) -> str:
    if downsize_video_path is None:
        return ""

    trim_video(
        downsize_video_path,
        video_metadata.start_time,
        video_metadata.duration,
        video_metadata.local_path,
    )

    folder_name = f"{video_metadata.video_name}-{video_metadata.random_id}/{video_metadata.video_name}"
    key = f"{folder_name}-{video_metadata.batch_id:03d}.{video_metadata.video_extension.value}"
    return save_video(
        s3_client, bucket_name, video_metadata.local_path, f"processed/{key}"
    )


def split_video(video_path: str, media_file: VideoFile, random_id: str) -> list[str]:
    video_duration: float = get_video_length(video_path)
    batch_duration: int = max(1, int((video_duration**0.5) / 6))

    videos_metadata: list[SplittedVideo] = []
    start_time: int = 0
    end_time: int = start_time + batch_duration
    batch_id: int = 1
    while True:
        if video_duration - end_time < min(0.5, batch_duration):
            end_time = -1
        if end_time >= video_duration:
            end_time = -1
        videos_metadata.append(
            SplittedVideo(
                start_time=convert_time(start_time),
                duration=convert_time(batch_duration) if end_time > 0 else None,
                local_path=f"/tmp/{media_file.file_name}-{batch_id:03d}.{media_file.extension.value}",
                batch_id=batch_id,
                video_name=media_file.file_name,
                video_extension=media_file.extension,
                random_id=random_id,
            )
        )
        if end_time == -1:
            break
        start_time = end_time
        end_time += batch_duration
        batch_id += 1

    pool = Pool(cpu_count())
    processed_keys = pool.map(save_split_video, videos_metadata)
    return processed_keys


def lambda_handler(event: dict, _) -> dict:
    global downsize_video_path
    logger.info(event)
    file_path: str = event["key"]
    random_id = uuid4().hex

    video_file: VideoFile = cast(VideoFile, find_media_type(file_path))
    local_file: str = download_from_s3(s3_client, bucket_name, file_path)

    video_width, video_height = get_video_resolution(local_file)
    new_height: int = 80
    scale_factor: float = new_height / video_height
    new_width = int(Font.Height.value / Font.Width.value * scale_factor * video_width)
    if new_width % 2 == 1:
        new_width += 1

    downsize_video_path = (
        f"/tmp/{video_file.file_name}-downsize.{video_file.extension.value}"
    )
    resize_video(local_file, new_width, new_height, downsize_video_path)

    video_folder_name = f"{video_file.file_name}-{random_id}/{video_file.file_name}"

    downsize_video_key = save_video(
        s3_client,
        bucket_name,
        f"/tmp/{video_file.file_name}-downsize.{video_file.extension.value}",
        f"processed/{video_folder_name}-downsize.{video_file.extension.value}",
    )

    processed_key = split_video(downsize_video_path, video_file, random_id)

    return {
        "key": file_path,
        "is_video": True,
        "is_image": False,
        "downsize_video": downsize_video_key,
        "processed_key": processed_key,
        "random_id": random_id,
    }
