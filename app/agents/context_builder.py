from app.repositories.session_state_repository import (
    SessionStateRepository
)

from app.repositories.problem_repository import (
    ProblemRepository
)


class TutorContextBuilder:

    def __init__(self):
        self.session_repository = (
            SessionStateRepository()
        )
        self.problem_repository = (
            ProblemRepository()
        )

    def build(
        self,
        session_id: str,
        state: dict,
        user_message: str,
    ) -> dict:

        problem = self.problem_repository.get(
            state["problem_id"]
        )

        if problem is None:
            raise ValueError(
                f"Problem not found: {state['problem_id']}"
            )

        architecture = (
            self.session_repository.get(
                session_id=session_id
            )
        )


        return {
            "problem": problem,
            "problem_id": state["problem_id"],
            "architecture": architecture,

            "current_topic": state["current_topic"],
            "interview_phase": state["interview_phase"],

            "conversation_summary": (
                state["conversation_summary"]
            ),

            "requirements_covered": (
                state["requirements_covered"]
            ),

            "candidate_decisions": (
                state["candidate_decisions"]
            ),

            "candidate_weaknesses": (
                state["candidate_weaknesses"]
            ),

            "hints_used": state["hints_used"],

            "user_message": user_message,
        }
            