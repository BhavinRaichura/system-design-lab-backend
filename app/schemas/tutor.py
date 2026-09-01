# app/schemas/tutor.py

from typing import Any, Literal, TypedDict
from pydantic import BaseModel, Field


class TutorAnalysisSchema(BaseModel):
    intent: str
    topic: str

    answer_quality: Literal[
        "STRONG",
        "GOOD",
        "WEAK",
        "VERY_WEAK",
        "NOT_APPLICABLE",
    ]

    reasoning_quality: Literal[
        "STRONG",
        "GOOD",
        "WEAK",
        "NONE",
    ]

    candidate_decisions: list[str] = []
    candidate_assumptions: list[str] = []

    candidate_strengths: list[str] = []
    candidate_weaknesses: list[str] = []

    missing_concepts: list[str] = []
    strong_concepts: list[str] = []

    requirements_covered: list[str] = []

    # 1-5 assessment of this specific response
    reasoning_score: int = Field(
        ge=1,
        le=5,
    )

    technical_score: int = Field(
        ge=1,
        le=5,
    )

    confidence: float = Field(
        ge=0,
        le=1,
    )

    # topic -> assessment
    skill_assessment: dict[str, Any] = {}

    conversation_summary: str


class InterviewDecisionSchema(BaseModel):
    decision: Literal[
        "ASK_QUESTION",
        "CLARIFICATION",
        "REQUIREMENT_GATHERING",
        "MOVE_PHASE",
        "END_INTERVIEW",
    ]

    action: Literal[
        "FOLLOW_UP",
        "CHALLENGE",
        "HINT",
        "DEEP_DIVE",
        "EVALUATE",
    ]

    topic: str

    objective: str

    next_phase: str | None = None

    reason: str


class QuestionPlanSchema(BaseModel):
    question_type: Literal[
        "FOLLOW_UP",
        "CHALLENGE",
        "TRADEOFF",
        "PROBE",
        "EDGE_CASE",
        "FAILURE_SCENARIO",
        "ESTIMATION",
        "DEEP_DIVE",
        "VALIDATION",
    ]

    topic: str
    concept: str
    objective: str

    difficulty: int = Field(
        ge=1,
        le=5,
    )

    question: str
    reason: str


class QuestionReviewSchema(BaseModel):
    relevant: bool
    tests_target_concept: bool
    appropriate_difficulty: bool
    not_duplicate: bool
    does_not_reveal_solution: bool
    single_question: bool

    score: float = Field(
        ge=0,
        le=1,
    )

    feedback: str


class TutorResponseSchema(BaseModel):
    response: str
    topic: str
    action: str
    conversation_summary: str


# app/agents/tutor_graph.py
class TutorState(TypedDict):

    problem_id: str

    interview_phase: str
    interview_status: str

    next_decision: str

    current_action: str
    current_topic: str
    current_objective: str

    current_question_type: str
    current_difficulty: int

    selected_question: str

    question_retry_count: int

    question_candidates: list[dict[str, Any]]

    question_review_feedback: str

    # NEW
    latest_analysis: dict[str, Any]

    candidate_summary: str

    candidate_decisions: list[str]
    candidate_assumptions: list[str]

    candidate_strengths: list[str]
    candidate_weaknesses: list[str]

    requirements_covered: list[str]
    requirements_remaining: list[str]

    skill_profile: dict[str, dict[str, Any]]

    questions_asked: list[dict[str, Any]]

    evidence: list[dict[str, Any]]

    hints_used: int
    questions_asked_count: int

    conversation_summary: str

    tutor_response: str

    evaluation: dict[str, Any] | None