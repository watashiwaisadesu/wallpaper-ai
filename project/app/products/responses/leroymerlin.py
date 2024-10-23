from pydantic import BaseModel

class LeroyMerlinResponse(BaseModel):
    url: str
    image_url: str
    name: str
    price: float
    price_type: str

    class Config:
        orm_mode = True
        from_attributes = True