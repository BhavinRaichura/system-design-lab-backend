from datetime import datetime
from typing import Literal

from pydantic import BaseModel

SessionStatus = Literal[
    "active",
    "completed"
]

# pyload send by frontend
class CreateSessionRequest(BaseModel):
    problem_id: str

# backend returns
class SessionResponse(BaseModel):
    session_id: str
    user_id: str
    problem_id: str
    status: SessionStatus
    created_at: datetime

class SessionListResponse(BaseModel):
    sessions: list[SessionResponse]