import io
import os

from PIL import Image


def calculate_scale(image_height: int) -> int:
    max_height = 200
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


def save_image(
    s3_client, image: Image.Image, image_format: str, bucket_name: str, key: str
) -> str:
    with io.BytesIO() as buffer:
        image.save(buffer, format=image_format)
        buffer.seek(0)
        s3_client.put_object(
            Body=buffer.getvalue(),
            Bucket=bucket_name,
            ContentType=f"image/{image_format}",
            Key=key,
        )
    return key
