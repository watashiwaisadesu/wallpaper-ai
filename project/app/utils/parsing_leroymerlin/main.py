from fastapi import FastAPI, HTTPException
import asyncio
from app.utils.parsing_leroymerlin import run_parse

app = FastAPI()


@app.post("/scrape/{item}")
async def scrape_item(item: str):
    try:
        # Create tasks
        tasks = []

        # Schedule tasks for each item type
        for item_type in ["tiles", "wallpapers"]:
            # Define an asynchronous task to run the parsing for each item type
            async def task(item_type):
                await run_parse(item_type)  # No need to pass the session here

            tasks.append(task(item_type))

        # Run all tasks concurrently
        await asyncio.gather(*tasks)
        return {"message": f"Started scraping for {item}."}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

