from dataclasses import dataclass
import logging
import os
import subprocess

import boto3

from lambda_multiprocessing import Pool
from multiprocessing import cpu_count
from typing import cast
from uuid import uuid4

from lambdas.font import Font
from lambdas.custom_types import VideoExtension, VideoFile
from lambdas.utils import download_from_s3, save_video, find_media_type

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client("s3")

bucket_name: str = os.environ["MEDIA_BUCKET"]
downsize_video_path: str | None = None


@dataclass
class SplitVideo:
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


def run_ffmpeg(command: list):
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error running ffmpeg command: {e}")
        raise


def save_split_video(video_metadata: SplitVideo) -> str:
    if downsize_video_path is None:
        return ""
    ffmpeg_command = [
        "ffmpeg",
        "-ss",
        video_metadata.start_time,
        "-i",
        downsize_video_path,
    ]

    if video_metadata.duration:
        ffmpeg_command += ["-t", video_metadata.duration]

    # It's re-encoding again to avoid miss key-frames
    ffmpeg_command += ["-async", "1", video_metadata.local_path]

    run_ffmpeg(ffmpeg_command)

    folder_name = f"{video_metadata.video_name}-{video_metadata.random_id}/{video_metadata.video_name}"
    key = f"{folder_name}-{video_metadata.batch_id:03d}.{video_metadata.video_extension.value}"
    return save_video(
        s3_client, bucket_name, video_metadata.local_path, f"processed/{key}"
    )


def split_video(video_path: str, media_file: VideoFile, random_id: str) -> list[str]:
    ffmpeg_command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        video_path,
    ]
    result = subprocess.run(ffmpeg_command, capture_output=True, text=True)
    video_duration: float = float(result.stdout.strip())
    batch_duration: int = max(1, int((video_duration**0.5) / 5))

    videos_metadata: list[SplitVideo] = []
    start_time: int = 0
    end_time: int = start_time + batch_duration
    batch_id: int = 1
    while True:
        if video_duration - end_time < min(0.5, batch_duration):
            end_time = -1
        if end_time >= video_duration:
            end_time = -1
        videos_metadata.append(
            SplitVideo(
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

    logger.info("Start splitting")

    pool = Pool(cpu_count())
    processed_keys = pool.map(save_split_video, videos_metadata)
    return processed_keys


def get_video_resolution(path: str) -> tuple[int, int]:
    ffprobe_command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "stream=width,height",
        "-of",
        "csv=s=x:p=0",
        path,
    ]
    ffprobe_result = subprocess.run(ffprobe_command, capture_output=True, text=True)
    video_width, video_height = map(int, ffprobe_result.stdout.strip().split("x"))
    return video_width, video_height


def resize_video(path: str, width: int, height: int, output_path: str):
    ffmpeg_command = [
        "ffmpeg",
        "-i",
        path,
        "-vf",
        f"scale={width}:{height}",
        "-preset",
        "veryfast",
        output_path,
    ]
    run_ffmpeg(ffmpeg_command)


def lambda_handler(event: dict, _) -> dict:
    global downsize_video_path
    logger.info(event)
    file_path: str = event["key"]
    random_id = uuid4().hex

    video_file: VideoFile = cast(VideoFile, find_media_type(file_path))
    local_file: str = download_from_s3(s3_client, bucket_name, file_path)

    video_width, video_height = get_video_resolution(local_file)
    new_height: int = 90
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
