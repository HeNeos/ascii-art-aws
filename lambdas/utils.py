import io
import os
import tarfile

from PIL import Image

from lambdas.custom_types import ImageExtension


def calculate_scale(image_height: int) -> int:
    max_height = 75
    new_scale: int = (image_height + max_height - 1) // max_height
    return new_scale


def split_file_name(file_path: str) -> tuple[str, str]:
    base_name: str = os.path.basename(file_path)
    file_name, file_extension = os.path.splitext(base_name)
    return file_name, file_extension.lstrip(".").lower()


def list_folder(s3_client, bucket_name: str, path: str) -> list[str]:
    paginator = s3_client.get_paginator("list_objects_v2")

    return [
        obj["Key"]
        for page in paginator.paginate(Bucket=bucket_name, Prefix=path)
        if "Contents" in page
        for obj in page["Contents"]
    ]


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
    s3_client, bucket_name: str, frames: list[tuple[Image.Image, str]], key: str
):
    with io.BytesIO() as buffer:
        with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
            for frame_data in frames:
                frame_image, frame_name = frame_data
                frame_buffer = io.BytesIO()
                frame_image.save(frame_buffer, format="PNG")
                frame_buffer.seek(0)

                tarinfo = tarfile.TarInfo(name=f"{frame_name}.png")
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


def save_video(s3_client, bucket_name: str, local_video_path: str, key: str) -> str:
    with open(local_video_path, "rb") as f:
        s3_client.upload_fileobj(f, bucket_name, key)
        return key


def unzip_file(gzip_path: str) -> list[str]:
    with tarfile.open(gzip_path, "r:gz") as tar:
        tar.extractall(path=os.path.dirname(gzip_path))
        image_paths = [
            os.path.join(os.path.dirname(gzip_path), member.name)
            for member in tar.getmembers()
            if member.isfile()
        ]
        return image_paths
