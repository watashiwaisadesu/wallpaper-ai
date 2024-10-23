from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.auth.services import get_current_user
from app.products.services import fetch_wallpapers,fetch_tiles
from app.core import get_async_db
from app.products.responses import LeroyMerlinResponse
from app.products.schemas import ProductRequestSchema


product_router = APIRouter(
    prefix="/products/leroymerlin",
    tags=["Products"]
)

@product_router.post("/wallpapers/", response_model=List[LeroyMerlinResponse])
async def get_wallpapers(request: ProductRequestSchema, db: AsyncSession = Depends(get_async_db), user = Depends(get_current_user)):
    return await fetch_wallpapers(request.page, db)


@product_router.post("/tiles/", response_model=List[LeroyMerlinResponse])
async def get_tiles(request: ProductRequestSchema, db: AsyncSession = Depends(get_async_db), user = Depends(get_current_user)):
    return await fetch_tiles(request.page, db)