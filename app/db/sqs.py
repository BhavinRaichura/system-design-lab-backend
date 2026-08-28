import boto3

from app.config.settings import settings

sqs_client = boto3.client(
    "sqs",
    endpoint_url=settings.aws_endpoint_url,
    region_name=settings.aws_region,
)