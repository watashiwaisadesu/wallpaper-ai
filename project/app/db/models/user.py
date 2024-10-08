from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    
    
    id = Column(Integer, primary_key=True, nullable=False)
    name = Column(String(150))
    email = Column(String(255),unique=True, nullable=False, index=True)
    password = Column(String(100))
    is_active = Column(Boolean, default=False)
    verified_at = Column(DateTime, nullable=True,default=None)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    
    tokens = relationship("UserToken", back_populates="user")
    
    def get_context_string(self, context: str):
        return f"{context}{self.password[-6:]}{self.created_at.strftime('%m%d%Y%H%M%S')}".strip()
    
    
class UserToken(Base):
    __tablename__ = "user_tokens"
    
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_id = mapped_column(ForeignKey('users.id'))
    access_key = Column(String(250), nullable=True, index=True, default=None)
    refresh_key = Column(String(250), nullable=True, index=True, default=None)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    
    user = relationship("User", back_populates="tokens")
    
    
    