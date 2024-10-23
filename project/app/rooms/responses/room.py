from pydantic import BaseModel
from uuid import UUID

class RoomResponse(BaseModel):
    uid: UUID
    id: int
    width: float
    height: float
    length: float
    owner_id: UUID