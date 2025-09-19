# core/base_parser.py
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BaseParser:
    def __init__(self, headless: bool = True, wait_time: int = 20):
        self.wait_time = wait_time
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        self.driver = webdriver.Chrome(options=options)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    # ---------- Утилиты ожидания ----------
    def wait(self, seconds: float):
        """Просто sleep"""
        time.sleep(seconds)

    def wait_until(self, condition):
        return WebDriverWait(self.driver, self.wait_time).until(condition)

    # ---------- Поиск ----------
    def safe_find(self, by: By, value: str):
        try:
            return self.wait_until(EC.presence_of_element_located((by, value)))
        except Exception:
            return None

    def safe_finds(self, by: By, value: str):
        try:
            return self.wait_until(EC.presence_of_all_elements_located((by, value)))
        except Exception:
            return []

    def safe_text(self, by: By, value: str) -> str:
        el = self.safe_find(by, value)
        return el.text.strip() if el else ""

    def safe_attr(self, by: By, value: str, attr: str) -> str:
        el = self.safe_find(by, value)
        return el.get_attribute(attr).strip() if el else ""

    # ---------- Клики ----------
    def click_element(self, by: By, value: str, use_js_fallback=True):
        """Клик по элементу, с fallback на JS"""
        el = self.safe_find(by, value)
        if not el:
            return False
        try:
            el.click()
            return True
        except Exception:
            if use_js_fallback:
                try:
                    self.driver.execute_script("arguments[0].click();", el)
                    return True
                except Exception:
                    return False
            return False

    # ---------- Навигация ----------
    def open(self, url: str):
        self.driver.get(url)
