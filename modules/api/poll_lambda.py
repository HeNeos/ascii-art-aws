import os
import json
import boto3

from typing import TypedDict, Any
from enum import Enum

dynamo_client = boto3.client("dynamodb")
STATUS_TABLE = os.environ["STATUS_TABLE_NAME"]


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
    body: dict[str, str] = json.loads(event.get("body", "{}"))
    # TODO: file name and content type are not used
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

    response = dynamo_client.get_item(
        TableName=STATUS_TABLE,
        Key={
            "status": {"S": "FINISHED"},
            "id": {"S": token},
        },
    )

    if response.get("Item") is None:
        return {
            "statusCode": StatusCode.BAD_REQUEST.value,
            "body": "Invalid uploadToken",
            "headers": {"Content-Type": "application/json"},
        }

    return {
        "statusCode": StatusCode.OK.value,
        "body": json.dumps(
            {
                "url": response["Item"]["url"]["S"],
                "fileName": file_name,
                "contentType": content_type,
            }
        ),
        "headers": {"Content-Type": "application/json"},
    }
