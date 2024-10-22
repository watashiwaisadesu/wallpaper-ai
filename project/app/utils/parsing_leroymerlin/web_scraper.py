import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
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
