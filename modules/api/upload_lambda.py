import os
import json
import boto3

from typing import TypedDict, Any
from enum import Enum
from time import time

s3 = boto3.client("s3")
BUCKET = os.environ["UPLOAD_BUCKET"]
STATUS_TABLE = os.environ["STATUS_TABLE_NAME"]

dynamo_client = boto3.client("dynamodb")


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
]

valid_resolutions: list[str] = [
    "240",
    "480",
    "720",
    "1080",
    "1440",
    "2160",
    "2880",
]

valid_dithering: list[str] = [
    "atkinson",
    "riemersma",
    "riemersma_naive",
    "floyd_steinberg",
    "jarvis_judice_ninke",
]


def check_parameters(
    token: str | None,
    dithering: str | None,
    resolution: str | None,
) -> str | None:
    if not token:
        return "Missing uploadToken"
    if not dithering:
        return "Missing dithering"
    if not resolution:
        return "Missing resolution"
    if dithering not in valid_dithering:
        return "Invalid dithering value"
    if resolution not in valid_resolutions:
        return "Invalid resolution value"
    return None


def lambda_handler(event: Event, _: Any) -> Response:
    token: str | None = event.get("queryStringParameters", {}).get("uploadToken")
    dithering: str | None = event.get("queryStringParameters", {}).get("dithering")
    resolution: str | None = event.get("queryStringParameters", {}).get("resolution")
    output: str = event.get("queryStringParameters", {}).get("output", "color")

    error_message: str | None = check_parameters(token, dithering, resolution)

    if error_message:
        return {
            "statusCode": StatusCode.BAD_REQUEST.value,
            "body": error_message,
            "headers": {"Content-Type": "application/json"},
        }
    body: dict[str, str] = json.loads(event.get("body", "{}"))
    file_name: str = body.get("fileName", "")
    content_type: str = body.get("contentType", "")

    if not file_name or not content_type:
        return {
            "statusCode": StatusCode.BAD_REQUEST.value,
            "body": "Missing fileName or contentType",
            "headers": {"Content-Type": "application/json"},
        }
    if not content_type.startswith("image/") and not content_type.startswith("video/"):
        return {
            "statusCode": StatusCode.BAD_REQUEST.value,
            "body": "Invalid content type",
            "headers": {"Content-Type": "application/json"},
        }

    key: str = f"raw/{token}/{file_name}"
    fields = {"key": key}

    presigned_post_data = s3.generate_presigned_post(
        Bucket=BUCKET,
        Key=key,
        Fields=fields,
        Conditions=conditions
        + [
            ["starts-with", "$key", key],
            ["starts-with", "$Content-Type", content_type],
        ],
        ExpiresIn=300,
    )

    dynamo_client.put_item(
        TableName=STATUS_TABLE,
        Item={
            "status": {"S": "PENDING"},
            "id": {"S": token},
            "dithering": {"S": dithering},
            "resolution": {"S": resolution},
            "ttl": {"N": str(int(time() + 300))},
            "output": {"S": output},
        },
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
