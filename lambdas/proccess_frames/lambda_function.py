import logging
import os

import boto3

from PIL import Image
from lambdas.proccess_frames.modules.ascii_dict import AsciiDict
from lambdas.proccess_frames.modules.utils import map_to_char
from lambdas.utils import (
    download_from_s3,
    save_ascii_image,
    split_file_name,
    list_folder,
    unzip_file,
)
from lambdas.custom_types import AsciiImage, AsciiColors, ImageExtension, ImageFile

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


def ascii_convert(image_path: str, image_file: ImageFile) -> str:
    image_name = image_file.file_name
    image_extension = image_file.extension
    image: Image.Image = Image.open(image_path).convert("RGB")
    grid, image_colors = process_image(image=image)
    image_file = ImageFile(image_name, ImageExtension(image_extension))

    return save_ascii_image(
        s3_client=s3_client,
        bucket_name=ASCII_ART_BUCKET,
        ascii_art=grid,
        image_file=image_file,
        image_colors=image_colors,
    )


def lambda_handler(event, _) -> dict:
    logger.info(event)

    bucket_name: str = event["bucket_name"]
    file_path: str = event["file_path"]
    is_video: bool = event["is_video"] == "true"

    frames: list[tuple[str, ImageFile]] = []
    if is_video:
        gzip_files: list[str] = list_folder(s3_client, bucket_name, file_path)
        for gzip_file in gzip_files:
            local_gzip_file: str = download_from_s3(s3_client, bucket_name, gzip_file)
            frames_path: list[str] = unzip_file(local_gzip_file)
            for frame_path in frames_path:
                frame_name, frame_extension = split_file_name(frame_path)
                image_file: ImageFile = ImageFile(
                    frame_name, ImageExtension(frame_extension)
                )
                frames.append((frame_path, image_file))
    else:
        local_file: str = download_from_s3(s3_client, bucket_name, file_path)
        file_name, file_extension = split_file_name(file_path)
        image_file = ImageFile(file_name, ImageExtension(file_extension))
        frames = [(local_file, image_file)]

    output_keys: list[str] = [ascii_convert(frame[0], frame[1]) for frame in frames]

    return {"ascii_art_key": output_keys}
