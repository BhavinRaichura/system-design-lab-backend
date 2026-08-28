from pydantic import BaseModel

class PersistenceMessage(BaseModel):
    session_id: str
    version: int

