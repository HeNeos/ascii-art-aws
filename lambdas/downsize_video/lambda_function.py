import logging

import boto3
import moviepy.editor as mp

from typing import cast

from lambdas.font import Font
from lambdas.custom_types import (
    MediaFile,
    ImageFile,
    VideoFile,
    ImageExtension,
    VideoExtension,
)
from lambdas.utils import split_file_name, download_from_s3, save_video

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client("s3")

bucket_name: str = ""


def find_media_type(file_path: str) -> MediaFile:
    file_name, file_extension = split_file_name(file_path)
    if file_extension in ImageExtension._value2member_map_:
        if ImageExtension(file_extension) is ImageExtension.JPG:
            return ImageFile(file_name, ImageExtension.JPEG)
        else:
            return ImageFile(file_name, ImageExtension(file_extension))
    if file_extension in VideoExtension._value2member_map_:
        return VideoFile(file_name, VideoExtension(file_extension))

    raise ValueError(f"Unsupported file extension: {file_extension}")


def lambda_handler(event: dict, _) -> dict:
    global bucket_name
    logger.info(event)
    file_path: str = event["Records"][0]["s3"]["object"]["key"]
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]

    media_file: VideoFile = cast(VideoFile, find_media_type(file_path))
    local_file: str = download_from_s3(s3_client, bucket_name, file_path)

    response = {
        "key": file_path,
        "bucket_name": bucket_name,
    }

    video = mp.VideoFileClip(local_file)
    video_width, video_height = video.size
    scale_factor = 180 / video_height

    video_resized = video.resize(
        height=180,
        width=int(Font.Height.value / Font.Width.value * scale_factor * video_width),
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

    batch_duration = 1 + int((video.duration**0.5) / 2)

    start_time: int = 0
    end_time: int = start_time + batch_duration
    batch_id: int = 1
    continue_splitting: bool = True
    processed_keys: list[str] = []
    while continue_splitting:
        logger.info([batch_id, start_time, end_time, video.duration])
        if end_time >= video.duration:
            splitted_video = video_resized.subclip(start_time, None).without_audio()
            continue_splitting = False
        else:
            splitted_video = video_resized.subclip(start_time, end_time).without_audio()
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

    return {**response, "processed_key": processed_keys}
