from fastapi import WebSocket, APIRouter, WebSocketDisconnect

from app.services.session_state_service import (
    SessionStateService,
)
from app.schemas.websocket import WebSocketEvent



router = APIRouter()

session_state_service = SessionStateService()

@router.websocket("/ws/sessions/{session_id}")
async def session_websocket(
    websocket: WebSocket,
    session_id: str,
):
    await websocket.accept()

    print(
        f"WebSocket connected: session={session_id}"
    )

    try:

        while True:

            data = await websocket.receive_json()

            print(data)

            event = WebSocketEvent.model_validate(
                data
            )

            state = session_state_service.apply_event(
                session_id=session_id,
                event=event,
            )

            await websocket.send_json(
                {
                    "event": "ACK",
                    "version": state["version"]
                }
            )

    except WebSocketDisconnect:
        print(
            f"WebSocket disconnected: "
            f"session={session_id}"
        )
