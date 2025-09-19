#core/tender_parser.py
import time
import requests
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from core.base_parser import BaseParser
from core.services.file_service import FileService
from models.tender import Tender, Document


class ZakupkiTenderParser(BaseParser):
    def __init__(self, base_output_dir="results", headless=True):
        super().__init__(headless=headless)
        self.base_url = (
            "https://zakupki.gov.ru/epz/order/notice/ea20/view/common-info.html?regNumber="
        )
        self.file_service = FileService(base_output_dir)

    # -----------------------------
    # Загрузка страницы тендера
    # -----------------------------
    def load_page(self, reg_number: str):
        url = self.base_url + reg_number
        self.driver.get(url)
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".cardMainInfo"))
        )
        time.sleep(1)

    # -----------------------------
    # Работа с вкладкой "Документы"
    # -----------------------------
    def click_documents_tab(self):
        try:
            documents_tab = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located(
                    (By.XPATH, "/html/body/div[2]/div/div[1]/div[3]/div/a[2]")
                )
            )
            self.driver.execute_script("arguments[0].scrollIntoView(true);", documents_tab)
            time.sleep(1)
            self.driver.execute_script("arguments[0].click();", documents_tab)

            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "blockFilesTabDocs"))
            )
            time.sleep(1)
            return True
        except Exception:
            return False

    def expand_all_documents(self):
        try:
            show_more_button = self.driver.find_element(
                By.XPATH, "//a[contains(text(), 'Показать больше')]"
            )
            show_more_button.click()
            time.sleep(1)
            return True
        except:
            return False

    def parse_documents(self) -> list[Document]:
        docs: list[Document] = []
        self.expand_all_documents()
        containers = self.driver.find_elements(
            By.CSS_SELECTOR, ".blockFilesTabDocs .attachment"
        )

        for container in containers:
            try:
                link = container.find_element(
                    By.CSS_SELECTOR, ".section__value a, a[href*='download']"
                )
                name = link.text.strip()
                url = link.get_attribute("href")
                original_filename = (
                    link.get_attribute("title")
                    or link.get_attribute("data-filename")
                    or name
                )
                docs.append(
                    Document(name=name, url=url, original_filename=original_filename)
                )
            except Exception:
                continue
        return docs

    def download_document(self, reg_number: str, doc: Document) -> Path | None:
        try:
            cookies = self.driver.get_cookies()
            session = requests.Session()
            for cookie in cookies:
                session.cookies.set(cookie["name"], cookie["value"])

            headers = {
                "User-Agent": self.driver.execute_script("return navigator.userAgent;")
            }
            response = session.get(doc.url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()

            filepath = self.file_service.save_binary(
                reg_number, doc.original_filename, response.content
            )
            return filepath
        except Exception:
            return None

    def download_all_documents(self, reg_number: str, docs: list[Document]):
        saved_files = []
        for doc in docs:
            filepath = self.download_document(reg_number, doc)
            if filepath:
                saved_files.append(filepath)
        return saved_files

    # -----------------------------
    # Сохранение HTML
    # -----------------------------
    def save_html(self, reg_number: str, filename="page.html"):
        html = self.driver.page_source
        return self.file_service.save_text(reg_number, filename, html)

    # -----------------------------
    # Парсинг карточки тендера
    # -----------------------------
    def parse_tender_card(self) -> Tender:
        def safe_xpath(xpath: str):
            try:
                return self.driver.find_element(By.XPATH, xpath).text.strip()
            except:
                return None

        reg_number = self.driver.current_url.split("regNumber=")[-1]
        title = safe_xpath(
            "/html/body/div[2]/div/div[1]/div[2]/div[2]/div[1]/div[2]/div[1]/span[2]"
        )
        price = safe_xpath(
            "/html/body/div[2]/div/div[1]/div[2]/div[2]/div[2]/div[1]/span[2]"
        )
        end_date = safe_xpath(
            "/html/body/div[2]/div/div[1]/div[2]/div[2]/div[2]/div[2]/div[2]/span[2]"
        )

        documents = []
        if self.click_documents_tab():
            documents = self.parse_documents()

        return Tender(
            reg_number=reg_number,
            title=title,
            price=price,
            end_date=end_date,
            documents=documents,
        )
