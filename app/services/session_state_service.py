from app.repositories.session_state_repository import (
    SessionStateRepository,
)

from app.schemas.websocket import WebSocketEvent

import json

from app.db.sqs import sqs_client
from app.config.settings import settings

class SessionStateService:

    def __init__(self):
        self.repository = SessionStateRepository()

    def apply_event(
        self,
        session_id: str,
        event: WebSocketEvent
    ) -> dict:

        state = self.repository.get(
            session_id=session_id
        )

        if state is None:
            state = {
                "version": 0,
                "nodes": [],
                "edges": [],
            }

        if event.version <= state["version"]:
            return state

        state["version"] = event.version

        self._apply_event(
            state,
            event,
        )

        self.repository.save(
            session_id=session_id,
            state=state,
        )

        should_persist = (
            self.repository.should_persist(
                session_id=session_id
            )
        )

        if should_persist:
            sqs_client.send_message(
                QueueUrl=settings.sqs_queue_url,
                MessageBody=json.dumps({
                    "session_id": session_id,
                    "version": state["version"],
                }),
            )

        return state

    @staticmethod
    def _apply_event(
        state: dict,
        event: WebSocketEvent
    ) -> None:

        if event.event == "NODE_MOVED":

            node_id = event.payload["node_id"]
            position = event.payload["position"]

            for node in state["nodes"]:
                if node["id"] == node_id:
                    node["position"] = position
                    break

