from time import time

from mypy_boto3_dynamodb import DynamoDBClient

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
        response = self.dynamo_db_client.get_item(
            TableName=self.table_name,
            Key={"id": {"S": unique_id}, "status": {"S": status.value}},
        )

        item: AsciiArtTableItemResponse | None = response.get("Item")

        if item is None:
            return None

        return AsciiArtTableItem(
            id=item["id"]["S"],
            status=AsciiArtTableStatus(item["status"]["S"]),
            dithering=item["dithering"]["S"],
            edge_detection=item["edge_detection"]["BOOL"],
            resolution=item["resolution"]["S"],
            output=item["output"]["S"],
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
