import json
import logging
import os
from typing import TypedDict, cast

import boto3
import cv2
import numpy as np
import numpy.typing as npt
from cairo import ImageSurface
from cv2.typing import MatLike
from moviepy.editor import ImageSequenceClip
from PIL import Image

from lambdas.utils.custom_types import (
    AsciiColors,
    AsciiImage,
    ImageExtension,
    MediaFile,
    VideoFile,
)

from lambdas.utils.font import Font

from lambdas.process_frames.modules.frames import FrameData, Frames
from lambdas.process_frames.modules.ascii_dict import AsciiDict
from lambdas.process_frames.modules.utils import (
    create_ascii_image,
    create_char_array,
    map_to_char_vectorized,
)
from lambdas.process_frames.dithering import DitheringStrategy
from lambdas.process_frames.dithering.utils import get_dithering_strategy
from lambdas.utils.utils import (
    download_from_s3,
    find_media_type,
    split_file_name,
)

from lambdas.utils.save import ImageCairo, save_video

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")

ASCII_ART_BUCKET = os.environ["ASCII_ART_BUCKET"]
MEDIA_BUCKET = os.environ["MEDIA_BUCKET"]


class LambdaEvent(TypedDict):
    key: str
    processed_key: str
    is_video: bool
    random_id: str
    dithering: str


def process_image(
    image: Image.Image,
    char_array: npt.NDArray[np.str_],
    dithering_strategy: type[DitheringStrategy] | None = None,
) -> tuple[AsciiImage, AsciiColors]:
    img_array: npt.NDArray[np.uint8] = np.array(image, dtype=np.uint8)

    gray_array: npt.NDArray[np.float64] = np.clip(
        np.dot(img_array[..., :3], [0.3090, 0.5770, 0.1240]), 0.0, 255.0
    )

    if dithering_strategy is not None:
        gray_array = dithering_strategy.dithering(gray_array, len(char_array))

    ascii_chars: npt.NDArray[np.str_] = map_to_char_vectorized(gray_array, char_array)

    grid: AsciiImage = ascii_chars.tolist()
    image_colors: AsciiColors = [row.tolist() for row in img_array]

    return grid, image_colors


def ascii_convert(
    image: Image.Image,
    char_array: npt.NDArray[np.str_],
    dithering_strategy: type[DitheringStrategy] | None,
) -> ImageSurface:
    grid, image_colors = process_image(
        image=image, char_array=char_array, dithering_strategy=dithering_strategy
    )
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


def lambda_handler(event: LambdaEvent, _: str) -> dict[str, int | str]:
    logger.info(event)

    initial_key: str = event["key"]
    video_name, _ = split_file_name(initial_key)
    file_path: str = event["processed_key"]
    is_video: bool = event["is_video"]
    random_id: str = event["random_id"]
    dithering: str = event.get("dithering", "riemersma_naive")
    dithering_strategy: type[DitheringStrategy] = get_dithering_strategy(dithering)

    media_file: MediaFile = find_media_type(file_path)
    local_file: str = download_from_s3(s3_client, MEDIA_BUCKET, file_path)

    if is_video:
        video_capture: cv2.VideoCapture = cv2.VideoCapture(local_file)
        width, height = video_capture.get()  # TODO
        video_fps = video_capture.get(cv2.CAP_PROP_FPS)
        frames: Frames = extract_frames(video_capture, cast(VideoFile, media_file))
        video_capture.release()
        logger.info("Finish extract frames")
        ascii_dict = (
            AsciiDict.HighAsciiDict
            if width * height >= (1600 // Font.Width.value) * (900 // Font.Height.value)
            else AsciiDict.LowAsciiDict
        )
        char_array: npt.NDArray[np.str_] = create_char_array(ascii_dict)
        ascii_frames: list[ImageSurface] = [
            ascii_convert(
                Image.fromarray(
                    cv2.cvtColor(cast(MatLike, frame.frame), cv2.COLOR_BGR2RGB),
                ),
                char_array,
                dithering_strategy,
            )
            for frame in frames
        ]
        logger.info("Finish ascii-ed frames")
        video = ImageSequenceClip(
            [
                np.ndarray(
                    shape=(frame.get_height(), frame.get_width(), 4),
                    dtype=np.uint8,
                    buffer=frame.get_data(),
                )[..., :3][:, :, ::-1]
                for frame in ascii_frames
            ],
            fps=video_fps,
        )
        video.write_videofile(
            "/tmp/temp-video.mp4",
            temp_audiofile="/tmp/null-audio.mp3",
            codec="libx264",
            ffmpeg_params=["-g", "128", "-crf", "19", "-preset", "medium"],
        )
        logger.info("Finish save local video")
        key = save_video(
            s3_client,
            ASCII_ART_BUCKET,
            "/tmp/temp-video.mp4",
            f"{video_name}-{random_id}/{media_file.file_name}_ascii.{media_file.extension.value}",  # noqa: 501
        )
    else:
        image: Image.Image = Image.open(local_file).convert("RGB")
        width, height = image.size
        ascii_dict = (
            AsciiDict.HighAsciiDict
            if width * height >= (1600 // Font.Width.value) * (900 // Font.Height.value)
            else AsciiDict.LowAsciiDict
        )
        char_array = create_char_array(ascii_dict)
        ascii_image = ascii_convert(image, char_array, dithering_strategy)
        image_object: ImageCairo = ImageCairo(
            ascii_image, ImageExtension(media_file.extension)
        )
        image_object.write_to_buffer()
        key = image_object.save_image(
            s3_client,
            ASCII_ART_BUCKET,
            f"{media_file.file_name}_ascii.{media_file.extension.value}",
        )
        url: str = s3_client.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": ASCII_ART_BUCKET,
                "Key": key,
            },
            ExpiresIn=300,
        )
        return {
            "statusCode": 200,
            "ascii_art_key": key,
            "body": json.dumps(cast(dict[str, str], {"url": url})),
        }
    return {
        "statusCode": 200,
        "ascii_art_key": key,
    }
