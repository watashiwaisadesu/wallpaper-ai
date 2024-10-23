from pydantic import BaseModel
from fastapi import UploadFile, File

class RoomCreateRequest(BaseModel):
    width: float
    height: float
    length: float
