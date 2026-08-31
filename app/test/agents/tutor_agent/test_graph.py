from app.agents.tutor_graph import tutor


SESSION_ID = "test-session-1"
PROBLEM_ID = "url-shortener"


# ===============================
# START INTERVIEW
# ===============================

tutor.start_session(
    session_id=SESSION_ID,
    problem_id=PROBLEM_ID,
)


# ===============================
# TURN 1
# ===============================

result = tutor.invoke(
    session_id=SESSION_ID,
    user_message="""
    I am designing a URL shortening service.

    I will use API Gateway, Lambda and DynamoDB.
    DynamoDB will store the mapping between the
    short URL and the original URL.
    """,
)

print("\n========== TURN 1 ==========")
print(result)


# ===============================
# TURN 2
# ===============================

result = tutor.invoke(
    session_id=SESSION_ID,
    user_message="""
    The system will have around 100 million redirects
    per day. Since reads are much higher than writes,
    I am thinking about adding Redis in front of DynamoDB.
    """,
)

print("\n========== TURN 2 ==========")
print(result)


# ===============================
# TURN 3
# ===============================

result = tutor.invoke(
    session_id=SESSION_ID,
    user_message="""
    For cache misses I will read from DynamoDB and then
    populate Redis. I think this should reduce the
    database load significantly.
    """,
)

print("\n========== TURN 3 ==========")
print(result)


# ===============================
# CHECKPOINT
# ===============================

checkpoint = tutor.get_state(
    SESSION_ID
)

print("\n========== CHECKPOINT ==========")

print("\nVALUES:")
print(checkpoint.values)

print("\nCONFIG:")
print(checkpoint.config)

print("\nNEXT:")
print(checkpoint.next)