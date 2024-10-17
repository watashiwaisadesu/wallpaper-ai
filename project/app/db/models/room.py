from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, DateTime, ForeignKey, Float, func, Integer
from sqlalchemy.orm import mapped_column, relationship
import uuid

from app.core import Base


class Room(Base):
    __tablename__ = "rooms"

    uid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    id = Column(Integer)
    owner_id = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False)  # Cascade delete on user deletion
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    length = Column(Float, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship("User", back_populates="rooms")
    images = relationship("RoomImage", back_populates="room", cascade="all, delete-orphan")  # Cascade delete on room deletion
