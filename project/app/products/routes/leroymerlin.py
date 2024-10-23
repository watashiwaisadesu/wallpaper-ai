from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.auth.services import get_current_user
from app.products.services import fetch_wallpapers,fetch_tiles
from app.core import get_async_db
from app.products.responses import LeroyMerlinResponse


product_router = APIRouter(
    prefix="/products/leroymerlin",
    tags=["Products"]
)

@product_router.get("/wallpapers/", response_model=List[LeroyMerlinResponse])
async def get_wallpapers(page: int = 1, db: AsyncSession = Depends(get_async_db), user = Depends(get_current_user)):
    return await fetch_wallpapers(page, db)


@product_router.get("/tiles/", response_model=List[LeroyMerlinResponse])
async def get_tiles(page: int = 1, db: AsyncSession = Depends(get_async_db), user = Depends(get_current_user)):
    return await fetch_tiles(page, db)