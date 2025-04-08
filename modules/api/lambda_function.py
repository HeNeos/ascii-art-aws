import os
import json
import boto3

from typing import TypedDict, Any
from enum import Enum

s3 = boto3.client("s3")
BUCKET = os.environ["UPLOAD_BUCKET"]


class StatusCode(Enum):
    OK = 200
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500


class Response(TypedDict):
    statusCode: int
    body: str
    headers: dict[str, str]


class Event(TypedDict):
    queryStringParameters: dict[str, str]
    pathParameters: dict[str, str]
    headers: dict[str, str]
    body: str
    isBase64Encoded: bool


def lambda_handler(event: Event, _: Any) -> Response:
    token = event.get("queryStringParameters", {}).get("uploadToken")
    if not token:
        return {
            "statusCode": StatusCode.BAD_REQUEST.value,
            "body": "Missing uploadToken",
            "headers": {"Content-Type": "application/json"},
        }

    # TODO: Fix to multiple file extensions and multiple names
    object_key = f"raw/{token}.png"

    presigned_url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": BUCKET, "Key": object_key, "ContentType": "image/png"},
        ExpiresIn=300,
    )

    return {
        "statusCode": StatusCode.OK.value,
        "body": json.dumps(
            {"uploadUrl": presigned_url, "s3Key": object_key, "jobId": token}
        ),
        "headers": {"Content-Type": "application/json"},
    }
