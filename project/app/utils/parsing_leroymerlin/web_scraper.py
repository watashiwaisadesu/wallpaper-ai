import logging


logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self, base_url: str, url_path: str, driver):
        self.base_url = base_url
        self.url_path = url_path
        self.driver = driver

    def get_page_source(self, page_id: int) -> (str, str):
        url = f"{self.base_url}{self.url_path}/?page={page_id}"
        self.driver.get(url)
        logger.info(f"Accessing {url}")

        current_url = self.driver.current_url
        logger.info(f"current_url: {current_url}")
        page_source = self.driver.page_source
        return page_source, current_url
