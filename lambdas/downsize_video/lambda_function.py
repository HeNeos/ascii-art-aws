import logging
import os
from dataclasses import dataclass
from multiprocessing import cpu_count
from typing import Any, TypedDict, cast

import boto3
from lambda_multiprocessing import Pool
from mypy_boto3_dynamodb import DynamoDBClient
from mypy_boto3_s3.client import S3Client

from lambdas.models.font import Font
from lambdas.models.lambda_warm import LambdaEventWarm, LambdaResponseWarm
from lambdas.models.media_file import VideoExtension, VideoFile
from lambdas.models.state_table import AsciiArtTableItemResponse
from lambdas.utils.ffmpeg import (
    get_video_length,
    get_video_resolution,
    resize_video,
    trim_video,
)
from lambdas.utils.save import save_video
from lambdas.utils.utils import download_from_s3, find_media_type

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client: S3Client = boto3.client("s3")
dynamo_client: DynamoDBClient = boto3.client("dynamodb")

bucket_name: str = os.environ["MEDIA_BUCKET"]
STATUS_TABLE_NAME: str = os.environ["STATUS_TABLE_NAME"]
MAX_HEIGHT: int = int(os.environ["MAX_HEIGHT"])

downsize_video_path: str | None = None


class LambdaEvent(TypedDict):
    key: str
    resolution: str
    warm: bool


class LambdaResponse(TypedDict):
    key: str
    is_video: bool
    is_image: bool
    downsize_video: str
    processed_key: list[str]
    random_id: str
    dithering: str
    edge_detection: bool
    resolution: int
    output: str


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
    return f"00:{minutes:02d}:{(t % 60):02d}"


def save_split_video(video_metadata: SplittedVideo) -> str:
    global downsize_video_path

    if downsize_video_path is None:
        return ""

    trim_video(
        downsize_video_path,
        video_metadata.start_time,
        video_metadata.duration,
        video_metadata.local_path,
    )

    folder_name: str = f"{video_metadata.random_id}/{video_metadata.video_name}/{video_metadata.video_name}"
    key: str = f"{folder_name}-{video_metadata.batch_id:03d}.{video_metadata.video_extension.value}"

    return save_video(
        s3_client=s3_client,
        bucket_name=bucket_name,
        local_video_path=video_metadata.local_path,
        key=f"processed/{key}",
    )


def split_video(video_path: str, media_file: VideoFile) -> list[str]:
    video_duration: float = get_video_length(video_path)
    batch_duration: int = min(max(int(pow(video_duration, 0.63) / 2), 1), 5)

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
                local_path=f"/tmp/{media_file.random_id}-{media_file.file_name}-{batch_id:03d}.{media_file.extension.value}",  # noqa: 501
                batch_id=batch_id,
                video_name=media_file.file_name,
                video_extension=media_file.extension,
                random_id=media_file.random_id,
            ),
        )
        if end_time == -1:
            break
        start_time = end_time
        end_time += batch_duration
        batch_id += 1

    pool = Pool(cpu_count())
    processed_keys: list[str] = pool.map(save_split_video, videos_metadata)
    return processed_keys


def lambda_handler(
    event: LambdaEvent | LambdaEventWarm,
    _: Any,
) -> LambdaResponse | LambdaResponseWarm:
    global downsize_video_path

    logger.info(event)

    if event.get("warm", None):
        return {"warmed": True}

    event = cast("LambdaEvent", event)

    file_path: str = event["key"]
    video_file: VideoFile = cast("VideoFile", find_media_type(file_path))

    response = dynamo_client.get_item(
        TableName=STATUS_TABLE_NAME,
        Key={"id": {"S": video_file.random_id}, "status": {"S": "PENDING"}},
    )

    item: AsciiArtTableItemResponse | None = response.get("Item")
    if item is None:
        raise ValueError("No item found in DynamoDB")

    resolution: int = min(int(item["resolution"]["S"]), MAX_HEIGHT)
    dithering: str = item["dithering"]["S"]
    edge_detection: bool = item["edge_detection"]["BOOL"]
    # output: str = item["dithering"]["S"]
    output: str = "COLOR"

    local_file: str = download_from_s3(
        s3_client=s3_client,
        bucket_name=bucket_name,
        s3_key=file_path,
    )

    video_width, video_height = get_video_resolution(video_path=local_file)
    new_width: int = int(video_width * resolution / video_height)
    if new_width % 2 == 1:
        new_width += 1
    if resolution % 2 == 1:
        resolution += 1
    downsize_height: int = resolution // Font.Height.value
    downsize_width: int = int(
        downsize_height
        * video_width
        * (Font.Height.value / Font.Width.value)
        / video_height,
    )

    if downsize_width % 2 == 1:
        downsize_width += 1

    downsize_video_path = (
        f"/tmp/{video_file.file_name}-downsize.{video_file.extension.value}"
    )
    resize_video(
        video_path=local_file,
        width=downsize_width,
        height=downsize_height,
        output_path=downsize_video_path,
    )

    video_folder_name: str = (
        f"{video_file.random_id}/{video_file.file_name}/{video_file.file_name}"
    )

    downsize_video_key: str = save_video(
        s3_client=s3_client,
        bucket_name=bucket_name,
        local_video_path=f"/tmp/{video_file.file_name}-downsize.{video_file.extension.value}",
        key=f"processed/{video_folder_name}-downsize.{video_file.extension.value}",
    )

    processed_key: list[str] = split_video(
        video_path=downsize_video_path,
        media_file=video_file,
    )

    return {
        "key": file_path,
        "is_video": True,
        "is_image": False,
        "downsize_video": downsize_video_key,
        "processed_key": processed_key,
        "random_id": video_file.random_id,
        "dithering": dithering,
        "edge_detection": edge_detection,
        "resolution": resolution,
        "output": output,
    }
