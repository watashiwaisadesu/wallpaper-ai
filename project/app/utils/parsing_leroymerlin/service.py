import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from .web_scraper import WebScraper
from .product_parser import ProductParser
from .product_saver import ProductSaver
from app.core import get_async_db



logger = logging.getLogger(__name__)


async def run_parse(item: str):
    driver = _init_driver()  # Initialize the driver once here
    try:
        await parse(item, driver)
    finally:
        driver.quit()  # Ensure the driver is closed after parsing

async def parse(item: str, driver):
    print(f"Parsing {item}...")
    if item == 'tiles':
        await main(base_url="https://leroymerlin.kz/catalogue", url_path="/plitka-keramogranit-i-mozaika", item='tiles', driver=driver)
    elif item == 'wallpapers':
        await main(base_url="https://leroymerlin.kz/catalogue", url_path="/oboi-dlya-sten-i-potolka", item='wallpapers', driver=driver)

def _init_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

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


def fetch_page_source(driver, url):
    logger.info(f"Fetching page: {url}")  # Логирование URL страницы
    driver.get(url)
    page_source = driver.page_source
    logger.info(f"Fetched page: {url}")  # Логирование успешного получения страницы
    return page_source

async def get_page_source_async(executor, driver, url):
    loop = asyncio.get_running_loop()
    logger.info(f"Starting to fetch {url} in a worker.")
    return await loop.run_in_executor(executor, fetch_page_source, driver, url)

async def main(base_url, url_path, item, driver):
    scraper = WebScraper(base_url, url_path, driver)
    valid_pages = []
    total_pages = scraper.get_total_pages()

    executor = ThreadPoolExecutor(max_workers=5)

    tasks = []
    page_id = 1
    for page in range(1, total_pages + 1):
        url = f"{base_url}{url_path}/?page={page_id}"
        tasks.append(get_page_source_async(executor, driver, url))
        page_id += 1

    page_contents = await asyncio.gather(*tasks)

    for page_id, page_content in enumerate(page_contents, 1):
        valid_pages.append(parse_product_and_save(page_content, item, page_id))

    await asyncio.gather(*valid_pages)
