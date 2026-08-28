from fastapi import APIRouter, HTTPException

from app.schemas.session import (
    CreateSessionRequest,
    SessionResponse,
    SessionListResponse,
)

from app.schemas.architecture import (
    ArchitectureResponse,
    ArchitectureRequest,
)

from app.services.session_service import (
    SessionService
)


from app.config.settings import settings

router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"],
)

session_service = SessionService()

@router.post(
        "",
        response_model=SessionResponse,
)
def create_session(
    request: CreateSessionRequest
):
    print("hello")
    return session_service.create_session(
        user_id=settings.demo_user_id,
        problem_id=request.problem_id
    )

@router.get(
    "/{session_id}",
    response_model=SessionResponse
)
def get_session(session_id: str):

    session = session_service.get_session(
        session_id=session_id
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found",
        )

    return session


@router.get(
    "",
    response_model=SessionListResponse
)
def get_sessions():

    user_id = settings.demo_user_id

    sessions = session_service.get_user_sessions(user_id=user_id)

    return SessionListResponse(
        sessions=sessions
    )


@router.put(
    "/{session_id}/architecture",
    response_model=ArchitectureResponse
)
def save_architecture(
    session_id: str,
    request: ArchitectureRequest,
):
    return session_service.save_architecture(
        session_id=session_id,
        architecture=request,
    )


@router.get(
    "/{session_id}/architecture",
    response_model=ArchitectureResponse,
)
def get_architecture(
    session_id: str,
):

    architecture = (
        session_service.get_architecture(
            session_id
        )
    )

    if architecture is None:
        raise HTTPException(
            status_code=404,
            detail="Architecture not found",
        )

    return architecture