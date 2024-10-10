import logging
import os

import boto3

from PIL import Image
from lambdas.process_frames.modules.ascii_dict import AsciiDict
from lambdas.process_frames.modules.utils import create_ascii_image, map_to_char
from lambdas.utils import (
    compress_and_save,
    download_from_s3,
    save_image,
    split_file_name,
    unzip_file,
)
from lambdas.custom_types import AsciiImage, AsciiColors, ImageExtension

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
        if width * height >= 150 * 150
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


def ascii_convert(image_path: str) -> Image.Image:
    image: Image.Image = Image.open(image_path).convert("RGB")
    grid, image_colors = process_image(image=image)

    return create_ascii_image(grid, image_colors)


def lambda_handler(event, _) -> dict:
    logger.info(event)

    bucket_name: str = event["bucket_name"]
    file_path: str = event["processed_key"]
    is_video: bool = event["is_video"]

    local_file: str = download_from_s3(s3_client, bucket_name, file_path)
    frames_path: list[str] = [local_file]

    if is_video:
        frames_path = unzip_file(local_file)

    ascii_frames: list[tuple[Image.Image, str]] = []
    for frame_path in frames_path:
        frame_name, _ = split_file_name(frame_path)
        ascii_frames.append((ascii_convert(frame_path), frame_name))

    if is_video:
        key = compress_and_save(s3_client, ASCII_ART_BUCKET, ascii_frames, file_path)
    else:
        ascii_image = ascii_frames[0][0]
        _, image_extension = split_file_name(local_file)
        key = save_image(
            s3_client,
            ASCII_ART_BUCKET,
            ascii_image,
            ImageExtension(image_extension),
            file_path,
        )

    return {"ascii_art_key": key}
