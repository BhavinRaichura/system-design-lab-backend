import json

from app.db.redis import redis_client

class SessionStateRepository:

    @staticmethod
    def _key(session_id: str) -> str:
        return f"session:{session_id}:state"

    def save(
        self,
        session_id: str,
        state: dict,
    ) -> None:

        redis_client.set(
            self._key(session_id),
            json.dumps(state)
        )

    def get(
        self,
        session_id: str
    ) -> dict | None:

        value = redis_client.get(
            self._key(session_id=session_id)
        )

        if value is None:
            return None

        return json.loads(value)

    def delete(
        self,
        session_id: str,
    ) -> None:

        redis_client.delete(
            self._key(session_id=session_id)
        )