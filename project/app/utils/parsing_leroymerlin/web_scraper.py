import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self, base_url: str, url_path: str, driver):
        self.base_url = base_url
        self.url_path = url_path
        self.driver = driver

    def get_page_source(self, page_id: int) -> (str, str):
        url = f"{self.base_url}{self.url_path}/?page={page_id}"
        self.driver.get(url)
        page_source = self.driver.page_source
        return page_source

    def get_total_pages(self) -> int:
        # Access the first page to retrieve the total number of pages
        self.driver.get(f"{self.base_url}{self.url_path}/")
        logger.info(f"Accessing {self.base_url}{self.url_path}/")

        # Loop to click the "Load More" button until it disappears
        while True:
            try:
                load_more_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "btn_more"))
                )
                load_more_button.click()
                logger.info("Clicked 'Load More' button.")
                time.sleep(2)  # Wait for new content to load
            except Exception as e:
                logger.info("No more 'Load More' button found or another error occurred.")
                break

        # After clicking "Load More", parse the final pagination element
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        pagination = soup.find('div', class_='pagination pagination_small catalog-controls__pagination')

        # Extract the last page number from the pagination links
        if pagination:
            pages = pagination.find_all('a', class_='pagination__item')
            if pages:
                last_page = int(pages[-1].text.strip())
                logger.info(f"Total pages found: {last_page}")
                return last_page

        logger.warning("No pagination found or pagination structure is different.")
        return 0  # No pagination found


