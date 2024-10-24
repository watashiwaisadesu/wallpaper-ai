import logging
from app.db.repositories import save
from app.db.models import LeroyMerlin

logger = logging.getLogger(__name__)

class ProductSaver:
    @staticmethod
    async def save_products(products, session):
        for product in products:
            new_product = LeroyMerlin(**product)
            await save(new_product, session)
        logger.info(f"Saved {len(products)} new products to the database.")
