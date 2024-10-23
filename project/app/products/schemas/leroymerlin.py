from pydantic import BaseModel

class ProductRequestSchema(BaseModel):
    page: int = 1