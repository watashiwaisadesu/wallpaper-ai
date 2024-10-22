from fastapi import FastAPI, HTTPException
import asyncio
from app.utils.parsing_leroymerlin import run_parse

app = FastAPI()

@app.post("/scrape/{item}")
async def scrape_item(item: str):
    if item not in ['tiles', 'wallpapers']:
        raise HTTPException(status_code=400, detail="Invalid item. Choose 'tiles' or 'wallpapers'.")

    try:
        asyncio.create_task(run_parse(item))
        return {"message": f"Started scraping for {item}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
