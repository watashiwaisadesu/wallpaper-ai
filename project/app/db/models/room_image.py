from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime, ForeignKey, LargeBinary, func
from sqlalchemy.orm import mapped_column, relationship
import uuid

from app.core import Base

class RoomImage(Base):
    __tablename__ = "room_images"


    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    room_id = mapped_column(ForeignKey('rooms.uid', ondelete='CASCADE'), nullable=False)
    image_type = Column(String(50), nullable=False)
    image_data = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    room = relationship("Room", back_populates="images")

