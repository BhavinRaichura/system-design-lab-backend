from app.agents.context_builder import (
    TutorContextBuilder
)

builder  = TutorContextBuilder()


# with problem available

# context = builder.build(
#     session_id="test-session-1",
#     state={
#         "problem_id": "url-shortener",
#         "current_topic": "DATABASE",
#         "interview_phase": "ARCHITECTURE",
#         "conversation_summary": "",
#         "requirements_covered": [],
#         "candidate_decisions": [],
#         "candidate_weaknesses": [],
#         "hints_used": 0,
#     },
#     user_message="I want to add Redis.",
# )
context = builder.build(
    session_id="test-session-1",
    state={
        "problem_id": "ccar-parking-system",
        "current_topic": "DATABASE",
        "interview_phase": "ARCHITECTURE",
        "conversation_summary": "",
        "requirements_covered": [],
        "candidate_decisions": [],
        "candidate_weaknesses": [],
        "hints_used": 0,
    },
    user_message="I want to add Redis.",
)

print(context)