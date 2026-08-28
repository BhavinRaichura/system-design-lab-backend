from boto3.dynamodb.conditions import Key
from decimal import Decimal

from app.config.settings import settings
from app.db.dynamodb import dynamodb
from app.schemas.session import SessionResponse, SessionListResponse

class SessionRepository:

    def __init__(self):
        self.table = dynamodb.Table(
            settings.dynamodb_table_name
        )

    def _convert_floats(self, value):

        if isinstance(value, float):
            return Decimal(str(value))

        if isinstance(value, list):
            return [
                self._convert_floats(item)
                for item in value
            ]

        if isinstance(value, dict):
            return {
                key: self._convert_floats(item)
                for key, item in value.items()
            }

        return value

    def create(
        self,
        session: SessionResponse,
    )->None:

        item = {
            "session_key": f"SESSION#{session.session_id}",
            "item_type": "METADATA",

            "session_id": session.session_id,
            "user_id": session.user_id,
            "problem_id": session.problem_id,
            "status": session.status,
            "created_at": session.created_at.isoformat(),

            "user_key": f"USER#{session.user_id}",
            "session_created_at": (
                f"{session.created_at.isoformat()}"
                f"#{session.session_id}"
            ),
        }

        self.table.put_item(Item=item)

    def get(
        self,
        session_id: str,
    ) -> dict | None:

        response = self.table.get_item(
            Key={
                "session_key": f"SESSION#{session_id}",
                "item_type": "METADATA",
            }
        )

        return response.get("Item")

    def get_user_sessions(
        self,
        user_id: str
    ) -> list[dict]:
        
        response = self.table.query(
            IndexName="user_sessions_index",
            KeyConditionExpression=Key("user_key").eq(
                f"USER#{user_id}"
            ),
        )

        return response.get("Items", [])

    def save_architecture(
        self,
        session_id: str,
        architecture: dict,
    ) -> None:

        item = {
            "session_key": f"SESSION#{session_id}",
            "item_type": "ARCHITECTURE",
            **architecture,
        }

        item = self._convert_floats(item)

        self.table.put_item(
            Item=item
        )

    def get_architecture(
        self,
        session_id: str,
    ) -> dict | None:

        response = self.table.get_item(
            Key={
                "session_key": f"SESSION#{session_id}",
                "item_type": "ARCHITECTURE",
            }
        )

        return response.get("Item")
        