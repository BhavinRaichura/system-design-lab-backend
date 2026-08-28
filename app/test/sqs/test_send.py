import json

from app.config.settings import settings
from app.db.sqs import sqs_client


sqs_client.send_message(
    QueueUrl=settings.sqs_queue_url,
    MessageBody=json.dumps({
        "session_id": "test-session",
        "version": 5
    }),
)