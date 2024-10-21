from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core import get_db
from app.db.models import LeroyMerlin
from app.responses import LeroyMerlinResponse
from typing import List

parse_router = APIRouter(
    prefix="/leroymerlin",
    tags=["LeroyMerlin"]
)


@parse_router.get("/wallpapers/", response_model=List[LeroyMerlinResponse])
async def get_wallpapers(page: int = 1, db: AsyncSession = Depends(get_db)):
    page_size = 10
    skip = (page - 1) * page_size

    result = await db.execute(
        select(LeroyMerlin).filter(LeroyMerlin.item_name == 'wallpapers').offset(skip).limit(page_size)
    )
    wallpapers = result.scalars().all()

    if not wallpapers:
        raise HTTPException(status_code=404, detail="No wallpapers found.")

    return wallpapers

@parse_router.get("/tiles/", response_model=List[LeroyMerlinResponse])
async def get_tiles(page: int = 1, db: AsyncSession = Depends(get_db)):
    page_size = 10
    skip = (page - 1) * page_size

    result = await db.execute(
        select(LeroyMerlin).filter(LeroyMerlin.item_name == 'tiles').offset(skip).limit(page_size)
    )
    tiles = result.scalars().all()

    if not tiles:
        raise HTTPException(status_code=404, detail="No wallpapers found.")

    return tiles