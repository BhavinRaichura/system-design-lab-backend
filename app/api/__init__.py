from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.sessions import router as session_router
from app.api.websocket import router as websocket_router
from app.api.session_websocket import router as session_websocket_router
from app.api.tutor_websocket import router as tutor_websocket_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(session_router)
api_router.include_router(websocket_router)
api_router.include_router(session_websocket_router)
api_router.include_router(tutor_websocket_router)