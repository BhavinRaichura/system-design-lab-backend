import os
from typing import Literal

from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)


Environment = Literal[
    "development",
    "qa",
]


environment = os.getenv(
    "ENVIRONMENT",
    "development",
)


class Settings(BaseSettings):
    app_name: str
    environment: Environment

    demo_user_id: str

    aws_region: str
    aws_endpoint_url: str
    
    dynamodb_table_name: str
    dynamodb_endpoint_url: str | None = None

    redis_url: str

    sqs_queue_url: str

    persistence_interval_seconds: int = 5
    session_state_ttl_seconds: int = 3600

    gemini_api_key: str
    gemini_model: str

    model_config = SettingsConfigDict(
        env_file=(
            f"app/config/environments/"
            f".env.{environment}"
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()