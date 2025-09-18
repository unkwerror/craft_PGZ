import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException


class BaseParser:
    def __init__(self, headless: bool = True, timeout: int = 20):
        self.driver = self._init_driver(headless)
        self.timeout = timeout

    def _init_driver(self, headless: bool) -> webdriver.Chrome:
        options = Options()
        if headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/140.0.0.0 Safari/537.36"
        )
        options.add_argument(f"user-agent={user_agent}")
        return webdriver.Chrome(options=options)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()

    def wait(self, seconds: float = 1.0):
        time.sleep(seconds)

    def safe_find(self, by: By, selector: str, timeout: int | None = None):
        try:
            wait = WebDriverWait(self.driver, timeout or self.timeout)
            return wait.until(EC.presence_of_element_located((by, selector)))
        except Exception:
            return None

    def safe_finds(self, by: By, selector: str, timeout: int | None = None):
        try:
            wait = WebDriverWait(self.driver, timeout or self.timeout)
            return wait.until(EC.presence_of_all_elements_located((by, selector)))
        except Exception:
            return []

    def click_element(self, by: By, selector: str, timeout: int | None = None, use_js_fallback: bool = True):
        try:
            wait = WebDriverWait(self.driver, timeout or self.timeout)
            element = wait.until(EC.element_to_be_clickable((by, selector)))
            element.click()
            return True
        except ElementClickInterceptedException:
            if use_js_fallback:
                try:
                    element = self.driver.find_element(by, selector)
                    self.driver.execute_script("arguments[0].click();", element)
                    return True
                except Exception as e:
                    print(f"[click_element] JS click тоже не удался: {e}")
                    return False
        except TimeoutException:
            print(f"[click_element] Элемент {selector} не найден за время ожидания")
            return False
        except Exception as e:
            print(f"[click_element] Ошибка: {e}")
            return False
