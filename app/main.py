from fastapi import FastAPI

from app.api import api_router
from app.config.settings import settings

app = FastAPI(
    title=settings.app_name
)

app.include_router(api_router)