from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.db.repositories.product_repository import get_products_by_type


async def fetch_wallpapers(page: int, db: AsyncSession):
    page_size = 10
    wallpapers = await get_products_by_type("wallpapers", page, page_size, db)

    if not wallpapers:
        raise HTTPException(status_code=404, detail="No wallpapers found.")

    return wallpapers


async def fetch_tiles(page: int, db: AsyncSession):
    page_size = 10
    tiles = await get_products_by_type("tiles", page, page_size, db)

    if not tiles:
        raise HTTPException(status_code=404, detail="No tiles found.")

    return tiles
