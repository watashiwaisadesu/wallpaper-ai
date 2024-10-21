from sqlalchemy import Column, Integer, String, Float
from app.core import Base

class LeroyMerlin(Base):
    __tablename__ = "leroymerlin_items"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True)
    image_url = Column(String)
    name = Column(String)
    price = Column(String)
    item_name = Column(String)
    page_number = Column(Integer)
