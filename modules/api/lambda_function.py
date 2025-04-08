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


# 128 bytes to 16MB
conditions = [
    ["content-length-range", 1 << 7, 1 << 24],
    ["starts-with", "$Content-Type", "image/"],
    ["starts-with", "$Content-Type", "video/"],
]


def lambda_handler(event: Event, _: Any) -> Response:
    token = event.get("queryStringParameters", {}).get("uploadToken")
    if not token:
        return {
            "statusCode": StatusCode.BAD_REQUEST.value,
            "body": "Missing uploadToken",
            "headers": {"Content-Type": "application/json"},
        }

    key_prefix: str = f"raw/{token}/"
    fields = {"key": key_prefix}

    presigned_post_data = s3.generate_presigned_post(
        Bucket=BUCKET,
        Key=key_prefix,
        Fields=fields,
        Conditions=conditions + [["starts-with", "$key", key_prefix]],
        ExpiresIn=300,
    )

    return {
        "statusCode": StatusCode.OK.value,
        "body": json.dumps(
            {
                "uploadUrl": presigned_post_data["url"],
                "jobId": token,
                "fields": presigned_post_data["fields"],
            },
        ),
        "headers": {"Content-Type": "application/json"},
    }
