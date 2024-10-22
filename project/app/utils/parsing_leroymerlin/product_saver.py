import logging
from sqlalchemy.future import select
from app.db.repositories import save
from app.db.models import LeroyMerlin

logger = logging.getLogger(__name__)

class ProductSaver:
    @staticmethod
    async def save_products(products, session):
        for product in products:
            existing_product = await session.execute(
                select(LeroyMerlin).filter(
                    LeroyMerlin.product_type == product['product_type'],
                    LeroyMerlin.name == product['name']
                )
            )
            existing_product = existing_product.scalars().first()

            if existing_product:
                logger.info(f"Product already exists: {product['product_type']}. Skipping save.")
                continue

            new_product = LeroyMerlin(**product)
            await save(new_product, session)

        logger.info(f"Saved {len(products)} new products to the database.")
