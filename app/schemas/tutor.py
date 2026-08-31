from pydantic import BaseModel
from typing import Literal

class TutorResponseSchema(BaseModel):

    response: str

    action: Literal[
        "FOLLOW_UP",
        "HINT",
        "CHALLENGE",
        "EVALUATE",
        "CLARIFICATION",
        "REQUIREMENT_GATHERING",
    ]

    topic: str

    requirements_covered: list[str]

    candidate_decisions: list[str]

    candidate_weaknesses: list[str]

    conversation_summary: str

from pydantic import BaseModel
from typing import Literal


class TutorAnalysisSchema(BaseModel):

    action: Literal[
        "FOLLOW_UP",
        "HINT",
        "CHALLENGE",
        "EVALUATE",
        "CLARIFICATION",
        "REQUIREMENT_GATHERING",
    ]

    last_action: Literal[
        "FOLLOW_UP",
        "HINT",
        "CHALLENGE",
        "EVALUATE",
        "CLARIFICATION",
        "REQUIREMENT_GATHERING",
    ]

    topic: str

    requirements_covered: list[str]

    candidate_decisions: list[str]

    candidate_weaknesses: list[str]

    conversation_summary: str


class TutorMessage(BaseModel):
    message: str
    problem_id: str | None = None


class TutorResponse(BaseModel):
    response: str
    action: str
    topic: str