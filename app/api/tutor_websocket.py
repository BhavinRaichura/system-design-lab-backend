from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.tutor_graph import tutor
from app.schemas.tutor import TutorMessage

router = APIRouter()

@router.websocket("/ws/tutor/{session_id}")
async def tutor_websocket(
    websocket: WebSocket,
    session_id: str,
):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_json()

            message = TutorMessage.model_validate(data)

            result = tutor.invoke(
                session_id=session_id,
                problem_id=message.problem_id,
                user_message=message.message,
            )

            print("\n\n============= result===================\n",result)

            await websocket.send_json(
                {
                    "event": "TUTOR_RESPONSE",
                    "payload": {
                        # "response": result["response"],
                        # "action": result["action"],
                        # "topic": result["topic"],
                        "response": result
                    },
                }
            )
            
    except WebSocketDisconnect:
        print(
            f"Tutor WebSocket disconnected: "
            f"session={session_id}"
        )
