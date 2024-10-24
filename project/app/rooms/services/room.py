from fastapi import HTTPException, UploadFile
from fastapi.responses import JSONResponse
from typing import List
import logging

from app.rooms.schemas import RoomCreateRequest
from app.db.models import Room, RoomImage
from app.db.repositories import save, get_room_images, get_newest_room, get_room_by_id, count_user_rooms

logger = logging.getLogger(__name__)


async def create_room_model(room: RoomCreateRequest, image_data: List[UploadFile], session, user):
    try:
        room_count = await count_user_rooms(session, user.id)  # Ensure this function is async
        logger.info(f"User ID: {user.id} is creating a room. Current room count: {room_count}")

        db_room = Room(
            width=room.width,
            height=room.height,
            length=room.length,
            owner_id=user.id,
            id=room_count + 1
        )
        await save(db_room, session)  # Await the save operation
        logger.info(f"Room created successfully. Room ID: {db_room.uid}, Owner ID: {user.id}")

        for image in image_data:
            image_bytes = await image.read()
            image_type = image.content_type

            room_image = RoomImage(
                room_id=db_room.uid,
                image_type=image_type,
                image_data=image_bytes
            )
            await save(room_image, session)  # Await the save operation
            logger.info(f"Image saved for Room ID: {db_room.uid}. Image Type: {image_type}")

        return db_room
    except Exception as e:
        logger.error(f"Error creating room for user ID: {user.id}. Error: {e}")
        raise HTTPException(status_code=500, detail="Error creating room.")

async def view_room_model(user, session, id: int = None):
    user_id = user.id
    try:
        if id == 0:
            logger.info(f"User ID: {user_id} is viewing the newest room.")
            room = await get_newest_room(session, user_id)
        else:
            logger.info(f"User ID: {user_id} is viewing room ID: {id}.")
            room = await get_room_by_id(session, user_id, id)

        if room is None:
            logger.warning(f"Room not found for User ID: {user_id}, Room ID: {id}")
            raise HTTPException(status_code=404, detail="Room not found")

        images_data = await get_room_images(session, room.uid)  # Ensure this function is async
        room_parameters = {
            "id": room.id,
            "width": room.width,
            "height": room.height,
            "length": room.length,
        }

        logger.info(f"Room viewed successfully. Room ID: {room.uid}, Owner ID: {user_id}")
        return JSONResponse(content={
            "room_parameters": room_parameters,
            "images": images_data
        })
    except Exception as e:
        logger.error(f"Error viewing room for User ID: {user_id}. Error: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving room.")