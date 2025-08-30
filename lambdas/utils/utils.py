import json
import os
from typing import no_type_check

import boto3
from mypy_boto3_s3.client import S3Client

from lambdas.utils.custom_types import (
    ImageExtension,
    ImageFile,
    MediaFile,
    R2Credentials,
    VideoExtension,
    VideoFile,
)


def split_file_name(file_path: str) -> tuple[str, str, str]:
    base_name: str = os.path.basename(file_path)
    file_name, file_extension = os.path.splitext(base_name)
    random_id: str = file_path.split("/")[1]
    return file_name, file_extension.lstrip(".").lower(), random_id


def find_media_type(file_path: str) -> MediaFile:
    file_name, file_extension, random_id = split_file_name(file_path)
    if file_extension in ImageExtension._value2member_map_:
        if ImageExtension(file_extension) is ImageExtension.JPG:
            return ImageFile(file_name, ImageExtension.JPEG, random_id)
        return ImageFile(file_name, ImageExtension(file_extension), random_id)
    if file_extension in VideoExtension._value2member_map_:
        return VideoFile(file_name, VideoExtension(file_extension), random_id)

    raise ValueError(f"Unsupported file extension: {file_extension}")


def download_from_s3(s3_client: S3Client, bucket_name: str, s3_key: str) -> str:
    local_path = os.path.join("/tmp", os.path.basename(s3_key))
    s3_client.download_file(bucket_name, s3_key, local_path)

    return local_path


def get_r2_credentials(s3_client: S3Client, bucket_name: str) -> R2Credentials:
    response = s3_client.get_object(Bucket=bucket_name, Key="r2_secrets.json")
    json_content = response["Body"].read().decode("utf-8")
    json_object = json.loads(json_content)

    return R2Credentials(
        cloudflare_account_id=json_object["cloudflare_account_id"],
        r2_access_key_id=json_object["r2_access_key_id"],
        r2_secret_access_key=json_object["r2_secret_access_key"],
        ascii_art_bucket_name=f"ascii-art-storage-{json_object['cloudflare_account_id']}",
    )


@no_type_check
def get_r2_client(credentials: R2Credentials, r2_client: S3Client | None) -> S3Client:
    if r2_client is None:
        r2_client = boto3.client(
            "s3",
            endpoint_url=f"https://{credentials.cloudflare_account_id}.r2.cloudflarestorage.com",
            aws_access_key_id=credentials.r2_access_key_id,
            aws_secret_access_key=credentials.r2_secret_access_key,
            region_name="auto",
        )
    return r2_client
