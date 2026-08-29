from app.agents.tutor_graph import tutor


state = {

    "problem_id": "url-shortener",

    "problem": """
    Design a URL shortening service like Bitly.

    Requirements:
    - Users can create short URLs.
    - Users can redirect using the short URL.
    - The system should support around 100 million
      redirects per day.
    - Redirect latency should be low.
    """,

    "architecture": {
        "version": 1,
        "nodes": [
            {
                "id": "api-gateway",
                "type": "API Gateway",
            },
            {
                "id": "lambda",
                "type": "Lambda",
            },
            {
                "id": "dynamodb",
                "type": "DynamoDB",
            },
        ],
        "edges": [
            {
                "source": "api-gateway",
                "target": "lambda",
            },
            {
                "source": "lambda",
                "target": "dynamodb",
            },
        ],
    },

    "current_topic": "DATABASE",

    "interview_phase": "ARCHITECTURE",

    "conversation_summary": "",

    "requirements_covered": [],

    "candidate_decisions": [],

    "candidate_weaknesses": [],

    "hints_used": 0,

    "user_message": "",
}


# ===============================
# TURN 1
# ===============================

state["user_message"] = """
I am designing a URL shortening service.

I will use API Gateway, Lambda and DynamoDB.
DynamoDB will store the mapping between the
short URL and the original URL.
"""

result = tutor.invoke(session_id="test-session-1",state=state)

print("\n========== TURN 1 ==========")
print(result)


# ===============================
# TURN 2
# ===============================

state["user_message"] = """
The system will have around 100 million redirects
per day. Since reads are much higher than writes,
I am thinking about adding Redis in front of DynamoDB.
"""

result = tutor.invoke(session_id="test-session-1",state=state)

print("\n========== TURN 2 ==========")
print(result)


# ===============================
# TURN 3
# ===============================

# state["user_message"] = """
# For cache misses I will read from DynamoDB and then
# populate Redis. I think this should reduce the
# database load significantly.
# """

# result = tutor.invoke(state)

# print("\n========== TURN 3 ==========")
# print(result)

tutor.debug_checkpointer()

checkpoint = tutor.get_state(
    "test-session-1"
)

print("\n========== CHECKPOINT ==========")
print(checkpoint)

print("\n========== CHECKPOINT ==========")
print("VALUES:")
print(checkpoint.values)

print("\nCONFIG:")
print(checkpoint.config)

print("\nNEXT:")
print(checkpoint.next)