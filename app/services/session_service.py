from datetime import datetime, timezone
from uuid import uuid4

from app.repositories.session_repository import (
    SessionRepository,
)

from app.schemas.session import SessionResponse
from app.schemas.architecture import (
    ArchitectureRequest,
    ArchitectureResponse,
)



class SessionService:

    def __init__(self):
        self.repository = SessionRepository()

    def create_session(
        self,
        user_id: str,
        problem_id: str,
    ) -> SessionResponse:

        session = SessionResponse(
            session_id=str(uuid4()),
            user_id=user_id,
            problem_id=problem_id,
            status="active",
            created_at=datetime.now(timezone.utc),
        )

        self.repository.create(session=session)

        return session

    def get_session(
        self,
        session_id: str
    ) -> SessionResponse:

        item = self.repository.get(session_id=session_id)

        if item is None:
            return None
        
        return SessionResponse(
            session_id=item["session_id"],
            user_id=item["user_id"],
            problem_id=item["problem_id"],
            status=item["status"],
            created_at=datetime.fromisoformat(
                item["created_at"]
            ),
        )

    def get_user_sessions(
        self,
        user_id: str,
    ):

        items = self.repository.get_user_sessions(user_id=user_id)

        return [
            SessionResponse(
                session_id=item["session_id"],
                user_id=item["user_id"],
                problem_id=item["problem_id"],
                status=item["status"],
                created_at=datetime.fromisoformat(
                    item["created_at"]
                ),
            ) 
            for item in items
        ]

    def save_architecture(
        self,
        session_id: str,
        architecture: ArchitectureRequest,
    ) -> ArchitectureResponse:

        self.repository.save_architecture(
            session_id,
            architecture.model_dump(),
        )

        return ArchitectureResponse(
            session_id=session_id,
            nodes=architecture.nodes,
            edges=architecture.edges,
        )

    def get_architecture(
        self,
        session_id: str,
    ) -> ArchitectureResponse | None:

        item = self.repository.get_architecture(
            session_id
        )

        if item is None:
            return None

        return ArchitectureResponse(
            session_id=session_id,
            nodes=item["nodes"],
            edges=item["edges"],
        )