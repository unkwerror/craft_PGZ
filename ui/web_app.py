# ui/web_app.py

import sys
from pathlib import Path

# Добавляем корень проекта (где лежит папка core) в sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))

import streamlit as st
from core.search_parser import ZakupkiSearchParser
from core.tender_parser import ZakupkiTenderParser
from core.services.excel_service import ExcelService

st.set_page_config(page_title="Госзакупки Парсер", layout="wide")

st.title("🔎 Парсер госзакупок")

# 1. Ввод запроса
query = st.text_input("Введите запрос для поиска", "шкафы металлические")
limit = st.slider("Максимум заказов", 5, 50, 10)

if st.button("Найти заказы"):
    with ZakupkiSearchParser(headless=True) as parser:
        st.write("Открываю сайт...")
        parser.open_site()
        parser.set_filters()
        parser.search_query(query)
        results = parser.parse_orders(limit=limit)

    if not results:
        st.warning("Ничего не найдено")
    else:
        st.success(f"Найдено {len(results)} заказов")
        selected_numbers = []
        for r in results:
            if st.checkbox(f"{r.number} | {r.title} | {r.price} | {r.customer}", key=r.number):
                selected_numbers.append(r.number)

        if selected_numbers:
            st.write("Выбраны заказы:", selected_numbers)

            if st.button("Спарсить выбранные"):
                excel_service = ExcelService()
                for num in selected_numbers:
                    with ZakupkiTenderParser(headless=True) as tparser:
                        st.write(f"📄 Парсинг {num} ...")
                        tparser.load_page(num)
                        tender = tparser.parse_tender_card()
                        tparser.save_html(num)
                        tparser.download_all_documents(num, tender.documents)
                        path = excel_service.save_tender(tender)
                        st.success(f"✅ Сохранено: {path}")
