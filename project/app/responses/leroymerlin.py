from pydantic import BaseModel

class LeroyMerlinResponse(BaseModel):
    url: str
    image_url: str
    name: str
    price: str

    class Config:
        orm_mode = True
