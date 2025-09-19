# web/streamlit_app.py - Полностью исправленная версия с реальным парсингом
import streamlit as st
import asyncio
import logging
from decimal import Decimal
from typing import List, Dict, Any
from datetime import datetime
import pandas as pd
import sys
from pathlib import Path

# Добавляем корневую директорию в Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

try:
    from application.services.economics_service import EconomicsService
    from application.services.search_service import SearchService
    from domain.value_objects.economics import ProjectConfig, TeamRole, ProjectType, DEFAULT_TEAM_TEMPLATES
    from domain.value_objects.search import SearchCriteria
    from infrastructure.parsers.http_parser import HttpTenderParser
    from infrastructure.cache.simple_cache import SimpleCache
    from infrastructure.database.repositories.memory_repository import MemoryTenderRepository
    from core.config import get_settings
except ImportError as e:
    st.error(f"❌ Ошибка импорта: {e}")
    st.info("📌 Убедитесь, что все __init__.py файлы созданы и структура папок правильная")
    st.stop()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация страницы
st.set_page_config(
    page_title="Tender Analyzer 2.0",
    page_icon="📊", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS стили
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e6e9ef;
        margin-bottom: 1rem;
    }
    
    .profit-positive {
        color: #00C851;
        font-weight: bold;
    }
    
    .profit-negative {
        color: #ff4444;
        font-weight: bold;
    }
    
    .risk-low { color: #00C851; }
    .risk-medium { color: #ffbb33; }
    .risk-high { color: #ff4444; }
    .risk-critical { color: #CC0000; }
    
    .tender-card {
        border: 1px solid #e6e9ef;
        border-radius: 0.5rem;
        padding: 1rem;
        margin-bottom: 1rem;
    }
    
    .tender-title {
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .tender-info {
        color: #666;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

class TenderAnalyzerApp:
    """Основное приложение Streamlit"""
    
    def __init__(self):
        try:
            self.settings = get_settings()
            self._init_services()
            self._init_session_state()
        except Exception as e:
            st.error(f"❌ Ошибка инициализации: {e}")
            st.stop()
    
    def _init_services(self):
        """Инициализация сервисов"""
        try:
            # Инициализация зависимостей
            cache = SimpleCache()
            repository = MemoryTenderRepository()
            parser = HttpTenderParser()
            
            # Создание сервисов
            self.search_service = SearchService(parser, cache, repository)
            self.economics_service = EconomicsService()
            
            logger.info("✅ Сервисы инициализированы")
        except Exception as e:
            logger.error(f"❌ Ошибка инициализации сервисов: {e}")
            raise
    
    def _init_session_state(self):
        """Инициализация состояния сессии"""
        if 'search_results' not in st.session_state:
            st.session_state.search_results = []
        
        if 'selected_tenders' not in st.session_state:
            st.session_state.selected_tenders = []
        
        if 'economics_results' not in st.session_state:
            st.session_state.economics_results = {}
        
        if 'last_search_query' not in st.session_state:
            st.session_state.last_search_query = ""
    
    def run(self):
        """Запуск приложения"""
        st.title("🏢 Tender Analyzer 2.0")
        st.markdown("*Анализ государственных закупок с реальными данными zakupki.gov.ru*")
        
        # Боковая панель с навигацией
        with st.sidebar:
            st.header("📋 Навигация")
            page = st.selectbox(
                "Выберите раздел:",
                ["🔍 Поиск тендеров", "💰 Расчет экономики", "📊 Аналитика", "⚙️ Настройки"]
            )
            
            # Статистика в сайдбаре
            if st.session_state.search_results:
                st.markdown("### 📈 Статистика")
                st.metric("Найдено тендеров", len(st.session_state.search_results))
                st.metric("Выбрано для анализа", len(st.session_state.selected_tenders))
                st.metric("Расчетов выполнено", len(st.session_state.economics_results))
        
        # Маршрутизация страниц
        if page == "🔍 Поиск тендеров":
            self._render_search_page()
        elif page == "💰 Расчет экономики":
            self._render_economics_page()
        elif page == "📊 Аналитика":
            self._render_analytics_page()
        elif page == "⚙️ Настройки":
            self._render_settings_page()
    
    def _render_search_page(self):
        """Страница поиска тендеров с реальными данными"""
        st.header("🔍 Поиск тендеров на zakupki.gov.ru")
        
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            search_query = st.text_input(
                "Поисковый запрос:",
                value=st.session_state.last_search_query,
                placeholder="Например: благоустройство территории",
                help="Введите ключевые слова для поиска тендеров"
            )
        
        with col2:
            search_limit = st.slider("Количество результатов:", 5, 50, 10)
        
        with col3:
            use_real_parser = st.checkbox("Реальный парсинг", value=True, help="Использовать реальные данные с zakupki.gov.ru")
        
        # Дополнительные фильтры
        with st.expander("🔧 Дополнительные фильтры"):
            col4, col5 = st.columns(2)
            
            with col4:
                price_from = st.number_input("Цена от (руб.):", min_value=0, value=0)
                date_from = st.date_input("Дата размещения от:", value=None)
            
            with col5:
                price_to = st.number_input("Цена до (руб.):", min_value=0, value=0)
                date_to = st.date_input("Дата размещения до:", value=None)
        
        # Кнопка поиска
        if st.button("🔍 Найти тендеры", type="primary"):
            if search_query.strip():
                st.session_state.last_search_query = search_query
                filters = {}
                if price_from > 0:
                    filters['price_from'] = price_from
                if price_to > 0:
                    filters['price_to'] = price_to
                if date_from:
                    filters['date_from'] = date_from.strftime('%d.%m.%Y')
                if date_to:
                    filters['date_to'] = date_to.strftime('%d.%m.%Y')
                
                self._perform_search(search_query, search_limit, filters, use_real_parser)
            else:
                st.warning("⚠️ Введите поисковый запрос")
        
        # Отображение результатов поиска
        self._display_search_results()
    
    def _perform_search(self, query: str, limit: int, filters: Dict, use_real_parser: bool):
        """Выполнение поиска тендеров"""
        with st.spinner("🔍 Поиск тендеров на zakupki.gov.ru..."):
            try:
                if use_real_parser:
                    # Реальный поиск через HTTP парсер
                    search_criteria = SearchCriteria(query=query, limit=limit, filters=filters)
                    
                    # Запускаем асинхронный поиск
                    results = asyncio.run(self._async_search(search_criteria))
                    
                    if results:
                        st.session_state.search_results = results
                        st.success(f"✅ Найдено {len(results)} тендеров на zakupki.gov.ru")
                        
                        # Показываем статистику по типам
                        type_counts = {}
                        for result in results:
                            tender_type = result.get('tender_type', 'unknown')
                            type_counts[tender_type] = type_counts.get(tender_type, 0) + 1
                        
                        st.info(f"📊 Распределение: " + " | ".join([f"{k}: {v}" for k, v in type_counts.items()]))
                    else:
                        st.warning("⚠️ Тендеры не найдены. Попробуйте изменить запрос.")
                else:
                    # Mock данные для тестирования
                    self._mock_search(query, limit)
                    
            except Exception as e:
                st.error(f"❌ Ошибка поиска: {str(e)}")
                logger.error(f"Search error: {e}")
                
                # Fallback на mock данные
                st.info("🔄 Переключаюсь на тестовые данные...")
                self._mock_search(query, limit)
    
    async def _async_search(self, criteria: SearchCriteria):
        """Асинхронный поиск через сервис"""
        try:
            results = await self.search_service.search_tenders(criteria, use_cache=True)
            return [result.to_dict() for result in results]
        except Exception as e:
            logger.error(f"Async search error: {e}")
            raise
    
    def _mock_search(self, query: str, limit: int):
        """Mock поиск для тестирования"""
        import random
        
        mock_results = []
        templates = [
            f"{query} - проект благоустройства",
            f"Капитальный ремонт и {query}",
            f"Строительство объектов {query}",
            f"Проектирование и {query}",
            f"Реконструкция с элементами {query}"
        ]
        
        for i in range(min(limit, 15)):
            template = random.choice(templates)
            mock_results.append({
                'reg_number': f'0162200011825{3000 + i:04d}',
                'title': f'{template} №{i+1}',
                'customer': f'Департамент городского хозяйства г. {["Москва", "СПб", "Екатеринбург", "Новосибирск"][i % 4]}',
                'initial_price': random.randint(1000000, 50000000),
                'tender_type': random.choice(['44-fz', '223-fz']),
                'status': 'active',
                'deadline': datetime.now(),
                'source_url': f'https://zakupki.gov.ru/epz/order/notice/ea44/view/common-info.html?regNumber=0162200011825{3000+i:04d}'
            })
        
        st.session_state.search_results = mock_results
        st.success(f"✅ Найдено {len(mock_results)} тендеров (тестовые данные)")
    
    def _display_search_results(self):
        """Отображение результатов поиска"""
        if not st.session_state.search_results:
            st.info("🔍 Выполните поиск для отображения результатов")
            return
        
        st.markdown(f"### 📋 Результаты поиска ({len(st.session_state.search_results)} тендеров)")
        
        selected_numbers = []
        
        for tender in st.session_state.search_results:
            reg_number = tender.get('reg_number', '')
            title = tender.get('title', '')
            customer = tender.get('customer', '')
            price = tender.get('initial_price', 0)
            tender_type = tender.get('tender_type', '')
            status = tender.get('status', '')
            source_url = tender.get('source_url', '')
            
            # Карточка тендера
            with st.container():
                col1, col2 = st.columns([5, 1])
                
                with col1:
                    # Заголовок как ссылка
                    if source_url:
                        st.markdown(f"**[{title}]({source_url})**")
                    else:
                        st.markdown(f"**{title}**")
                    
                    # Информация о тендере
                    st.markdown(f"📋 **№ {reg_number}** | 🏢 {customer}")
                    st.markdown(f"💰 **{price:,.2f} ₽** | 📜 {tender_type.upper()} | 🔄 {status}")
                
                with col2:
                    if st.checkbox("Выбрать", key=f"select_{reg_number}", help="Выбрать для экономического анализа"):
                        selected_numbers.append(reg_number)
                
                st.divider()
        
        # Обновляем выбранные тендеры
        if selected_numbers:
            st.session_state.selected_tenders = [
                t for t in st.session_state.search_results 
                if t.get('reg_number') in selected_numbers
            ]
            
            st.success(f"📝 Выбрано тендеров для анализа: {len(selected_numbers)}")
    
    def _render_economics_page(self):
        """Страница расчета экономики"""
        st.header("💰 Расчет экономики проектов")
        
        if not st.session_state.selected_tenders:
            st.info("📝 Сначала выберите тендеры на странице поиска")
            
            # Добавим demo тендер для тестирования
            if st.button("🎯 Добавить тестовый тендер"):
                st.session_state.selected_tenders = [{
                    'reg_number': '0162200011825DEMO',
                    'title': 'Благоустройство территории (DEMO)',
                    'customer': 'Департамент благоустройства г. Москва',
                    'initial_price': 5000000,
                    'tender_type': '44-fz',
                    'status': 'active'
                }]
                st.rerun()
            return
        
        # Выбор тендера для расчета
        tender_options = [
            f"{t.get('reg_number', 'N/A')} — {t.get('title', 'Без названия')[:80]}..." 
            for t in st.session_state.selected_tenders
        ]
        
        selected_tender_idx = st.selectbox(
            "Выберите тендер для расчета:",
            range(len(tender_options)),
            format_func=lambda i: tender_options[i]
        )
        
        if selected_tender_idx is not None:
            selected_tender = st.session_state.selected_tenders[selected_tender_idx]
            self._render_economics_calculator(selected_tender)
    
    def _render_economics_calculator(self, tender: Dict[str, Any]):
        """Калькулятор экономики для конкретного тендера"""
        st.subheader(f"📊 Расчет экономики")
        
        # Информация о тендере
        with st.expander("📋 Информация о тендере", expanded=True):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Номер:** {tender.get('reg_number', 'N/A')}")
                st.write(f"**Заказчик:** {tender.get('customer', 'Не указан')}")
            with col2:
                st.write(f"**Цена:** {tender.get('initial_price', 0):,.2f} ₽")
                st.write(f"**Тип:** {tender.get('tender_type', 'N/A').upper()}")
            
            st.write(f"**Название:** {tender.get('title', 'Без названия')}")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("### 👥 Настройка команды")
            
            # Выбор шаблона команды
            template_names = list(DEFAULT_TEAM_TEMPLATES.keys())
            selected_template = st.selectbox(
                "Шаблон команды:",
                template_names,
                help="Выберите готовый шаблон команды"
            )
            
            # Получаем конфигурацию команды
            team_config = DEFAULT_TEAM_TEMPLATES[selected_template].copy()
            
            # Отображение и редактирование команды
            edited_team = self._edit_team_config(team_config)
        
        with col2:
            st.markdown("### ⚙️ Параметры проекта")
            
            project_name = st.text_input("Название проекта:", tender.get('title', 'Проект')[:50])
            duration_months = st.slider("Длительность (месяцы):", 1, 24, 6)
            
            project_type_options = [t.value for t in ProjectType]
            project_type = st.selectbox(
                "Тип проекта:",
                project_type_options,
                format_func=lambda x: {
                    'architecture': 'Архитектура',
                    'engineering': 'Инжиниринг',
                    'landscaping': 'Благоустройство',
                    'complex': 'Комплексный',
                    'restoration': 'Реставрация',
                    'infrastructure': 'Инфраструктура'
                }.get(x, x)
            )
            
            # Накладные расходы
            st.markdown("#### 💼 Накладные расходы")
            office_rent = st.number_input("Аренда офиса (месяц):", value=50000)
            software = st.number_input("ПО и лицензии:", value=30000)
            utilities = st.number_input("Коммунальные услуги:", value=20000)
            
            # Налоги
            st.markdown("#### 📊 Налоги и отчисления")
            income_tax = st.slider("Налог на прибыль (%):", 0, 30, 20) / 100
            social_tax = st.slider("Социальные взносы (%):", 0, 50, 30) / 100
        
        # Кнопка расчета
        if st.button("🧮 Рассчитать экономику", type="primary"):
            try:
                # Создаем конфигурацию проекта
                config = ProjectConfig(
                    project_name=project_name,
                    total_amount=Decimal(str(tender.get('initial_price', 0))),
                    duration_months=duration_months,
                    project_type=ProjectType(project_type),
                    team=edited_team,
                    overhead_costs={
                        "office_rent": Decimal(str(office_rent * duration_months)),
                        "software": Decimal(str(software)),
                        "utilities": Decimal(str(utilities * duration_months))
                    },
                    taxes={
                        "income_tax": income_tax,
                        "social": social_tax
                    }
                )
                
                # Выполняем расчет
                result = self.economics_service.calculate_project_economics(
                    Decimal(str(tender.get('initial_price', 0))), config
                )
                
                # Сохраняем результат
                st.session_state.economics_results[tender.get('reg_number', 'unknown')] = result
                
                # Отображаем результаты
                self._display_economics_results(result)
                
            except Exception as e:
                st.error(f"❌ Ошибка расчета: {str(e)}")
                logger.error(f"Economics calculation error: {e}")
                
                # Показываем подробную информацию об ошибке в debug режиме
                if self.settings.debug:
                    st.exception(e)
    
    def _edit_team_config(self, team_config: Dict[str, TeamRole]) -> Dict[str, TeamRole]:
        """Редактирование конфигурации команды"""
        edited_team = {}
        
        st.markdown("**Состав команды:**")
        
        total_percentage = 0
        
        for role_name, role in team_config.items():
            with st.expander(f"👤 {role_name}", expanded=True):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    percentage = st.slider(
                        f"Процент от проекта (%)",
                        0.0, 50.0, role.percentage * 100,
                        key=f"perc_{role_name}",
                        help=f"Рекомендуемый процент: {role.percentage * 100:.1f}%"
                    ) / 100
                
                with col2:
                    hourly_rate = st.number_input(
                        "Ставка/час (₽)",
                        value=role.hourly_rate or 2000,
                        key=f"rate_{role_name}",
                        min_value=500,
                        max_value=10000
                    )
                
                edited_team[role_name] = TeamRole(
                    name=role_name,
                    percentage=percentage,
                    hourly_rate=hourly_rate,
                    hours_per_month=role.hours_per_month or 80
                )
                
                total_percentage += percentage
        
        # Показываем общий процент с предупреждениями
        total_percentage_display = total_percentage * 100
        
        if total_percentage_display > 100:
            st.error(f"⚠️ Общий процент команды: {total_percentage_display:.1f}% (превышает 100%)")
        elif total_percentage_display < 50:
            st.warning(f"⚠️ Общий процент команды: {total_percentage_display:.1f}% (слишком мало)")
        else:
            st.success(f"✅ Общий процент команды: {total_percentage_display:.1f}%")
        
        return edited_team
    
    def _display_economics_results(self, result):
        """Отображение результатов расчета экономики"""
        st.markdown("---")
        st.markdown("### 📈 Результаты расчета экономики")
        
        # Основные метрики
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            profit_color = "🟢" if result.net_profit > 0 else "🔴"
            st.metric(
                "💰 Чистая прибыль", 
                f"{result.net_profit:,.0f} ₽",
                help=f"Оценка: {result.get_profit_grade()}"
            )
            st.markdown(f"{profit_color} **{result.get_profit_grade()}**")
        
        with col2:
            st.metric("📊 Маржа прибыли", f"{result.profit_margin:.1f}%")
        
        with col3:
            st.metric("📈 ROI", f"{result.roi:.1f}%")
        
        with col4:
            risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}
            risk_color = risk_emoji.get(result.risk_level.value, "🟡")
            st.metric("⚠️ Уровень риска", f"{result.risk_level.value.upper()}")
            st.markdown(f"{risk_color} **Оценка: {result.risk_score:.1f}/1.0**")
        
        # Детализация затрат
        col5, col6 = st.columns(2)
        
        with col5:
            st.markdown("#### 💼 Детализация затрат")
            
            team_data = []
            for role, amount in result.team_breakdown.items():
                team_data.append({
                    'Роль': role,
                    'Сумма (₽)': f"{amount:,.0f}",
                    'Доля (%)': f"{(amount/result.total_revenue*100):.1f}%"
                })
            
            team_df = pd.DataFrame(team_data)
            st.dataframe(team_df, use_container_width=True, hide_index=True)
        
        with col6:
            st.markdown("#### 📊 Структура затрат")
            
            costs_breakdown = {
                'Команда': float(result.team_costs),
                'Накладные расходы': float(result.overhead_costs),
                'Налоги': float(result.tax_costs)
            }
            
            # Простая диаграмма затрат
            for category, amount in costs_breakdown.items():
                percentage = (amount / float(result.total_costs)) * 100 if result.total_costs > 0 else 0
                st.write(f"**{category}:** {amount:,.0f} ₽ ({percentage:.1f}%)")
        
        # Факторы риска
        if result.risk_factors:
            st.markdown("#### ⚠️ Факторы риска")
            for factor in result.risk_factors:
                st.warning(f"• {factor}")
        
        # Сравнение с рынком
        st.markdown("#### 🏆 Сравнение с рынком")
        market_data = result.market_comparison
        
        col7, col8, col9 = st.columns(3)
        
        with col7:
            st.metric(
                "Наша маржа", 
                f"{result.profit_margin:.1f}%",
                f"{market_data.get('profit_margin_diff', 0):+.1f}% к рынку"
            )
        
        with col8:
            st.metric(
                "Средняя по рынку",
                f"{market_data.get('market_avg_profit_margin', 0):.1f}%"
            )
        
        with col9:
            position = market_data.get('market_position', 'Неизвестно')
            position_emoji = {
                'Значительно выше рынка': '🚀',
                'Выше рынка': '📈',
                'На уровне рынка': '➡️',
                'Ниже рынка': '📉',
                'Значительно ниже рынка': '⬇️'
            }
            st.markdown(f"**Позиция:** {position_emoji.get(position, '❓')} {position}")
        
        # Рекомендации
        st.markdown("#### 💡 Рекомендации")
        
        if result.net_profit > 0:
            if result.profit_margin >= 20:
                st.success("🎯 **Отличный проект!** Высокая прибыльность, рекомендуем участие")
            elif result.profit_margin >= 10:
                st.info("👍 **Хороший проект.** Участие рекомендуется с учетом рисков")
            else:
                st.warning("⚠️ **Проект с низкой маржой.** Требует тщательного контроля затрат")
        else:
            st.error("❌ **Убыточный проект.** Участие не рекомендуется без пересмотра условий")
    
    def _render_analytics_page(self):
        """Страница аналитики"""
        st.header("📊 Аналитика и история расчетов")
        
        if st.session_state.economics_results:
            st.markdown("### 📈 Сохраненные расчеты")
            
            # Создаем таблицу с результатами
            analytics_data = []
            for reg_number, result in st.session_state.economics_results.items():
                analytics_data.append({
                    'Номер тендера': reg_number,
                    'Чистая прибыль (₽)': f"{result.net_profit:,.0f}",
                    'Маржа (%)': f"{result.profit_margin:.1f}",
                    'ROI (%)': f"{result.roi:.1f}",
                    'Уровень риска': result.risk_level.value.upper(),
                    'Оценка': result.get_profit_grade()
                })
            
            if analytics_data:
                df = pd.DataFrame(analytics_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                # Статистика
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    profitable_count = sum(1 for _, result in st.session_state.economics_results.items() if result.net_profit > 0)
                    st.metric("Прибыльных проектов", profitable_count)
                
                with col2:
                    avg_margin = sum(result.profit_margin for _, result in st.session_state.economics_results.items()) / len(st.session_state.economics_results)
                    st.metric("Средняя маржа", f"{avg_margin:.1f}%")
                
                with col3:
                    high_risk_count = sum(1 for _, result in st.session_state.economics_results.items() if result.risk_level.value in ['high', 'critical'])
                    st.metric("Высокорисковых", high_risk_count)
        else:
            st.info("📝 Пока нет сохраненных расчетов. Выполните анализ экономики тендеров.")
            
            # Показываем статистику поиска
            if st.session_state.search_results:
                st.markdown("### 🔍 Статистика поиска")
                
                # Анализ по типам тендеров
                type_counts = {}
                total_value = 0
                
                for tender in st.session_state.search_results:
                    tender_type = tender.get('tender_type', 'unknown')
                    price = tender.get('initial_price', 0)
                    
                    type_counts[tender_type] = type_counts.get(tender_type, 0) + 1
                    total_value += price
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Распределение по типам:**")
                    for tender_type, count in type_counts.items():
                        st.write(f"• {tender_type.upper()}: {count} тендеров")
                
                with col2:
                    st.metric("Общая стоимость", f"{total_value:,.0f} ₽")
                    st.metric("Средняя стоимость", f"{total_value/len(st.session_state.search_results):,.0f} ₽")
    
    def _render_settings_page(self):
        """Страница настроек"""
        st.header("⚙️ Настройки приложения")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔧 Параметры парсинга")
            
            st.checkbox("Режим отладки", value=self.settings.debug, disabled=True, help="Настраивается через .env файл")
            st.selectbox("Уровень логирования:", ["INFO", "DEBUG", "WARNING", "ERROR"], disabled=True)
            
            st.number_input("Таймаут запросов (сек):", value=30, disabled=True)
            st.number_input("Задержка между запросами (сек):", value=1.0, disabled=True)
            
            st.markdown("### 📊 Настройки экономики")
            
            st.number_input("Максимальная команда (чел.):", value=10, min_value=1, max_value=20, disabled=True)
            st.number_input("Максимальная длительность (мес.):", value=24, min_value=1, max_value=60, disabled=True)
        
        with col2:
            st.markdown("### 📈 Информация о системе")
            
            st.info(f"**Версия приложения:** 2.0.0")
            st.info(f"**Найдено тендеров:** {len(st.session_state.search_results)}")
            st.info(f"**Выполнено расчетов:** {len(st.session_state.economics_results)}")
            
            st.markdown("### 🔄 Управление данными")
            
            if st.button("🗑️ Очистить результаты поиска"):
                st.session_state.search_results = []
                st.session_state.selected_tenders = []
                st.success("Результаты поиска очищены")
            
            if st.button("🗑️ Очистить расчеты экономики"):
                st.session_state.economics_results = {}
                st.success("Расчеты экономики очищены")
            
            if st.button("🔄 Сбросить все данные"):
                st.session_state.search_results = []
                st.session_state.selected_tenders = []
                st.session_state.economics_results = {}
                st.session_state.last_search_query = ""
                st.success("Все данные сброшены")

# Точка входа
def main():
    try:
        app = TenderAnalyzerApp()
        app.run()
    except Exception as e:
        st.error(f"💥 Критическая ошибка приложения: {e}")
        st.info("📝 Проверьте логи и структуру проекта")
        logger.error(f"Critical app error: {e}")
        
        if st.button("🔄 Перезагрузить приложение"):
            st.rerun()

if __name__ == "__main__":
    main()