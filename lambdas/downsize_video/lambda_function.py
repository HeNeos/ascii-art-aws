from dataclasses import dataclass
import logging

import boto3

from lambda_multiprocessing import Pool
from multiprocessing import cpu_count
from typing import cast
from moviepy.editor import VideoFileClip

from lambdas.font import Font
from lambdas.custom_types import VideoExtension, VideoFile
from lambdas.utils import download_from_s3, save_video, find_media_type

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client("s3")

bucket_name: str = ""
video: VideoFileClip | None = None


@dataclass
class SplitVideo:
    start_time: int | None
    end_time: int | None
    local_path: str
    batch_id: int
    video_name: str
    video_extension: VideoExtension


def save_split_video(video_metadata: SplitVideo) -> str:
    if video is None:
        return ""
    splitted_video = video.subclip(
        video_metadata.start_time, video_metadata.end_time
    ).without_audio()
    folder_name = f"{video_metadata.video_name}/{video_metadata.video_name}"
    key = (
        f"{folder_name}-{video_metadata.batch_id:03d}.{video_metadata.video_extension}"
    )
    splitted_video.write_videofile(video_metadata.local_path)
    return save_video(
        s3_client, bucket_name, video_metadata.local_path, f"processed/{key}"
    )


def split_video(video: VideoFileClip, media_file: VideoFile) -> list[str]:
    batch_duration = 1 + int((video.duration**0.5) / 3)

    videos_metadata: list[SplitVideo] = []
    start_time: int = 0
    end_time: int | None = start_time + batch_duration
    batch_id: int = 1
    while True:
        if end_time >= video.duration:
            end_time = None
        videos_metadata.append(
            SplitVideo(
                start_time=start_time,
                end_time=end_time,
                local_path="",
                batch_id=batch_id,
                video_name=media_file.file_name,
                video_extension=media_file.extension,
            )
        )
        if end_time is None:
            break
        start_time = end_time
        end_time += batch_duration
        batch_id += 1

    pool = Pool(cpu_count())
    processed_keys = pool.map(save_split_video, videos_metadata)
    return processed_keys


def lambda_handler(event: dict, _) -> dict:
    global bucket_name
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
        "processed_key": split_video(video_resized, media_file),
    }