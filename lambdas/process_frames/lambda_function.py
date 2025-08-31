import logging
import os
from shutil import rmtree
from typing import TypedDict, cast

import boto3
from cv2 import (
    CAP_PROP_FPS,
    CAP_PROP_FRAME_HEIGHT,
    CAP_PROP_FRAME_WIDTH,
    COLOR_BGR2RGB,
    VideoCapture,
    cvtColor,
)
from mypy_boto3_s3.client import S3Client
from numpy import str_, uint8
from numpy.typing import NDArray

from lambdas.models.media_file import (
    ImageExtension,
    MediaFile,
    VideoFile,
)
from lambdas.models.r2 import R2Credentials
from lambdas.process.dithering import DitheringStrategy
from lambdas.process.dithering.utils import get_dithering_strategy
from lambdas.process.utils import (
    ascii_convert,
    create_char_array,
    get_ascii_dict,
)
from lambdas.process_frames.modules.frames import FrameData, Frames
from lambdas.utils.ffmpeg import merge_frames
from lambdas.utils.save import save_video
from lambdas.utils.save_image import ImageCairo
from lambdas.utils.utils import (
    download_from_s3,
    find_media_type,
    get_r2_credentials,
    split_file_name,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")
dynamo_client = boto3.client("dynamodb")

DEFAULT_DITHERING: str = os.environ["DEFAULT_DITHERING"]
ASCII_ART_BUCKET: str = os.environ["ASCII_ART_BUCKET"]
MEDIA_BUCKET: str = os.environ["MEDIA_BUCKET"]
R2_SECRETS_BUCKET: str = os.environ["R2_SECRETS_BUCKET"]
STATUS_TABLE_NAME: str = os.environ["STATUS_TABLE_NAME"]

r2_credentials: R2Credentials | None = None
r2_client: S3Client | None = None


class LambdaEvent(TypedDict):
    key: str
    processed_key: str
    is_video: bool
    random_id: str
    dithering: str
    edge_detection: bool
    output: str
    warm: bool


def extract_frames(video_capture: VideoCapture, video_file: VideoFile) -> Frames:
    frame_id: int = 1
    video_name: str = video_file.file_name
    frames: Frames = []

    while True:
        ret, frame = video_capture.read()
        if ret:
            resized_frame: NDArray[uint8] = cast(
                "NDArray[uint8]",
                cvtColor(frame, COLOR_BGR2RGB),
            )
            frames.append(
                FrameData(frame=resized_frame, frame_id=frame_id, video_name=video_name),
            )
            frame_id += 1
        else:
            break

    return frames


def lambda_handler(event: LambdaEvent, _: str) -> dict[str, int | str]:
    logger.info(event)
    if event.get("warm", None):
        return {"warmed": True}
    global r2_credentials

    if r2_credentials is None:
        r2_credentials = get_r2_credentials(s3_client, R2_SECRETS_BUCKET)

    initial_key: str = event["key"]
    video_name, _, random_id = split_file_name(initial_key)
    file_path: str = event["processed_key"]
    dithering: str = event.get("dithering", DEFAULT_DITHERING)
    output: str = event.get("output", "COLOR")
    edge_detection: bool = event.get("edge_detection", False)
    dithering_strategy: type[DitheringStrategy] = get_dithering_strategy(dithering)

    media_file: MediaFile = find_media_type(file_path)
    local_file: str = download_from_s3(s3_client, MEDIA_BUCKET, file_path)

    video_capture: VideoCapture = VideoCapture(local_file)
    width: int = int(video_capture.get(CAP_PROP_FRAME_WIDTH))
    height: int = int(video_capture.get(CAP_PROP_FRAME_HEIGHT))
    video_fps = video_capture.get(CAP_PROP_FPS)
    frames: Frames = extract_frames(video_capture, cast("VideoFile", media_file))
    video_capture.release()
    logger.info("Finish extract frames")
    ascii_dict = get_ascii_dict(width, height, output)
    char_array: NDArray[str_] = create_char_array(ascii_dict)
    ascii_frames: list[ImageCairo] = [
        ImageCairo(
            ascii_convert(
                frame.frame,
                char_array,
                dithering_strategy,
                output,
                edge_detection,
            ),
            ImageExtension.JPG,
        )
        for frame in frames
    ]
    output_dir = os.path.join("/tmp", video_name)
    if os.path.exists(output_dir):
        rmtree(output_dir)
    os.makedirs(output_dir, exist_ok=True)
    frame_paths: list[str] = [
        os.path.join(output_dir, f"{frame_id:04d}.{ImageExtension.JPG.value}")
        for frame_id in range(len(ascii_frames))
    ]
    for i in range(len(ascii_frames)):
        ascii_frames[i].write_to_disk(frame_paths[i])
    logger.info("Finish ascii-ed frames")
    video_path: str = f"/tmp/{video_name}.mp4"
    merge_frames(
        frames_filename=frame_paths,
        frame_rate=video_fps,
        output_path=video_path,
    )
    logger.info("Finish save local video")
    key = save_video(
        s3_client,
        ASCII_ART_BUCKET,
        video_path,
        f"{random_id}/{video_name}/{media_file.file_name}_ascii.{media_file.extension.value}",  # noqa: 501
    )
    return {
        "statusCode": 200,
        "ascii_art_key": key,
    }
