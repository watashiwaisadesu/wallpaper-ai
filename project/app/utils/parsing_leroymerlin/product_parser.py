import logging
import re
import asyncio
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ProductParser:
    def __init__(self, page_content: str, item_is: str, page_number):
        self.soup = BeautifulSoup(page_content, 'lxml')
        self.product_type = item_is
        self.page_number = page_number

    async def parse_products(self) -> list:
        """Extract product details from the page content asynchronously."""
        catalog_items = self.soup.find_all('li', class_='catalog-lvl3-page__catalog-item')

        if not catalog_items:
            logger.warning("No catalog_items found.")
            return []

        logger.info(f"Found {len(catalog_items)} catalog_item(s). {self.page_number}===={self.product_type}")

        # Create a list of tasks for each product parsing
        tasks = [self._parse_product(item, index + 1, len(catalog_items)) for index, item in enumerate(catalog_items)]

        # Gather the results of all tasks
        products = await asyncio.gather(*tasks)

        # Filter out None values from the results
        return [product for product in products if product is not None]

    async def _parse_product(self, item, index, total_items) -> dict:
        tag_lookup = {
            'wallpapers': lambda: item.find('a', attrs={'data-slick-index': '1'}),
            'tiles': lambda: item.find('a'),
        }

        a_tag = tag_lookup.get(self.product_type, lambda: item.find('a'))()

        if not a_tag:
            logger.warning(f"No appropriate <a> tag found in catalog_item {index}.")
            return None

        full_url = f"https://leroymerlin.kz{a_tag.get('href')}"
        img_url = a_tag.find('img')['src'] if a_tag.find('img') else None
        product_name = item.find('a', class_='catalog__name').get_text(strip=True) if item.find('a',
                                                                                                class_='catalog__name') else None

        price_str = item.find('p', class_='catalog__price').get_text(strip=True).replace('\xa0', ' ') if item.find('p',
                                                                                                                   class_='catalog__price') else None


        # Use regex to extract the numeric part and the price type
        match = re.match(r'([\d\s,]+)(₸/.*)', price_str)
        price_value = None
        price_type = None

        if match:
            price_value_str = match.group(1).replace(' ', '').replace(',', '.')
            price_value = float(price_value_str)
            price_type = match.group(2)

        else:
            logger.warning("Could not parse the price value.")

        return {
            "name": product_name,
            "url": full_url,
            "image_url": img_url,
            "price": price_value,
            "price_type": price_type,
            "product_type": self.product_type,
        }
