"""Bootstrap script to create required DynamoDB tables for Meme Museum.
Run locally with AWS credentials or on an EC2 instance with proper IAM role.
"""
import boto3
import botocore

AWS_REGION = "us-east-1"

dynamodb = boto3.client("dynamodb", region_name=AWS_REGION)

TABLES = [
    {
        "TableName": "MemeUsers",
        "KeySchema": [{"AttributeName": "email", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "email", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "MemeItems",
        "KeySchema": [{"AttributeName": "meme_id", "KeyType": "HASH"}],
        "AttributeDefinitions": [
            {"AttributeName": "meme_id", "AttributeType": "S"},
            {"AttributeName": "user", "AttributeType": "S"},
            {"AttributeName": "created_at", "AttributeType": "S"},
        ],
        "BillingMode": "PAY_PER_REQUEST",
        "GlobalSecondaryIndexes": [
            {
                "IndexName": "by_user",
                "KeySchema": [{"AttributeName": "user", "KeyType": "HASH"}, {"AttributeName": "created_at", "KeyType": "RANGE"}],
                "Projection": {"ProjectionType": "ALL"}
            }
        ]
    },
    {
        "TableName": "MemeLikes",
        "KeySchema": [{"AttributeName": "meme_id", "KeyType": "HASH"}, {"AttributeName": "user", "KeyType": "RANGE"}],
        "AttributeDefinitions": [
            {"AttributeName": "meme_id", "AttributeType": "S"},
            {"AttributeName": "user", "AttributeType": "S"}
        ],
        "BillingMode": "PAY_PER_REQUEST",
    },
    {
        "TableName": "MemeLogs",
        "KeySchema": [{"AttributeName": "id", "KeyType": "HASH"}],
        "AttributeDefinitions": [{"AttributeName": "id", "AttributeType": "S"}],
        "BillingMode": "PAY_PER_REQUEST",
    }
]


def table_exists(name):
    try:
        dynamodb.describe_table(TableName=name)
        return True
    except botocore.exceptions.ClientError as e:
        return False


def create_table(defn):
    name = defn["TableName"]
    if table_exists(name):
        print(f"Table {name} already exists. Skipping.")
        return
    print(f"Creating table {name} ...")
    dynamodb.create_table(**defn)
    waiter = boto3.client("dynamodb", region_name=AWS_REGION).get_waiter('table_exists')
    waiter.wait(TableName=name)
    print(f"Table {name} created.")


if __name__ == "__main__":
    for t in TABLES:
        create_table(t)
    print("All tables created or verified.")
