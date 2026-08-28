from app.config.settings import settings
from app.db.sqs import sqs_client
from app.workers.persistence_worker import (
    PersistenceWorker,
)


worker = PersistenceWorker()

response = sqs_client.receive_message(
    QueueUrl=settings.sqs_queue_url,
    MaxNumberOfMessages=1,
    WaitTimeSeconds=1,
)

messages = response.get(
    "Messages",
    [],
)

for message in messages:
    worker.process_message(message)