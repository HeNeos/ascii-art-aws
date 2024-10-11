import logging
import os
from typing import cast

import cv2
import numpy as np

import boto3

from cv2.typing import MatLike
from moviepy.editor import ImageSequenceClip
from PIL import Image
from lambdas.process_frames.modules.ascii_dict import AsciiDict
from lambdas.process_frames.modules.utils import create_ascii_image, map_to_char
from lambdas.utils import (
    download_from_s3,
    find_media_type,
    save_image,
    save_video,
)
from lambdas.custom_types import (
    AsciiImage,
    AsciiColors,
    ImageExtension,
    FrameData,
    Frames,
    MediaFile,
    VideoFile,
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")

ASCII_ART_BUCKET = os.environ["ASCII_ART_BUCKET"]


def process_image(image: Image.Image) -> tuple[AsciiImage, AsciiColors]:
    pix = image.load()

    gray_image: Image.Image = image.convert("LA")
    width, height = gray_image.size

    ascii_dict = (
        AsciiDict.HighAsciiDict
        if width * height >= 180 * 180
        else AsciiDict.LowAsciiDict
    )

    grid: AsciiImage = [["X"] * width for _ in range(height)]
    image_colors: AsciiColors = [[(255, 255, 255)] * width for _ in range(height)]

    gray_pixels = gray_image.load()
    for y in range(height):
        for x in range(width):
            current_char: str = map_to_char(gray_pixels[x, y][0], ascii_dict)
            grid[y][x] = current_char
            image_colors[y][x] = pix[x, y]

    return grid, image_colors


def ascii_convert(image: Image.Image) -> Image.Image:
    grid, image_colors = process_image(image=image)
    return create_ascii_image(grid, image_colors)


def extract_frames(video_capture: cv2.VideoCapture, video_file: VideoFile) -> Frames:
    frame_id: int = 1
    video_name: str = video_file.file_name
    frames: Frames = []

    while True:
        ret, frame = video_capture.read()
        if ret:
            frames.append(
                FrameData(frame=frame, frame_id=frame_id, video_name=video_name)
            )
            frame_id += 1
        else:
            break

    return frames


def lambda_handler(event, _) -> dict:
    logger.info(event)

    bucket_name: str = event["bucket_name"]
    file_path: str = event["processed_key"]
    is_video: bool = event["is_video"]

    media_file: MediaFile = find_media_type(file_path)
    local_file: str = download_from_s3(s3_client, bucket_name, file_path)

    if is_video:
        video_capture: cv2.VideoCapture = cv2.VideoCapture(local_file)
        frames: Frames = extract_frames(video_capture, cast(VideoFile, media_file))
        video_capture.release()
        ascii_frames: list[Image.Image] = []
        logger.info("Finish extract frames")
        for frame in frames:
            ascii_image = ascii_convert(
                Image.fromarray(
                    cv2.cvtColor(cast(MatLike, frame.frame), cv2.COLOR_BGR2RGB)
                )
            )
            ascii_frames.append(ascii_image)
        logger.info("Finish ascii-ed frames")
        video = ImageSequenceClip([np.array(frame) for frame in ascii_frames], fps=24)
        video.write_videofile(
            "/tmp/temp-video.mp4",
            temp_audiofile="/tmp/null-audio.mp3",
            codec="libx264",
            bitrate="8000K",
            ffmpeg_params=["-g", "128", "-crf", "23", "-preset", "slower"],
        )
        logger.info("Finish save local video")
        key = save_video(s3_client, ASCII_ART_BUCKET, "/tmp/temp-video.mp4", file_path)
    else:
        image: Image.Image = Image.open(local_file).convert("RGB")
        ascii_image = ascii_convert(image)
        key = save_image(
            s3_client,
            ASCII_ART_BUCKET,
            ascii_image,
            ImageExtension(media_file.extension),
            file_path,
        )
    return {"ascii_art_key": key}
