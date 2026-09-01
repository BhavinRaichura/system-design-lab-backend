import uuid
from app.agents.tutor_graph import tutor


def print_state(state, turn):
    print("\n" + "=" * 70)
    print(f"TURN {turn}")
    print("=" * 70)

    print(f"Phase        : {state.get('interview_phase')}")
    print(f"Status       : {state.get('interview_status')}")
    print(f"Decision     : {state.get('next_decision')}")
    print(f"Action       : {state.get('current_action')}")
    print(f"Topic        : {state.get('current_topic')}")
    print(f"Difficulty   : {state.get('current_difficulty')}")

    print("\nTutor:")
    print(state.get("tutor_response"))

    print("\nCandidate weaknesses:")
    for item in state.get("candidate_weaknesses", []):
        print(f"  - {item}")

    print("\nCandidate decisions:")
    for item in state.get("candidate_decisions", []):
        print(f"  - {item}")

    print("\nQuestions asked:")
    for q in state.get("questions_asked", []):
        print(f"  - {q}")

    print("\nEvidence count:", len(state.get("evidence", [])))


def main():
    session_id = str(uuid.uuid4())

    print("Starting HLD Interview")
    print("Session:", session_id)

    # --------------------------------------------------
    # TURN 1
    # --------------------------------------------------

    message = """
    I would first clarify the requirements.
    We need to support millions of users and the system should
    generate short URLs and redirect users from the short URL
    to the original URL.
    """

    state = tutor.invoke(
        session_id=session_id,
        user_message=message,
        problem_id="url-shortener",
    )

    print_state(state, 1)

    # --------------------------------------------------
    # TURN 2
    # --------------------------------------------------

    message = """
    For storage, I think DynamoDB would be a good choice because
    we mainly need key-value access. The short URL can be the
    partition key and the original URL can be stored as the value.
    """

    state = tutor.invoke(
        session_id=session_id,
        user_message=message,
    )

    print_state(state, 2)

    # --------------------------------------------------
    # TURN 3
    # --------------------------------------------------

    message = """
    For redirects, I would put API Gateway in front of Lambda.
    Lambda will look up the short URL in DynamoDB and return
    the original URL.
    """

    state = tutor.invoke(
        session_id=session_id,
        user_message=message,
    )

    print_state(state, 3)

    # --------------------------------------------------
    # TURN 4
    # --------------------------------------------------

    message = """
    Since the system can receive a very large number of reads,
    I would add Redis caching in front of DynamoDB.
    Frequently accessed short URLs can be cached.
    """

    state = tutor.invoke(
        session_id=session_id,
        user_message=message,
    )

    print_state(state, 4)

    # --------------------------------------------------
    # FINAL STATE
    # --------------------------------------------------

    print("\n" + "#" * 70)
    print("FINAL INTERVIEW STATE")
    print("#" * 70)

    final_state = tutor.get_state(session_id)

    print(final_state.values)


if __name__ == "__main__":
    main()