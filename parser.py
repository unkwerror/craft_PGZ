import time
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class ZakupkiParser:
    def __init__(self):
        self.driver = self._init_driver()
        self.base_url = "https://zakupki.gov.ru/epz/order/notice/ea20/view/common-info.html?regNumber="

    def _init_driver(self) -> webdriver.Chrome:
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        )
        options.add_argument(f'user-agent={user_agent}')
        return webdriver.Chrome(options=options)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    def load_page(self, reg_number: str):
        url = self.base_url + reg_number
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".cardMainInfo"))
        )
        time.sleep(1)  # чуть-чуть подождать рендер

    def save_html(self, filename="page.html"):
        html = self.driver.page_source
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html)

    def parse_tender_card(self) -> dict:
        """Парсит карточку закупки в соответствии с ТЗ"""
        data = {}

        def safe_xpath(xpath: str):
            try:
                return self.driver.find_element(By.XPATH, xpath).text.strip()
            except:
                return None

        # Номер заявки
        data["reg_number"] = self.driver.current_url.split("regNumber=")[-1]

        # Название закупки
        data["title"] = safe_xpath('/html/body/div[2]/div/div[1]/div[2]/div[2]/div[1]/div[2]/div[1]/span[2]')

        # Сумма контракта (НМЦК)
        data["price"] = safe_xpath(
            '/html/body/div[2]/div/div[1]/div[2]/div[2]/div[2]/div[1]/span[2]'
        )

        # Сроки размещения заявки (окончание подачи)
        data["end_date"] = safe_xpath(
            '/html/body/div[2]/div/div[1]/div[2]/div[2]/div[2]/div[2]/div[2]/span[2]'
        )

        return data


if __name__ == "__main__":
    reg_number = "0162200011825003267"
    reg_number2 = "0162300005325001781"

    with ZakupkiParser() as parser:
        parser.load_page(reg_number)
        info = parser.parse_tender_card()
        print(info)

