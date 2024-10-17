from sqlalchemy import Column, Integer, String, Text, TIMESTAMP
from datetime import datetime

from app.core import Base
class LogEntry(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(TIMESTAMP, default=datetime.utcnow)
    log_level = Column(String(10))
    message = Column(Text)
    source = Column(String(255))