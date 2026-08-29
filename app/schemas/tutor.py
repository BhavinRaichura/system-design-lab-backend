from pydantic import BaseModel
from typing import Literal

class TutorResponseSchema(BaseModel):
    response: str
    action: Literal["FOLLOW_UP", "HINT", "CHALLANGE", "EVALUATE"]
    topic: str