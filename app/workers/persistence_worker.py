import json

from app.config.settings import settings
from app.db.sqs import sqs_client
from app.repositories.session_state_repository import (
    SessionStateRepository,
)
from app.repositories.session_repository import (
    SessionRepository
)
from app.schemas.persistence import PersistenceMessage

class PersistenceWorker:

    def __init__(self):
        self.state_repository = SessionStateRepository()
        self.session_repository = SessionRepository()

    def run(self):

        while True:

            response = sqs_client.receive_message(
                QueueUrl=settings.sqs_queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10,
            )

            messages = response.get(
                "Messages",
                [],
            )

            for message in messages:

                self.process_message(
                    message
                )

    def process_message(
        self,
        message: dict,
    ):

        body = json.loads(
            message["Body"]
        )

        persistence_message = (
            PersistenceMessage.model_validate(
                body
            )
        )

        session_id = (
            persistence_message.session_id
        )

        state = self.state_repository.get(
            session_id
        )

        print("start")

        if state is None:

            print(
                f"Session state not found: "
                f"{session_id}"
            )

            return

        updated = self.session_repository.save_architecture(
            session_id=session_id,
            architecture={
                "nodes": state.get("nodes", []),
                "edges": state.get("edges", []),
            },
            version=state["version"],
        )

        if updated:

            print(
                f"Persisted session={session_id} "
                f"version={state['version']}"
            )

        else:

            print(
                f"Skipped stale/duplicate message: "
                f"session={session_id} "
                f"version={state['version']}"
            )

        sqs_client.delete_message(
            QueueUrl=settings.sqs_queue_url,
            ReceiptHandle=message["ReceiptHandle"],
        )