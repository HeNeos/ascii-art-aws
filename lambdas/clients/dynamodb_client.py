from time import time
from typing import cast

from mypy_boto3_dynamodb import DynamoDBClient
from mypy_boto3_dynamodb.type_defs import GetItemOutputTypeDef

from lambdas.models.state_table import (
    AsciiArtTableItem,
    AsciiArtTableItemResponse,
    AsciiArtTableStatus,
)


class AsciiArtDynamoDbClient:
    def __init__(self, dynamo_db_client: DynamoDBClient, table_name: str) -> None:
        self.dynamo_db_client: DynamoDBClient = dynamo_db_client
        self.table_name: str = table_name

    def get_item(
        self,
        unique_id: str,
        status: AsciiArtTableStatus,
    ) -> AsciiArtTableItem | None:
        response: GetItemOutputTypeDef = self.dynamo_db_client.get_item(
            TableName=self.table_name,
            Key={"id": {"S": unique_id}, "status": {"S": status.value}},
        )

        item = response.get("Item")
        if item is None:
            return None

        ascii_art_item: AsciiArtTableItemResponse = cast(
            "AsciiArtTableItemResponse",
            item,
        )

        return AsciiArtTableItem(
            id=ascii_art_item["id"]["S"],
            status=AsciiArtTableStatus(ascii_art_item["status"]["S"]),
            dithering=ascii_art_item["dithering"]["S"],
            edge_detection=ascii_art_item["edge_detection"]["BOOL"],
            resolution=ascii_art_item["resolution"]["S"],
            output=ascii_art_item["output"]["S"],
        )

    def put_item(self, unique_id: str, status: AsciiArtTableStatus, url: str) -> None:
        self.dynamo_db_client.put_item(
            TableName=self.table_name,
            Item={
                "id": {"S": unique_id},
                "status": {"S": status.value},
                "url": {"S": url},
                "ttl": {"N": str(int(time() + 300))},
            },
        )
