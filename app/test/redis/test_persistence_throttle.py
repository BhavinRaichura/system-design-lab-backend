from app.repositories.session_state_repository import (
    SessionStateRepository,
)


repo = SessionStateRepository()

session_id = "test-throttle"

print(
    "1:",
    repo.should_persist(session_id)
)

print(
    "2:",
    repo.should_persist(session_id)
)