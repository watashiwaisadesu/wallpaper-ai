from fastapi import FastAPI, HTTPException
import asyncio
from sqlalchemy import delete
import logging

from app.utils.parsing_leroymerlin import run_parse
from app.db.logging import setup_logging
from app.db.models import LeroyMerlin
from app.core import get_async_db

app = FastAPI()
logger = logging.getLogger(__name__)

@app.post("/scrape/{item}")
async def scrape_item(item: str):
    try:
        # Create tasks
        setup_logging()
        tasks = []

        # Schedule tasks for each item type
        for item_type in ["tiles", "wallpapers"]:
            async for session in get_async_db():
                await session.execute(
                    delete(LeroyMerlin).filter(LeroyMerlin.product_type == item_type)
                )
                logger.info(f"Deleted all products with product_type: {item_type} from the database.")
                await session.commit()

            async def task(item_type=item_type):  # Use default argument to capture the current item_type
                await run_parse(item_type)  # No need to pass the session here

            tasks.append(task())

        # Run all tasks concurrently
        await asyncio.gather(*tasks)
        return {"message": f"Started scraping for {item}."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

