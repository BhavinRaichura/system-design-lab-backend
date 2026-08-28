from app.config.settings import settings
from app.db.sqs import sqs_client


response = sqs_client.receive_message(
    QueueUrl=settings.sqs_queue_url,
    MaxNumberOfMessages=1,
    WaitTimeSeconds=1,
)

print(response)