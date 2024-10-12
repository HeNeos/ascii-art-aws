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
from lambdas.process_frames.modules.utils import create_ascii_image
from lambdas.utils import (
    download_from_s3,
    find_media_type,
    save_image,
    save_video,
    split_file_name,
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
MEDIA_BUCKET = os.environ["MEDIA_BUCKET"]


def create_char_array(ascii_dict: str) -> np.ndarray:
    return np.array(list(ascii_dict))


def map_to_char_vectorized(values: np.ndarray, char_array: np.ndarray) -> np.ndarray:
    return char_array[np.digitize(values, np.linspace(0, 256, len(char_array) + 1)) - 1]


def process_image(image: Image.Image) -> tuple[AsciiImage, AsciiColors]:
    img_array = np.array(image)
    height, width, _ = img_array.shape

    gray_array = np.dot(img_array[..., :3], [0.2989, 0.5870, 0.1140])

    ascii_dict = (
        AsciiDict.HighAsciiDict
        if width * height >= 180 * 180
        else AsciiDict.LowAsciiDict
    )
    char_array = create_char_array(ascii_dict.value)

    ascii_chars = map_to_char_vectorized(gray_array, char_array)

    grid: AsciiImage = ascii_chars.tolist()
    image_colors: AsciiColors = [row.tolist() for row in img_array]

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

    initial_key = event["key"]
    video_name, _ = split_file_name(initial_key)
    file_path: str = event["processed_key"]
    is_video: bool = event["is_video"]
    random_id: str = event["random_id"]

    media_file: MediaFile = find_media_type(file_path)
    local_file: str = download_from_s3(s3_client, MEDIA_BUCKET, file_path)

    if is_video:
        video_capture: cv2.VideoCapture = cv2.VideoCapture(local_file)
        video_fps = video_capture.get(cv2.CAP_PROP_FPS)
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
        video = ImageSequenceClip(
            [np.array(frame) for frame in ascii_frames], fps=video_fps
        )
        video.write_videofile(
            "/tmp/temp-video.mp4",
            temp_audiofile="/tmp/null-audio.mp3",
            codec="libx264",
            bitrate="8000K",
            ffmpeg_params=["-g", "128", "-crf", "23", "-preset", "medium"],
        )
        logger.info("Finish save local video")
        key = save_video(
            s3_client,
            ASCII_ART_BUCKET,
            "/tmp/temp-video.mp4",
            f"{video_name}-{random_id}/{media_file.file_name}_ascii.{media_file.extension.value}",
        )
    else:
        image: Image.Image = Image.open(local_file).convert("RGB")
        ascii_image = ascii_convert(image)
        key = save_image(
            s3_client,
            ASCII_ART_BUCKET,
            ascii_image,
            ImageExtension(media_file.extension),
            f"{media_file.file_name}_ascii.{media_file.extension.value}",
        )
    return {"ascii_art_key": key}
