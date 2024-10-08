import io
import os
import tarfile

from PIL import Image, ImageDraw, ImageFont

from lambdas.font import Font
from lambdas.custom_types import AsciiColors, AsciiImage, ImageExtension, ImageFile


def calculate_scale(image_height: int) -> int:
    max_height = 150
    new_scale: int = (image_height + max_height - 1) // max_height
    return new_scale


def split_file_name(file_path: str) -> tuple[str, str]:
    base_name: str = os.path.basename(file_path)
    file_name, file_extension = os.path.splitext(base_name)
    return file_name, file_extension.lstrip(".").lower()


def download_from_s3(s3_client, bucket_name: str, s3_key: str) -> str:
    """
    Downloads a file from S3 to the local /tmp directory in Lambda.

    :param bucket_name: The name of the S3 bucket
    :param s3_key: The key of the file in the S3 bucket (i.e., file path)
    :return local_path: Full local file path
    """
    local_path = os.path.join("/tmp", os.path.basename(s3_key))
    s3_client.download_file(bucket_name, s3_key, local_path)

    return local_path


def compress_and_save(
    s3_client, frames: list[tuple[Image.Image, int]], bucket_name: str, key: str
):
    with io.BytesIO() as buffer:
        with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
            for frame_data in frames:
                frame_image, frame_id = frame_data
                frame_buffer = io.BytesIO()
                frame_image.save(frame_buffer, format="PNG")
                frame_buffer.seek(0)

                tarinfo = tarfile.TarInfo(name=f"{frame_id:06d}.png")
                tarinfo.size = len(frame_buffer.getvalue())

                tar.addfile(tarinfo, fileobj=frame_buffer)
        buffer.seek(0)
        s3_client.upload_fileobj(buffer, bucket_name, key)


def save_image(
    s3_client,
    bucket_name: str,
    image: Image.Image,
    image_format: ImageExtension,
    key: str,
) -> str:
    with io.BytesIO() as buffer:
        image.save(buffer, format=image_format.value)
        buffer.seek(0)
        s3_client.put_object(
            Body=buffer.getvalue(),
            Bucket=bucket_name,
            ContentType=f"image/{image_format.value}",
            Key=key,
        )
    return key


def save_ascii_image(
    s3_client,
    bucket_name: str,
    ascii_art: AsciiImage,
    image_file: ImageFile,
    image_colors: AsciiColors,
) -> str:
    image: Image.Image = Image.new(
        "RGBA",
        (Font.Width.value * len(ascii_art[0]), Font.Height.value * len(ascii_art)),
        "black",
    )
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("consolas.ttf", 14)
    x, y = 0, 0
    for row in range(len(ascii_art)):
        for column in range(len(ascii_art[row])):
            color = image_colors[row][column]
            draw.text((x, y), ascii_art[row][column], font=font, fill=color)
            x += Font.Width.value
        x = 0
        y += Font.Height.value

    image_name: str = image_file.file_name
    image_extension: ImageExtension = image_file.extension

    key = f"{image_name}_ascii.{image_extension.value}"
    save_image(s3_client, bucket_name, image, image_extension, key)
    return key
