from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

@router.websocket("/ws/test")
async def websocket_test(websocket: WebSocket):

    await websocket.accept()

    try:
        while True:
            message = await websocket.receive_text()

            await websocket.send_text(
                f"Server Received: {message}"
            )
            
    except WebSocketDisconnect:
        print("disconnected")