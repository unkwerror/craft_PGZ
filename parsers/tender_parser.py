from selenium.webdriver.common.by import By
from pathlib import Path
import requests
from .base_parser import BaseParser

class ZakupkiTender(BaseParser):
    BASE_URL = "https://zakupki.gov.ru/epz/order/notice/ea20/view/common-info.html?regNumber="

    def __init__(self, base_output_dir="results", headless=True):
        super().__init__(headless=headless)
        self.base_output_dir = Path(base_output_dir)
        self.base_output_dir.mkdir(exist_ok=True)

    def create_tender_folder(self, reg_number: str) -> Path:
        tender_path = self.base_output_dir / reg_number
        tender_path.mkdir(exist_ok=True)
        return tender_path

    def load_page(self, reg_number: str):
        self.driver.get(f"{self.BASE_URL}{reg_number}")
        self.safe_find(By.CSS_SELECTOR, ".cardMainInfo")
        self.wait(1)

    def click_documents_tab(self):
        if not self.click_element(By.XPATH, "/html/body/div[2]/div/div[1]/div[3]/div/a[2]"):
            # fallback прямой URL
            reg_number = self.driver.current_url.split("regNumber=")[-1]
            self.driver.get(f"https://zakupki.gov.ru/epz/order/notice/ea20/view/documents.html?regNumber={reg_number}")
            self.safe_find(By.CLASS_NAME, "blockFilesTabDocs")
        self.wait(1)

    def expand_all_documents(self):
        self.click_element(By.XPATH, "//a[contains(text(), 'Показать больше')]", use_js_fallback=True)

    def parse_documents(self):
        self.expand_all_documents()
        documents = []
        containers = self.safe_finds(By.CSS_SELECTOR, ".blockFilesTabDocs .attachment")
        for c in containers:
            try:
                link = c.find_element(By.CSS_SELECTOR, ".section__value a, a[href*='download']")
                name = link.text.strip()
                url = link.get_attribute("href")
                original_filename = link.get_attribute("title") or link.get_attribute("data-filename") or name
                documents.append({"name": name, "url": url, "original_filename": original_filename})
            except Exception as e:
                print(f"Ошибка при парсинге документа: {e}")
        return documents

    def download_document(self, url, filepath):
        try:
            session = requests.Session()
            for cookie in self.driver.get_cookies():
                session.cookies.set(cookie['name'], cookie['value'])
            headers = {'User-Agent': 'Mozilla/5.0', 'Referer': self.driver.current_url}
            r = session.get(url, headers=headers, stream=True, timeout=30)
            r.raise_for_status()
            with open(filepath, "wb") as f:
                for chunk in r.iter_content(8192):
                    if chunk: f.write(chunk)
            return True
        except Exception as e:
            print(f"Ошибка при скачивании {url}: {e}")
            return False
