from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

class WebSocketEventType(StrEnum):
    NODE_ADDED = "NODE_ADDED"
    NODE_UPDATED = "NODE_UPDATED"
    NODE_MOVED = "NODE_MOVED"
    NODE_DELETED = "NODE_DELETED"

    EDGE_ADDED = "EDGE_ADDED"
    EDGE_DELETED = "EDGE_DELETED"

    ARCHITECTURE_UPDATED = "ARCHITECTURE_UPDATED"


class WebSocketEvent(BaseModel):
    event: WebSocketEventType
    version: int
    payload: dict[str, Any] = Field(default_factory=dict)


class WebSocketResponse(BaseModel):
    event: WebSocketEventType
    version: int
    payload: dict[str, Any] = Field(default_factory=dict)