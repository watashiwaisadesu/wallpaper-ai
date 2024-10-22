import logging
import asyncio

from app.core import get_async_db
from .web_scraper import WebScraper
from .product_parser import ProductParser
from .product_saver import ProductSaver

logger = logging.getLogger(__name__)

async def main(base_url, url_path, item, session):
    page_id = 1
    scraper = WebScraper(base_url, url_path)
    while True:
        page_content, current_url = scraper.get_page_source(page_id)
        expected_url = f"{scraper.base_url}{scraper.url_path}/" if page_id == 1 else f"{scraper.base_url}{scraper.url_path}/?page={page_id}"
        if current_url != expected_url:
            logger.info(f"Redirection detected. Expected: {expected_url}, but got: {current_url}. Stopping.")
            break

        parser = ProductParser(page_content, item, page_id)
        products = parser.parse_products()

        if not products:
            logger.info(f"No products found on page {page_id}. Stopping the scraping process.")
            break

        await ProductSaver.save_products(products, session)
        page_id += 1
    scraper.close_driver()

async def parse(item: str, session):
    print(f"Parsing {item}...")
    if item == 'tiles':
        await main(base_url="https://leroymerlin.kz/catalogue", url_path="/plitka-keramogranit-i-mozaika", item='tiles', session=session)
    elif item == 'wallpapers':
        await main(base_url="https://leroymerlin.kz/catalogue", url_path="/oboi-dlya-sten-i-potolka", item='wallpapers', session=session)

async def run_parse(item: str):
    async for session in get_async_db():
        await parse(item, session)

if __name__ == '__main__':
    asyncio.create_task(run_parse('tiles'))
    asyncio.create_task(run_parse('wallpapers'))
