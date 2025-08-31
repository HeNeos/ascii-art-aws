import os
from typing import Self

from mypy_boto3_s3.client import S3Client

from lambdas.models.r2 import R2Credentials

ascii_r2_client: S3Client | None = None
client_cache: dict[str, "AsciiArtS3Client"] = dict()


class AsciiArtS3Client:
    def __new__(cls, s3_client: S3Client, bucket_name: str) -> "AsciiArtS3Client":
        if bucket_name in client_cache:
            return client_cache[bucket_name]

        instance = super().__new__(cls)
        client_cache[bucket_name] = instance
        return instance

    def __init__(self, s3_client: S3Client, bucket_name: str) -> None:
        self.s3_client: S3Client = s3_client
        self.bucket_name: str = bucket_name

    def download_to_local(self, s3_key: str) -> str:
        local_path: str = os.path.join("/tmp", os.path.basename(s3_key))
        self.s3_client.download_file(self.bucket_name, s3_key, local_path)
        return local_path

    def save_from_local(self, local_path: str, key: str) -> str:
        with open(local_path, "rb") as f:
            self.s3_client.upload_fileobj(f, self.bucket_name, key)
            return key

    @classmethod
    def get_r2_client(cls, credentials: R2Credentials) -> Self:
        global ascii_r2_client

        if ascii_r2_client is None:
            import boto3

            ascii_r2_client = boto3.client(
                "s3",
                endpoint_url=f"https://{credentials.cloudflare_account_id}.r2.cloudflarestorage.com",
                aws_access_key_id=credentials.r2_access_key_id,
                aws_secret_access_key=credentials.r2_secret_access_key,
                region_name="auto",
            )
            if ascii_r2_client is None:
                raise RuntimeError("Failed to create r2 client")

        return cls(
            s3_client=ascii_r2_client,
            bucket_name=credentials.ascii_art_bucket_name,
        )
