import logging

import boto3

from typing import cast
from moviepy.editor import VideoFileClip

from lambdas.font import Font
from lambdas.custom_types import VideoFile
from lambdas.utils import download_from_s3, save_video, find_media_type

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client("s3")


def split_video(
    video: VideoFileClip, media_file: VideoFile, bucket_name: str
) -> list[str]:
    video_folder_name = f"{media_file.file_name}/{media_file.file_name}"
    batch_duration = 1 + int((video.duration**0.5) / 3)

    start_time: int = 0
    end_time: int = start_time + batch_duration
    batch_id: int = 1
    continue_splitting: bool = True
    processed_keys: list[str] = []
    while continue_splitting:
        if end_time >= video.duration:
            splitted_video = video.subclip(start_time, None).without_audio()
            continue_splitting = False
        else:
            splitted_video = video.subclip(start_time, end_time).without_audio()
        s3_splitted_video_key = (
            f"{video_folder_name}-{batch_id:03d}.{media_file.extension.value}"
        )
        local_splitted_video_path = (
            f"/tmp/{media_file.file_name}-{batch_id:03d}.{media_file.extension.value}"
        )
        splitted_video.write_videofile(local_splitted_video_path)
        processed_keys.append(
            save_video(
                s3_client,
                bucket_name,
                local_splitted_video_path,
                f"processed/{s3_splitted_video_key}",
            )
        )
        start_time = end_time
        end_time += batch_duration
        batch_id += 1
    return processed_keys


def lambda_handler(event: dict, _) -> dict:
    logger.info(event)
    file_path: str = event["key"]
    bucket_name = event["bucket_name"]

    media_file: VideoFile = cast(VideoFile, find_media_type(file_path))
    local_file: str = download_from_s3(s3_client, bucket_name, file_path)

    video = VideoFileClip(local_file)
    video_width, video_height = video.size
    scale_factor = 90 / video_height

    video_resized = video.resize(
        newsize=(
            int(Font.Height.value / Font.Width.value * scale_factor * video_width),
            90,
        )
    )

    video_folder_name = f"{media_file.file_name}/{media_file.file_name}"
    video_resized.write_videofile(
        f"/tmp/{media_file.file_name}-downsize.{media_file.extension.value}",
        temp_audiofile=f"/tmp/{media_file.file_name}-downsize.mp3",
    )

    save_video(
        s3_client,
        bucket_name,
        f"/tmp/{media_file.file_name}-downsize.{media_file.extension.value}",
        f"processed/{video_folder_name}-downsize.{media_file.extension.value}",
    )

    return {
        "key": file_path,
        "is_video": True,
        "is_image": False,
        "bucket_name": bucket_name,
        "downsize_video": f"processed/{video_folder_name}-downsize.{media_file.extension.value}",
        "processed_key": split_video(video_resized, media_file, bucket_name),
    }
