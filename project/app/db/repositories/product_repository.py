from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.products.responses import LeroyMerlinResponse
from app.db.models import LeroyMerlin


async def get_products_by_type(product_type: str, page: int, page_size: int, db: AsyncSession):
    skip = (page - 1) * page_size

    result = await db.execute(
        select(LeroyMerlin).filter(LeroyMerlin.product_type == product_type).offset(skip).limit(page_size)
    )
    products = result.scalars().all()

    if not products:
        raise HTTPException(status_code=404, detail="Products not found")

    # Return list of Pydantic models
    return [LeroyMerlinResponse.from_orm(product) for product in products]