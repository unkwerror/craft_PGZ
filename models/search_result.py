# models/search_result.py
from dataclasses import dataclass

@dataclass
class SearchResult:
    """Краткая карточка закупки (результат поиска)"""
    number: str      # № закупки
    title: str       # объект закупки
    customer: str    # заказчик
    price: str       # цена (строкой, так как в выдаче бывает форматированная ₽)
    type: str        # ФЗ (например: 44-ФЗ, 223-ФЗ)