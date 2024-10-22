import logging
from bs4 import BeautifulSoup
import re

logger = logging.getLogger(__name__)


class ProductParser:
    def __init__(self, page_content: str, item_is: str, page_number):
        self.soup = BeautifulSoup(page_content, 'lxml')
        self.product_type = item_is
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
        logger.info(f"Processing catalog_item {index}/{total_items}")
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

        price_str = item.find('p', class_='catalog__price').get_text(strip=True).replace('\xa0', ' ') if item.find(
            'p', class_='catalog__price') else None
        logger.warning(f"price_value: {price_str}")
        # Use regex to extract the numeric part and the price type
        match = re.match(r'([\d\s,]+)(₸/.*)', price_str)
        if match:
            price_value_str = match.group(1).replace(' ', '').replace(',','.')
            price_value = float(price_value_str)
            price_type = match.group(2)

            print(f"Price: {price_value}")
            print(f"Price Type: {price_type}")
        else:
            print("Could not parse the price value.")

        return {
            "name": product_name,
            "url": full_url,
            "image_url": img_url,
            "price": price_value,
            "price_type": price_type,
            "product_type": self.product_type,
        }

