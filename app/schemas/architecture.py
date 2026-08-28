from typing import Any

from pydantic import BaseModel


class ArchitectureNode(BaseModel):
    id: str
    type: str
    data: dict[str, Any] = {}
    position: dict[str, float] = {}


class ArchitectureEdge(BaseModel):
    id: str
    source: str
    target: str
    type: str | None = None


class ArchitectureRequest(BaseModel):
    nodes: list[ArchitectureNode]
    edges: list[ArchitectureEdge]


class ArchitectureResponse(BaseModel):
    session_id: str
    nodes: list[ArchitectureNode]
    edges: list[ArchitectureEdge]