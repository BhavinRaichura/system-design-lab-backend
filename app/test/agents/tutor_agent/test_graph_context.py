from app.agents.tutor_graph import tutor


result = tutor.invoke(
    session_id="test-session-1",
    user_message="""
    I think Redis should sit in front of DynamoDB
    because redirects are read-heavy.
    """,
)

print("result: ", result)