import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from sqlalchemy.future import select

from app.db.repositories import save
from app.db.models import LeroyMerlin

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self, base_url: str, url_path: str):
        self.base_url = base_url
        self.url_path = url_path
        self.driver = self._init_driver()

    def _init_driver(self):
        """Initialize the Selenium WebDriver."""
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')

        return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    def get_page_source(self, page_id: int) -> (str, str):
        """Fetch the HTML content of the webpage and return the current URL."""
        url = f"{self.base_url}{self.url_path}/?page={page_id}"
        self.driver.get(url)
        logger.info(f"Accessing {url}")

        current_url = self.driver.current_url
        logger.info(f"current_url: {current_url}")
        page_source = self.driver.page_source
        return page_source, current_url

    def close_driver(self):
        """Close the Selenium WebDriver."""
        self.driver.quit()


class ProductParser:
    def __init__(self, page_content: str, item_is: str, page_number):
        """
        Initialize with page content and a flag for different parsing logic.
        item_is: str - The type of product, e.g., 'tiles', 'wallpapers', etc.
        """
        self.soup = BeautifulSoup(page_content, 'lxml')
        self.item_is = item_is  # The type of item being parsed
        self.page_number = page_number

    def parse_products(self) -> list:
        """Extract product details from the page content."""
        catalog_items = self.soup.find_all('li', class_='catalog-lvl3-page__catalog-item')

        if not catalog_items:
            logging.warning("No catalog_items found.")
            return []

        logger.info(f"Found {len(catalog_items)} catalog_item(s).")

        products = []
        for i, item in enumerate(catalog_items, start=1):
            product_data = self._parse_product(item, i, len(catalog_items))
            if product_data:
                products.append(product_data)
        return products

    def _parse_product(self, item, index, total_items) -> dict:
        """Parse individual product item based on item type."""
        logger.info(f"Processing catalog_item {index}/{total_items}")
        # Dictionary-based dispatch (switch-case alternative in Python)
        tag_lookup = {
            'wallpapers': lambda: item.find('a', attrs={'data-slick-index': '1'}),
            'tiles': lambda: item.find('a'),
            # Add more item types here as needed
        }

        # Default to a generic <a> tag lookup if no specific logic is provided
        a_tag = tag_lookup.get(self.item_is, lambda: item.find('a'))()

        if not a_tag:
            logger.warning(f"No appropriate <a> tag found in catalog_item {index}.")
            return None

        # Extract product details
        full_url = f"https://leroymerlin.kz{a_tag.get('href')}"
        img_url = a_tag.find('img')['src'] if a_tag.find('img') else None
        product_name = item.find('a', class_='catalog__name').get_text(strip=True) if item.find('a', class_='catalog__name') else None
        price_value = item.find('p', class_='catalog__price').get_text(strip=True).replace('\xa0', ' ') if item.find('p', class_='catalog__price') else None

        return {
            "name": product_name,
            "url": full_url,
            "image_url": img_url,
            "price": price_value,
            "item_name": self.item_is,
            "page_number": self.page_number
        }


class ProductSaver:
    @staticmethod
    async def save_products(products, session):
        for product in products:
            # Check if the product already exists in the database
            existing_product = await session.execute(
                select(LeroyMerlin).filter(
                    LeroyMerlin.item_name == product['item_name'],
                    LeroyMerlin.page_number == product['page_number'],
                    LeroyMerlin.name == product['name']
                )
            )
            existing_product = existing_product.scalars().first()

            if existing_product:
                logger.info(f"Product already exists: {product['item_name']} on page {product['page_number']}. Skipping save.")
                continue  # Skip saving if the product already exists

            new_product = LeroyMerlin(**product)
            await save(new_product, session)

        logger.info(f"Saved {len(products)} new products to the database.")


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

        if not products:  # Stop if no products are found on the current page
            logger.info(f"No products found on page {page_id}. Stopping the scraping process.")
            break

        await ProductSaver.save_products(products, session)
        page_id += 1
    scraper.close_driver()



async def parse(item: str, session):
    print(f"Parsing {item}...")
    if item == 'tiles':
        await main( base_url="https://leroymerlin.kz/catalogue", url_path="/plitka-keramogranit-i-mozaika",
             item='tiles', session=session)
    elif item == 'wallpapers':
        await main(base_url="https://leroymerlin.kz/catalogue", url_path="/oboi-dlya-sten-i-potolka",
             item='wallpapers', session=session)

