import os
import json
import boto3

from typing import TypedDict, Any
from enum import Enum

sqs = boto3.client("sqs")
QUEUE_URL = os.environ["QUEUE_URL"]


class StatusCode(Enum):
    OK = 200
    BAD_REQUEST = 400
    INTERNAL_SERVER_ERROR = 500


class Response(TypedDict):
    statusCode: int


class S3Detail(TypedDict):
    bucket: dict[str, str]
    object: dict[str, str]


class S3Record(TypedDict):
    detail: S3Detail


class S3Event(TypedDict):
    Records: list[S3Record]


def lambda_handler(event: S3Event, _: Any) -> Response:
    for record in event.get("Records", []):
        s3_detail: S3Detail = record["detail"]
        key = s3_detail["object"]["key"]

        if not key.startswith("raw/"):
            continue

        # TODO: Fix the job id logic
        job_id = key.split("/")[-1].replace(".png", "")

        message = {"jobId": job_id, "s3Key": key, "bucket": s3_detail["bucket"]["name"]}

        sqs.send_message(QueueUrl=QUEUE_URL, MessageBody=json.dumps(message))

    return {"statusCode": 200}
