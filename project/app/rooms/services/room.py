from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates
from base64 import b64encode

from app.schemas import RoomCreateRequest
from app.db.models import Room
from app.db.repositories import save


templates = Jinja2Templates(directory="app/templates")

async def create_room_model(room: RoomCreateRequest,image_data, session, user):
    image_bytes = await image_data.read()
    image_type = image_data.content_type
    user_id = user.id
    db_room = Room(
        width=room.width,
        height=room.height,
        length=room.length,
    )
    db_room.image_type = image_type
    db_room.owner_id = user_id
    db_room.image = image_bytes
    save(db_room, session)
    return db_room

async def view_room_model(request: Request, session, user):
    user_id = user.id
    results = session.query(Room).filter(Room.owner_id == user_id).first()

    if results:
        # Encode binary image data to Base64
        image_type = results.image_type
        encoded_image = b64encode(results.image).decode("utf-8")

        # Send the image data and type to the template for rendering
        return templates.TemplateResponse("deviceModelView.html", {
            "request": request,
            "image_type": image_type,
            "image_data": encoded_image,  # Base64 encoded image data
        })
    else:
        raise HTTPException(status_code=404, detail="Model not found")