from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, LargeBinary, func
from sqlalchemy.orm import mapped_column, relationship
import uuid

from app.core import Base

class Room(Base):
    __tablename__ = "rooms"


    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    owner_id = mapped_column(ForeignKey('users.id'))
    image_type = Column(String(50), nullable=False)
    width = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    length = Column(Float, nullable=False)
    image = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    user = relationship("User", back_populates="rooms")

