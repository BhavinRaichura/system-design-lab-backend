import boto3

from app.config.settings import settings

dynamodb = boto3.resource(
    "dynamodb",
    region_name=settings.aws_region,
    endpoint_url=settings.dynamodb_endpoint_url,
)