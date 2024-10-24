from sqlalchemy import Column, String, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from app.core import Base
import uuid


class LeroyMerlin(Base):
    __tablename__ = "leroymerlin_items"

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    url = Column(String, index=True)
    image_url = Column(String)
    name = Column(String)
    price = Column(Float)
    price_type = Column(String)
    product_type = Column(String)

