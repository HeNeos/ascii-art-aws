import logging
import psutil

import boto3
import cv2

from cv2.typing import MatLike
from multiprocessing import cpu_count
from lambda_multiprocessing import Pool
from typing import cast
from PIL import Image

from lambdas.font import Font
from lambdas.custom_types import (
    FrameData,
    Frames,
    MediaFile,
    ImageFile,
    VideoFile,
    ImageExtension,
    VideoExtension,
)
from lambdas.utils import (
    compress_and_save,
    split_file_name,
    calculate_scale,
    download_from_s3,
    save_image,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)
s3_client = boto3.client("s3")

bucket_name: str = ""
batch_size: int = 200


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


def rescale_image(image: Image.Image, image_file: ImageFile) -> str:
    width, height = image.size
    image_name: str = image_file.file_name
    image_extension: ImageExtension = image_file.extension
    rescale: int = calculate_scale(height)
    resized_width: int = int(width * (Font.Height.value / Font.Width.value) // rescale)
    resized_height: int = height // rescale
    resized_image_name: str = f"{image_name}_resized.{image_extension.value}"
    resized_image = image.resize((resized_width, resized_height))
    return save_image(
        s3_client,
        resized_image,
        image_extension.value,
        bucket_name,
        f"proccessed/{resized_image_name}",
    )


def resize_frame(frame_data: FrameData) -> tuple[Image.Image, int]:
    frame_image: MatLike = cast(MatLike, frame_data.frame)
    height, width, _ = frame_image.shape
    scale = calculate_scale(height)
    return (
        Image.fromarray(
            cv2.cvtColor(
                cv2.resize(
                    frame_image,
                    (
                        int(Font.Height.value / Font.Width.value * width / scale),
                        int(height / scale),
                    ),
                ),
                cv2.COLOR_BGR2RGB,
            )
        ),
        frame_data.frame_id,
    )


def extract_frames(video_capture: cv2.VideoCapture, video_file: VideoFile) -> str:
    frame_id: int = 1
    last_frame_id: int = 1
    video_name: str = video_file.file_name
    continue_proccessing: bool = True

    logger.info(cpu_count())

    while continue_proccessing:
        frames: Frames = []
        for _ in range(batch_size):
            ret, frame = video_capture.read()
            if ret:
                frames.append(
                    FrameData(frame=frame, frame_id=frame_id, video_name=video_name)
                )
                frame_id += 1
            else:
                continue_proccessing = False
                break
        logger.info(f"Finished extract frames: {psutil.virtual_memory()[3]/1000000}")
        pool = Pool(cpu_count())
        resized_frames = pool.map(resize_frame, frames)

        logger.info(f"Finished resize: {psutil.virtual_memory()[3]/1000000}")

        compress_and_save(
            s3_client,
            resized_frames,
            bucket_name,
            f"proccessed/{video_name}/{(last_frame_id):06d}-{frame_id-1:06d}.tar.gz",
        )
        last_frame_id = frame_id
        resized_frames.clear()

        logger.info(f"Finished saving: {psutil.virtual_memory()[3]/1000000}")

    return f"proccessed/{video_name}"


def lambda_handler(event: dict, _) -> dict:
    global bucket_name
    logger.info(event)
    file_path: str = event["Records"][0]["s3"]["object"]["key"]
    bucket_name = event["Records"][0]["s3"]["bucket"]["name"]

    media_file: MediaFile = find_media_type(file_path)
    local_file: str = download_from_s3(s3_client, bucket_name, file_path)

    is_video: bool = media_file.extension in VideoExtension
    is_image: bool = media_file.extension in ImageExtension

    response = {"key": file_path, "is_video": is_video, "is_image": is_image}

    if is_video:
        video_capture: cv2.VideoCapture = cv2.VideoCapture(local_file)
        proccessed_key = extract_frames(video_capture, cast(VideoFile, media_file))
        video_capture.release()
        return {**response, "proccessed_key": proccessed_key}
    if is_image:
        image: Image.Image = Image.open(local_file).convert("RGB")
        proccessed_key = rescale_image(image, cast(ImageFile, media_file))
        return {**response, "proccessed_key": proccessed_key}

    logger.info(response)
    return response
