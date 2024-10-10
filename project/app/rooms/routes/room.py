from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, status, HTTPException, Request, UploadFile, File, Form

from app.core import get_db, settings_env
from app.responses import RoomResponse
from app.rooms.services import create_room_model,view_room_model
from app.schemas import RoomCreateRequest
from app.auth.services import get_current_user


settings = settings_env

room_router = APIRouter(
    prefix="/rooms",
    tags=["Rooms"]
)

@room_router.post("/create_room", status_code=status.HTTP_201_CREATED, response_model = RoomResponse)
async def create_room(
    width: float = Form(...),
    height: float = Form(...),
    length: float = Form(...),
    ImageFile: UploadFile = File(...),
    session: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        room_data = RoomCreateRequest(width=width, height=height, length=length)
        return await create_room_model(image_data=ImageFile, room=room_data, session=session, user=current_user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating user account: {e}")


@room_router.get("/view_room/", response_model = RoomResponse)
async def room_view(request: Request,session: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return await view_room_model(request, session, current_user)










