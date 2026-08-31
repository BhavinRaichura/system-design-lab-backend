from app.agents.tutor_graph import tutor


result = tutor.invoke(
    session_id="test-session-1",
    problem_id="url-shortener",
    user_message="""
    I would use DynamoDB as the primary
    database because the access pattern is
    simple key-value lookup.
    """,
)

print(result)


result = tutor.invoke(
    session_id="test-session-1",
    user_message="""
    Since the system is read heavy, I would
    add Redis in front of DynamoDB.
    """,
)

# print(result)

checkpoint = tutor.get_state("test-session-1")

print("\n========== CHECKPOINT ==========")
print(checkpoint.values)