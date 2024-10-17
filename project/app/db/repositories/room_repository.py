from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc
from base64 import b64encode
import logging

from app.db.models import Room, RoomImage

logger = logging.getLogger(__name__)


async def get_newest_room(session: AsyncSession, user_id: str):
    try:
        result = await session.execute(
            select(Room).filter(Room.owner_id == user_id).order_by(desc(Room.created_at))
        )
        room = result.scalars().first()  # Get the first result

        if room is None:
            logger.warning(f"No rooms found for user ID: {user_id}.")
            raise HTTPException(status_code=404, detail="No rooms found for this user.")

        logger.info(f"Fetched the newest room for user ID: {user_id}. Room ID: {room.id}")
        return room
    except Exception as e:
        logger.error(f"Error fetching the newest room for user ID: {user_id}. Error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching the newest room.")


async def get_room_by_id(session: AsyncSession, user_id: str, id: str):
    try:
        result = await session.execute(
            select(Room).filter(Room.id == id, Room.owner_id == user_id)
        )
        room = result.scalars().first()  # Get the first result

        if room is None:
            logger.warning(f"Room ID: {id} not found for user ID: {user_id}.")
            raise HTTPException(status_code=404, detail="Room not found.")

        logger.info(f"Fetched room ID: {id} for user ID: {user_id}.")
        return room
    except Exception as e:
        logger.error(f"Error fetching the room by ID: {id} for user ID: {user_id}. Error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching the room by ID.")


async def count_user_rooms(session: AsyncSession, user_id: str):
    try:
        result = await session.execute(
            select(Room).filter(Room.owner_id == user_id)
        )
        rooms = result.scalars().all()  # Get all rooms

        room_count = len(rooms)
        logger.info(f"User ID: {user_id} has {room_count} rooms.")
        return room_count
    except Exception as e:
        logger.error(f"Error counting rooms for user ID: {user_id}. Error: {e}")
        raise HTTPException(status_code=500, detail="Error counting user rooms.")


async def get_room_images(session: AsyncSession, room_id: str):
    """Fetch images associated with a room."""
    try:
        result = await session.execute(
            select(RoomImage).filter(RoomImage.room_id == room_id)
        )
        room_images = result.scalars().all()  # Get all room images
        images_data = []

        for image in room_images:
            encoded_image = b64encode(image.image_data).decode("utf-8")
            images_data.append({
                "image_type": image.image_type,
                "image_data": encoded_image,
            })

        logger.info(f"Fetched {len(images_data)} images for room ID: {room_id}.")
        return images_data
    except Exception as e:
        logger.error(f"Error fetching images for room ID: {room_id}. Error: {e}")
        raise HTTPException(status_code=500, detail="Error fetching room images.")