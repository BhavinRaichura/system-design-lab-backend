import json

from app.repositories.session_state_repository import (
    SessionStateRepository,
)

repo = SessionStateRepository()

repo.save(
    session_id="test-session",
    state={
        "version": 5,
        "nodes": [
            {
                "id": "node-1",
                "type": "lambda",
                "position": {
                    "x": 100,
                    "y": 200,
                },
            }
        ],
        "edges": [],
    },
)

print(repo.get("test-session"))