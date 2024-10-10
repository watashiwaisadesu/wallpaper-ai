from sqlalchemy import Column, String, DateTime, Boolean, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from app.core import Base


class User(Base):
    __tablename__ = "users"
    
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String(150))
    email = Column(String(255),unique=True, nullable=False, index=True)
    password = Column(String(100))
    is_active = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True,default=None)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    rooms = relationship("Room", back_populates="user")
    tokens = relationship("UserToken", back_populates="user")
    
    def get_context_string(self, context: str):
        return f"{context}{self.password[-6:]}{self.created_at.strftime('%m%d%Y%H%M%S')}".strip()
    

    
    
    