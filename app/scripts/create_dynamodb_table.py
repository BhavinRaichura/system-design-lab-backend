import boto3

from app.config.settings import settings


dynamodb = boto3.client(
    "dynamodb",
    region_name=settings.aws_region,
    endpoint_url=settings.dynamodb_endpoint_url,
)


def create_table():
    dynamodb.create_table(
        TableName=settings.dynamodb_table_name,
        AttributeDefinitions=[
            {
                "AttributeName": "session_key",
                "AttributeType": "S",
            },
            {
                "AttributeName": "item_type",
                "AttributeType": "S",
            },
            {
                "AttributeName": "user_key",
                "AttributeType": "S",
            },
            {
                "AttributeName": "session_created_at",
                "AttributeType": "S",
            },
        ],
        KeySchema=[
            {
                "AttributeName": "session_key",
                "KeyType": "HASH",
            },
            {
                "AttributeName": "item_type",
                "KeyType": "RANGE",
            },
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "user_sessions_index",
                "KeySchema": [
                    {
                        "AttributeName": "user_key",
                        "KeyType": "HASH",
                    },
                    {
                        "AttributeName": "session_created_at",
                        "KeyType": "RANGE",
                    },
                ],
                "Projection": {
                    "ProjectionType": "ALL",
                },
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )

    print(
        f"Created table: "
        f"{settings.dynamodb_table_name}"
    )


if __name__ == "__main__":
    create_table()