from mypy_boto3_s3.client import S3Client


def save_video(
    s3_client: S3Client,
    bucket_name: str,
    local_video_path: str,
    key: str,
) -> str:
    with open(local_video_path, "rb") as f:
        s3_client.upload_fileobj(f, bucket_name, key)
        return key
