# core/search_parser.py
from selenium.webdriver.common.by import By
from core.base_parser import BaseParser
from models.search_result import SearchResult


class ZakupkiSearchParser(BaseParser):
    BASE_URL = "https://zakupki.gov.ru/epz/order/extendedsearch/results.html"

    def open_site(self):
        self.open(self.BASE_URL)

    def set_filters(self):
        # Снимаем все галочки
        checkboxes = self.safe_finds(By.CSS_SELECTOR, "#orderStages input[type='checkbox']")
        for cb in checkboxes:
            if cb.is_selected():
                self.driver.execute_script("arguments[0].click();", cb)

        # Ставим только "Подача заявок"
        af = self.safe_find(By.ID, "af")
        if af and not af.is_selected():
            self.driver.execute_script("arguments[0].click();", af)

        self.wait(1)

    def search_query(self, query: str):
        search_input = self.safe_find(By.ID, "searchString")
        if search_input:
            search_input.clear()
            search_input.send_keys(query)

        self.click_element(By.CSS_SELECTOR, ".search__btn")
        self.safe_finds(By.CSS_SELECTOR, ".search-registry-entry-block")
        self.wait(2)

    def parse_orders(self, limit: int = 20) -> list[SearchResult]:
        cards = self.safe_finds(By.CSS_SELECTOR, ".search-registry-entry-block")
        results: list[SearchResult] = []

        for card in cards[:limit]:
            try:
                results.append(
                    SearchResult(
                        number=card.find_element(By.CSS_SELECTOR, ".registry-entry__header-mid__number a").text.strip(),
                        type=card.find_element(By.CSS_SELECTOR, ".registry-entry__header-top__title").text.strip(),
                        title=card.find_element(By.CSS_SELECTOR, ".registry-entry__body-value").text.strip(),
                        customer=card.find_element(By.CSS_SELECTOR, ".registry-entry__body-href a").text.strip(),
                        price=card.find_element(By.CSS_SELECTOR, ".price-block__value").text.strip(),
                    )
                )
            except Exception as e:
                print("Ошибка парсинга карточки:", e)

        return results
