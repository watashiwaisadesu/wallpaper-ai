import logging
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from .web_scraper import WebScraper
from .product_parser import ProductParser
from .product_saver import ProductSaver
from app.core import get_async_db


logger = logging.getLogger(__name__)

async def parse_product_and_save(page_content, item, page_id):
    """Create a new session for each page parsing operation."""
    async for session in get_async_db():  # Create a new session for each page
        print(f"parse_product_and_save====={page_id}     {item}")
        parser = ProductParser(page_content, item, page_id)
        products = await parser.parse_products()

        if products:
            await ProductSaver.save_products(products, session)
        else:
            logger.info(f"No products found on page {page_id}.")

async def main(base_url, url_path, item, driver):
    scraper = WebScraper(base_url, url_path, driver)
    valid_pages = []  # List to store valid page contents

    # Fetch pages and store valid ones
    page_id = 1
    while True:
        page_content, current_url = scraper.get_page_source(page_id)
        expected_url = f"{scraper.base_url}{scraper.url_path}/" if page_id == 1 else f"{scraper.base_url}{scraper.url_path}/?page={page_id}"
        if current_url != expected_url:
            logger.info(f"Redirection detected. Expected: {expected_url}, but got: {current_url}. Stopping.")
            break

        # Store valid page content
        print(f"{item}_page: {page_id}")
        valid_pages.append(parse_product_and_save(page_content, item, page_id))
        print(f"tasks:{valid_pages}")
        page_id += 1

    # Wait for all parsing tasks to complete
    await asyncio.gather(*valid_pages)


async def parse(item: str, driver):
    print(f"Parsing {item}...")
    if item == 'tiles':
        await main(base_url="https://leroymerlin.kz/catalogue", url_path="/plitka-keramogranit-i-mozaika", item='tiles', driver=driver)
    elif item == 'wallpapers':
        await main(base_url="https://leroymerlin.kz/catalogue", url_path="/oboi-dlya-sten-i-potolka", item='wallpapers', driver=driver)



async def run_parse(item: str):
    driver = _init_driver()  # Initialize the driver once here
    try:
        await parse(item, driver)
    finally:
        driver.quit()  # Ensure the driver is closed after parsing

def _init_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)