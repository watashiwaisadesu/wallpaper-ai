from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, status, HTTPException, UploadFile, File, Form
from typing import List

from app.core import get_db, settings_env
from app.responses import RoomResponse
from app.rooms.services import create_room_model, view_room_model
from app.schemas import RoomCreateRequest
from app.auth.services import get_current_user
import logging

settings = settings_env
logger = logging.getLogger(__name__)

room_router = APIRouter(
    prefix="/rooms",
    tags=["Rooms"]
)

@room_router.post("/create_room", status_code=status.HTTP_201_CREATED, response_model=RoomResponse)
async def create_room(
    width: float = Form(...),
    height: float = Form(...),
    length: float = Form(...),
    image_files: List[UploadFile] = File(...),
    session: AsyncSession = Depends(get_db),  # Change to AsyncSession
    current_user=Depends(get_current_user)
):
    try:
        room_data = RoomCreateRequest(width=width, height=height, length=length)
        room = await create_room_model(image_data=image_files, room=room_data, session=session, user=current_user)

        logger.info(f"Room created successfully. Room ID: {room.id}, Owner: {current_user.id}")
        return room
    except Exception as e:
        logger.error(f"Error creating room for user ID: {current_user.id}. Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating room: {e}")

@room_router.get("/view_room/", response_model=RoomResponse)
async def room_view_newest(session: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        room = await view_room_model(id=0, session=session, user=current_user)
        logger.info(f"Viewed newest room for user ID: {current_user.id}. Room ID: {room.id}")
        return room
    except Exception as e:
        logger.error(f"Error viewing newest room for user ID: {current_user.id}. Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error viewing room: {e}")

@room_router.get("/view_room/{id}", response_model=RoomResponse)
async def room_view(id: int, session: AsyncSession = Depends(get_db), current_user=Depends(get_current_user)):
    try:
        room = await view_room_model(id=id, session=session, user=current_user)
        logger.info(f"Viewed room ID: {id} for user ID: {current_user.id}.")
        return room
    except Exception as e:
        logger.error(f"Error viewing room ID: {id} for user ID: {current_user.id}. Error: {e}")
        raise HTTPException(status_code=500, detail=f"Error viewing room: {e}")
