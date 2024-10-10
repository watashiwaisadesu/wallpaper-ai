from pydantic import BaseModel
from uuid import UUID

class RoomResponse(BaseModel):
    id: UUID
    width: float
    height: float
    length: float
    owner_id: UUID