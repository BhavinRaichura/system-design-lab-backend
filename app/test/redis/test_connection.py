import json

from app.repositories.session_state_repository import (
    SessionStateRepository,
)

repo = SessionStateRepository()

repo.save(
    session_id="test-session",
    state={
        "version": 1,
        "nodes": [],
        "edges": [],
    },
)

print(repo.get("test-session"))