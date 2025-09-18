import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import pandas as pd
from core.search_parser import ZakupkiSearchParser

st.set_page_config(page_title="Закупки РФ", layout="wide")

st.title("🔎 Поиск закупок")

# Поле для запроса
query = st.text_input("Введите ключевое слово для поиска:", "бумага")

if st.button("Искать"):
    with ZakupkiSearchParser(headless=True) as parser:
        with st.spinner("Открываем сайт..."):
            parser.open_site()

        with st.spinner("Применяем фильтры..."):
            parser.set_filters()

        with st.spinner("Выполняем поиск..."):
            parser.search_query(query)

        with st.spinner("Парсим результаты..."):
            orders = parser.parse_orders(limit=30)

    if orders:
        st.success(f"Найдено {len(orders)} закупок")
        df = pd.DataFrame(orders)
        st.dataframe(df, use_container_width=True)

        # Чекбоксы для выбора
        selected = st.multiselect(
            "Выберите закупки для детального анализа",
            options=[o["number"] for o in orders],
            format_func=lambda x: f"{x} | {next(o['title'] for o in orders if o['number']==x)}"
        )

        if selected:
            st.info(f"Вы выбрали {len(selected)} закупок")
            st.write([o for o in orders if o["number"] in selected])
    else:
        st.warning("⚠️ Закупки не найдены")