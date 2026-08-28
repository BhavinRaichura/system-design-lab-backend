import json

from app.repositories.session_state_repository import (
    SessionStateRepository,
)

repo = SessionStateRepository()

repo.get(
    session_id="test-session"
)



print(repo.get("test-session"))