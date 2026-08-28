from app.config.settings import settings
from app.db.sqs import sqs_client


response = sqs_client.send_message(
    QueueUrl=settings.sqs_queue_url,
    MessageBody="hello from system design tutor",
)

print(response["MessageId"])