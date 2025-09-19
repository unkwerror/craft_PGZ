# infrastructure/parsers/http_parser.py - ПОЛНАЯ версия для реальных данных
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
from datetime import datetime
from decimal import Decimal
import re
from urllib.parse import urljoin, urlparse, quote
from tenacity import retry, stop_after_attempt, wait_exponential
from infrastructure.parsers.parser_interface import ParserInterface
from core.config import get_settings
from typing import Optional, Dict, Any, List

logger = logging.getLogger(__name__)

class HttpTenderParser(ParserInterface):
    """HTTP-парсер для zakupki.gov.ru - ТОЛЬКО РЕАЛЬНЫЕ ДАННЫЕ"""
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = "https://zakupki.gov.ru"
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Заголовки как у реального браузера
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
    
    async def __aenter__(self):
        """Создание HTTP-сессии"""
        timeout = aiohttp.ClientTimeout(total=45, connect=10)
        connector = aiohttp.TCPConnector(
            limit=5,
            limit_per_host=3,
            ttl_dns_cache=300,
            use_dns_cache=True,
            ssl=False  # zakupki.gov.ru может иметь проблемы с SSL сертификатами
        )
        
        self.session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=timeout,
            connector=connector,
            cookie_jar=aiohttp.CookieJar()  # Сохраняем cookies для сессии
        )
        
        logger.info("🌐 HTTP session created for zakupki.gov.ru")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            logger.info("🔒 HTTP session closed")
    
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=20))
    async def search_tenders(self,
                           query: str,
                           limit: int = 10,
                           filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        РЕАЛЬНЫЙ поиск тендеров на zakupki.gov.ru
        """
        logger.info(f"🔍 REAL SEARCH on zakupki.gov.ru: '{query}', limit={limit}")
        
        if not self.session:
            raise RuntimeError("Session not initialized. Use 'async with' context manager.")
        
        # Сначала идем на главную страницу для получения cookies
        await self._initialize_session()
        
        try:
            # Точный URL страницы поиска zakupki.gov.ru
            search_url = f"{self.base_url}/epz/order/extendedsearch/results.html"
            
            # РЕАЛЬНЫЕ параметры поиска для zakupki.gov.ru (проверенные в 2025)
            params = {
                'morphology': 'on',
                'search-filter': 'Дате размещения',
                'pageNumber': 1,
                'sortDirection': 'false',
                'recordsPerPage': f'_{min(limit, 50)}',  # _10, _20, _50
                'showLotsInfoHidden': 'false',
                'sortBy': 'UPDATE_DATE',
                'fz44': 'on',        # 44-ФЗ
                'fz223': 'on',       # 223-ФЗ
                'af': 'on',          # Другие федеральные законы
                'ca': 'on',          # Конкурсы с ограниченным участием
                'placingWay0': 'on', # Способы размещения
                'currencyIdGeneral': -1,
                'searchString': query.strip()
            }
            
            # Добавляем фильтры если есть
            if filters:
                params.update(self._prepare_real_filters(filters))
            
            logger.info(f"🌐 Making REAL request to: {search_url}")
            logger.debug(f"📝 Search params: {params}")
            
            # Выполняем РЕАЛЬНЫЙ запрос
            async with self.session.get(search_url, params=params, allow_redirects=True) as response:
                
                logger.info(f"📡 Response status: {response.status}")
                logger.info(f"📍 Final URL: {response.url}")
                
                if response.status == 200:
                    html = await response.text()
                    logger.info(f"📄 Received HTML: {len(html)} characters")
                    
                    # Парсим РЕАЛЬНЫЕ результаты
                    results = self._parse_real_search_results(html)
                    
                    if results:
                        logger.info(f"✅ Successfully parsed {len(results)} REAL tenders")
                        
                        # Получаем детали для каждого найденного тендера
                        enhanced_results = []
                        for result in results[:limit]:
                            try:
                                # Добавляем задержку между запросами
                                await asyncio.sleep(0.5)
                                
                                # Пытаемся получить дополнительные детали
                                enhanced_result = await self._enhance_tender_data(result)
                                enhanced_results.append(enhanced_result or result)
                                
                            except Exception as e:
                                logger.warning(f"⚠️ Could not enhance tender {result.get('reg_number')}: {e}")
                                enhanced_results.append(result)
                        
                        logger.info(f"🎯 Returning {len(enhanced_results)} REAL tenders")
                        return enhanced_results
                    else:
                        logger.warning(f"❌ No tenders found for query: '{query}'")
                        
                        # Проверяем, не заблокировали ли нас
                        if "капча" in html.lower() or "captcha" in html.lower():
                            logger.error("🚫 CAPTCHA detected - need to handle")
                            raise Exception("Сайт запросил капчу. Попробуйте позже.")
                        
                        return []
                        
                elif response.status == 403:
                    logger.error("🚫 Access forbidden (403) - possible blocking")
                    raise Exception("Доступ к сайту заблокирован. Попробуйте позже.")
                    
                elif response.status == 429:
                    logger.error("⏰ Too many requests (429) - rate limited")
                    raise Exception("Слишком много запросов. Попробуйте позже.")
                    
                else:
                    logger.error(f"❌ Request failed with status: {response.status}")
                    error_text = await response.text()
                    logger.debug(f"Error response: {error_text[:500]}...")
                    raise Exception(f"Ошибка сайта: HTTP {response.status}")
            
        except Exception as e:
            logger.error(f"❌ Error in REAL search: {str(e)}")
            raise
    
    async def _initialize_session(self):
        """Инициализация сессии - получаем cookies с главной страницы"""
        try:
            logger.info("🔄 Initializing session with zakupki.gov.ru")
            
            async with self.session.get(f"{self.base_url}/epz/main/public/home.html") as response:
                if response.status == 200:
                    logger.info("✅ Session initialized successfully")
                    await asyncio.sleep(1)  # Даем время на обработку cookies
                else:
                    logger.warning(f"⚠️ Session initialization returned: {response.status}")
                    
        except Exception as e:
            logger.warning(f"⚠️ Session initialization failed: {e}")
    
    def _parse_real_search_results(self, html: str) -> List[Dict[str, Any]]:
        """Парсинг РЕАЛЬНЫХ результатов поиска с zakupki.gov.ru"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        logger.debug("🔍 Parsing REAL HTML from zakupki.gov.ru")
        
        # Ищем основной контейнер с результатами
        containers_to_try = [
            {'id': 'searchResultPlaceHolder'},  # Основной контейнер
            {'class': 'search-results'},
            {'class': 'registry-entry-list'}
        ]
        
        results_container = None
        for container_selector in containers_to_try:
            results_container = soup.find('div', container_selector)
            if results_container:
                logger.debug(f"✅ Found results container: {container_selector}")
                break
        
        if not results_container:
            logger.warning("❌ Results container not found in HTML")
            # Сохраняем HTML для отладки
            with open('debug_search_results.html', 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info("💾 Saved HTML to debug_search_results.html for analysis")
            return []
        
        # Ищем карточки тендеров (актуальные селекторы для 2025)
        selectors_to_try = [
            'div.row.no-gutters.registry-entry__form',  # Новый формат
            'div.search-registry-entry-block',          # Старый формат
            'div.registry-entry',                       # Запасной формат
            'div[class*="registry-entry"]'              # Любые registry-entry
        ]
        
        tender_cards = []
        for selector in selectors_to_try:
            tender_cards = results_container.select(selector)
            if tender_cards:
                logger.debug(f"✅ Found {len(tender_cards)} tender cards with selector: {selector}")
                break
        
        if not tender_cards:
            logger.warning("❌ No tender cards found")
            return []
        
        logger.info(f"🎯 Processing {len(tender_cards)} REAL tender cards")
        
        # Парсим каждую карточку
        for i, card in enumerate(tender_cards):
            try:
                result = self._parse_real_tender_card(card)
                if result:
                    results.append(result)
                    logger.debug(f"✅ Parsed tender {i+1}: {result.get('reg_number', 'N/A')}")
                else:
                    logger.debug(f"⚠️ Failed to parse tender card {i+1}")
                    
            except Exception as e:
                logger.error(f"❌ Error parsing tender card {i+1}: {str(e)}")
                continue
        
        logger.info(f"✅ Successfully parsed {len(results)} REAL tenders")
        return results
    
    def _parse_real_tender_card(self, card) -> Optional[Dict[str, Any]]:
        """Парсинг одной РЕАЛЬНОЙ карточки тендера"""
        try:
            data = {}
            
            # 1. Номер тендера - КРИТИЧЕСКИ ВАЖНО
            reg_number = self._extract_real_reg_number(card)
            if not reg_number:
                logger.debug("❌ No registration number found")
                return None
            
            data['reg_number'] = reg_number
            
            # 2. Заголовок (название тендера)
            title = self._extract_real_title(card)
            data['title'] = title or f'Тендер № {reg_number}'
            
            # 3. Заказчик
            customer = self._extract_real_customer(card)
            data['customer'] = customer or 'Заказчик не указан'
            
            # 4. Цена
            price = self._extract_real_price(card)
            data['initial_price'] = price
            
            # 5. URL на детальную страницу
            source_url = self._extract_real_url(card, reg_number)
            data['source_url'] = source_url
            
            # 6. Тип тендера (44-ФЗ, 223-ФЗ и т.д.)
            tender_type = self._determine_real_tender_type(card)
            data['tender_type'] = tender_type
            
            # 7. Статус
            status = self._determine_real_status(card)
            data['status'] = status
            
            # 8. Дедлайн подачи заявок
            deadline = self._extract_real_deadline(card)
            data['deadline'] = deadline
            
            # 9. Дополнительные поля
            data['parsed_at'] = datetime.now()
            data['data_source'] = 'zakupki.gov.ru'
            
            logger.debug(f"✅ Successfully parsed: {reg_number} - {title[:50]}...")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error parsing real tender card: {str(e)}")
            return None
    
    def _extract_real_reg_number(self, card) -> Optional[str]:
        """Извлечение РЕАЛЬНОГО номера тендера"""
        selectors = [
            '.registry-entry__header-mid__number',
            '.registry-entry__body-number',
            'span[class*="number"]',
            'div[class*="number"]',
            '[data-number]',
            '.number'
        ]
        
        for selector in selectors:
            elem = card.select_one(selector)
            if elem:
                # Пробуем атрибут data-number
                reg_number = elem.get('data-number', '').strip()
                if reg_number:
                    return reg_number
                
                # Пробуем текст элемента
                text = elem.get_text(strip=True)
                if text:
                    # Убираем лишние символы
                    reg_number = re.sub(r'[№#\s]', '', text)
                    if re.match(r'\d{19,}', reg_number):  # Номера тендеров обычно длинные
                        return reg_number
        
        # Ищем номер в любом тексте карточки
        full_text = card.get_text()
        reg_match = re.search(r'№?\s*(\d{19,})', full_text)
        if reg_match:
            return reg_match.group(1)
        
        return None
    
    def _extract_real_title(self, card) -> Optional[str]:
        """Извлечение РЕАЛЬНОГО названия тендера"""
        selectors = [
            '.registry-entry__body-value a',
            '.registry-entry__body-value',
            'a[href*="common-info"]',
            'a[title]',
            '.registry-entry__body .d-block',
            '.entry-title',
            'h3 a',
            'h4 a'
        ]
        
        for selector in selectors:
            elem = card.select_one(selector)
            if elem:
                # Сначала атрибут title
                title = elem.get('title', '').strip()
                if title and len(title) > 10:
                    return self._clean_title(title)
                
                # Затем текст элемента
                text = elem.get_text(strip=True)
                if text and len(text) > 10:
                    return self._clean_title(text)
        
        return None
    
    def _extract_real_customer(self, card) -> Optional[str]:
        """Извлечение РЕАЛЬНОГО заказчика"""
        selectors = [
            '.registry-entry__body-href',
            '.purchaser',
            'a[href*="purchaser"]',
            '.customer',
            '.registry-entry__body .text-truncate',
            '.organization'
        ]
        
        for selector in selectors:
            elem = card.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                if text and len(text) > 3:
                    return self._clean_customer_name(text)
        
        return None
    
    def _extract_real_price(self, card) -> float:
        """Извлечение РЕАЛЬНОЙ цены"""
        selectors = [
            '.price-block__value',
            '.cost .currency',
            '.price',
            'span[class*="price"]',
            '.amount'
        ]
        
        for selector in selectors:
            elem = card.select_one(selector)
            if elem:
                price_text = elem.get_text(strip=True)
                price = self._parse_real_price(price_text)
                if price > 0:
                    return price
        
        # Поиск цены в любом тексте
        full_text = card.get_text()
        price_matches = re.findall(r'(?:цена|стоимость|сумма).*?(\d[\d\s,]*(?:\.\d+)?)', full_text.lower())
        
        for match in price_matches:
            price = self._parse_real_price(match)
            if price > 1000:  # Минимальная разумная цена
                return price
        
        return 0.0
    
    def _extract_real_url(self, card, reg_number: str) -> str:
        """Создание РЕАЛЬНОЙ ссылки на тендер"""
        # Ищем прямую ссылку
        selectors = [
            'a[href*="common-info"]',
            'a[href*="view"]',
            '.registry-entry__body-value a'
        ]
        
        for selector in selectors:
            elem = card.select_one(selector)
            if elem and elem.get('href'):
                relative_url = elem['href']
                return urljoin(self.base_url, relative_url)
        
        # Создаем ссылку по шаблону, если прямая ссылка не найдена
        if reg_number:
            # Пробуем разные типы URL для разных типов тендеров
            url_templates = [
                f"{self.base_url}/epz/order/notice/ea44/view/common-info.html?regNumber={reg_number}",
                f"{self.base_url}/epz/order/notice/ok44/view/common-info.html?regNumber={reg_number}",
                f"{self.base_url}/epz/order/notice/oa44/view/common-info.html?regNumber={reg_number}",
                f"{self.base_url}/epz/order/notice/ok504/view/common-info.html?regNumber={reg_number}"
            ]
            return url_templates[0]  # Возвращаем первый шаблон
        
        return f"{self.base_url}/epz/order/extendedsearch/results.html"
    
    def _determine_real_tender_type(self, card) -> str:
        """Определение РЕАЛЬНОГО типа тендера"""
        text = card.get_text().upper()
        
        if '44-ФЗ' in text or '44-FZ' in text:
            return '44-fz'
        elif '223-ФЗ' in text or '223-FZ' in text:
            return '223-fz'
        elif 'КОММЕРЧЕСК' in text:
            return 'commercial'
        else:
            return 'unknown'
    
    def _determine_real_status(self, card) -> str:
        """Определение РЕАЛЬНОГО статуса тендера"""
        text = card.get_text().lower()
        
        if any(word in text for word in ['завершен', 'completed', 'окончен']):
            return 'completed'
        elif any(word in text for word in ['отменен', 'cancelled', 'аннулирован']):
            return 'cancelled'
        elif any(word in text for word in ['черновик', 'draft', 'проект']):
            return 'draft'
        else:
            return 'active'
    
    def _extract_real_deadline(self, card) -> Optional[datetime]:
        """Извлечение РЕАЛЬНОГО дедлайна"""
        selectors = [
            '.deadline',
            '.date',
            '.data-block__value',
            '[class*="date"]'
        ]
        
        for selector in selectors:
            elem = card.select_one(selector)
            if elem:
                date_text = elem.get_text(strip=True)
                deadline = self._parse_real_date(date_text)
                if deadline:
                    return deadline
        
        # Ищем дату в любом тексте
        full_text = card.get_text()
        date_patterns = [
            r'до\s+(\d{1,2}\.\d{1,2}\.\d{4})\s*(\d{1,2}:\d{2})?',
            r'(\d{1,2}\.\d{1,2}\.\d{4})\s+(\d{1,2}:\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4})\s+(\d{1,2}:\d{2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, full_text)
            if match:
                try:
                    date_str = match.group(1)
                    time_str = match.group(2) if match.lastindex > 1 else '23:59'
                    
                    if '.' in date_str:
                        return datetime.strptime(f"{date_str} {time_str}", '%d.%m.%Y %H:%M')
                    else:
                        return datetime.strptime(f"{date_str} {time_str}", '%d/%m/%Y %H:%M')
                except ValueError:
                    continue
        
        return None
    
    async def _enhance_tender_data(self, basic_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Получение дополнительных РЕАЛЬНЫХ данных о тендере"""
        try:
            reg_number = basic_data.get('reg_number')
            if not reg_number:
                return basic_data
            
            detailed_data = await self.parse_tender_details(reg_number)
            
            if detailed_data:
                # Объединяем базовые и детальные данные
                enhanced = basic_data.copy()
                enhanced.update(detailed_data)
                return enhanced
            
            return basic_data
            
        except Exception as e:
            logger.debug(f"Could not enhance data for {basic_data.get('reg_number')}: {e}")
            return basic_data
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
    async def parse_tender_details(self, reg_number: str) -> Optional[Dict[str, Any]]:
        """
        Получение РЕАЛЬНОЙ детальной информации о тендере
        """
        logger.info(f"📋 Getting REAL tender details for: {reg_number}")
        
        if not self.session:
            raise RuntimeError("Session not initialized")
        
        try:
            # Различные URL шаблоны для разных типов тендеров
            url_templates = [
                f"{self.base_url}/epz/order/notice/ea44/view/common-info.html",
                f"{self.base_url}/epz/order/notice/ok44/view/common-info.html",
                f"{self.base_url}/epz/order/notice/oa44/view/common-info.html",
                f"{self.base_url}/epz/order/notice/ok504/view/common-info.html"
            ]
            
            for tender_url in url_templates:
                params = {'regNumber': reg_number}
                
                async with self.session.get(tender_url, params=params) as response:
                    if response.status == 200:
                        html = await response.text()
                        
                        # Проверяем, что это реальная страница тендера
                        if reg_number in html and 'общие сведения' in html.lower():
                            data = self._parse_real_tender_details(html, reg_number)
                            if data:
                                logger.info(f"✅ REAL details loaded for {reg_number}")
                                return data
                    
                    elif response.status == 404:
                        logger.debug(f"📍 URL {tender_url} returned 404 for {reg_number}")
                        continue
                    else:
                        logger.debug(f"📍 URL {tender_url} returned {response.status}")
            
            logger.warning(f"⚠️ Could not fetch REAL details for {reg_number}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Error parsing REAL tender details: {str(e)}")
            return None
    
    def _parse_real_tender_details(self, html: str, reg_number: str) -> Optional[Dict[str, Any]]:
        """Парсинг РЕАЛЬНОЙ детальной страницы тендера"""
        soup = BeautifulSoup(html, 'html.parser')
        
        try:
            data = {'reg_number': reg_number}
            
            # Название
            title_selectors = [
                'span.cardMainInfo__title',
                '.cardMainInfo__title',
                'h1.orgName',
                'h1',
                '.noticeTabBox .active'
            ]
            
            for selector in title_selectors:
                elem = soup.select_one(selector)
                if elem:
                    data['title'] = self._clean_title(elem.get_text(strip=True))
                    break
            
            # Заказчик
            customer_selectors = [
                'span.cardMainInfo__purchaser',
                '.cardMainInfo__purchaser',
                '.purchaser a',
                '.orgName a'
            ]
            
            for selector in customer_selectors:
                elem = soup.select_one(selector)
                if elem:
                    data['customer'] = self._clean_customer_name(elem.get_text(strip=True))
                    break
            
            # Цена
            price_selectors = [
                'span.cardMainInfo__price',
                '.cardMainInfo__price',
                '.cost .currency'
            ]
            
            for selector in price_selectors:
                elem = soup.select_one(selector)
                if elem:
                    price_text = elem.get_text(strip=True)
                    data['initial_price'] = self._parse_real_price(price_text)
                    break
            
            # Описание
            desc_selectors = [
                '.noticeTabBox .tabContent',
                '.description',
                '.purchaseObjectInfo'
            ]
            
            for selector in desc_selectors:
                elem = soup.select_one(selector)
                if elem:
                    desc_text = elem.get_text(strip=True)
                    if len(desc_text) > 50:  # Только содержательные описания
                        data['description'] = desc_text[:2000]  # Ограничиваем длину
                        break
            
            logger.debug(f"✅ Parsed REAL details for: {reg_number}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Error parsing REAL tender details HTML: {str(e)}")
            return None
    
    # Вспомогательные методы для очистки данных
    
    def _clean_title(self, title: str) -> str:
        """Очистка названия тендера"""
        if not title:
            return ''
        
        # Убираем лишние пробелы и символы
        cleaned = re.sub(r'\s+', ' ', title.strip())
        
        # Убираем HTML теги если остались
        cleaned = re.sub(r'<[^>]+>', '', cleaned)
        
        return cleaned[:500]  # Ограничиваем длину
    
    def _clean_customer_name(self, customer: str) -> str:
        """Очистка названия заказчика"""
        if not customer:
            return ''
        
        # Убираем лишние пробелы
        cleaned = re.sub(r'\s+', ' ', customer.strip())
        
        # Убираем типичные префиксы
        prefixes_to_remove = [
            'заказчик:', 'организация:', 'покупатель:',
            'customer:', 'organization:'
        ]
        
        for prefix in prefixes_to_remove:
            if cleaned.lower().startswith(prefix):
                cleaned = cleaned[len(prefix):].strip()
        
        return cleaned[:300]  # Ограничиваем длину
    
    def _parse_real_price(self, price_text: str) -> float:
        """Парсинг РЕАЛЬНОЙ цены из текста"""
        if not price_text:
            return 0.0
        
        # Удаляем все кроме цифр, пробелов, запятых и точек
        clean_text = re.sub(r'[^\d\s,.]', '', price_text)
        
        # Заменяем запятые на точки и убираем пробелы
        clean_text = clean_text.replace(',', '.').replace(' ', '')
        
        # Находим все числа
        numbers = re.findall(r'\d+(?:\.\d+)?', clean_text)
        
        if numbers:
            try:
                # Берем самое большое число (скорее всего цена)
                prices = [float(num) for num in numbers]
                max_price = max(prices)
                
                # Проверяем разумность цены
                if max_price > 1000000000:  # Больше 1 млрд - возможно ошибка в копейках
                    max_price = max_price / 100
                
                return max_price
                
            except (ValueError, TypeError):
                return 0.0
        
        return 0.0
    
    def _parse_real_date(self, date_text: str) -> Optional[datetime]:
        """Парсинг РЕАЛЬНОЙ даты из текста"""
        if not date_text:
            return None
        
        # Различные форматы дат
        date_patterns = [
            (r'(\d{1,2})\.(\d{1,2})\.(\d{4})\s+(\d{1,2}):(\d{2})', '%d.%m.%Y %H:%M'),
            (r'(\d{1,2})\.(\d{1,2})\.(\d{4})', '%d.%m.%Y'),
            (r'(\d{1,2})/(\d{1,2})/(\d{4})\s+(\d{1,2}):(\d{2})', '%d/%m/%Y %H:%M'),
            (r'(\d{1,2})/(\d{1,2})/(\d{4})', '%d/%m/%Y'),
            (r'(\d{4})-(\d{1,2})-(\d{1,2})\s+(\d{1,2}):(\d{2})', '%Y-%m-%d %H:%M'),
            (r'(\d{4})-(\d{1,2})-(\d{1,2})', '%Y-%m-%d')
        ]
        
        for pattern, format_str in date_patterns:
            match = re.search(pattern, date_text)
            if match:
                try:
                    if len(match.groups()) == 5:  # С временем
                        date_str = f"{match.group(1)}.{match.group(2)}.{match.group(3)} {match.group(4)}:{match.group(5)}"
                        return datetime.strptime(date_str, format_str)
                    else:  # Только дата
                        date_str = f"{match.group(1)}.{match.group(2)}.{match.group(3)}"
                        return datetime.strptime(date_str, format_str.split()[0])
                        
                except ValueError:
                    continue
        
        return None
    
    def _prepare_real_filters(self, filters: Dict[str, Any]) -> Dict[str, str]:
        """Подготовка РЕАЛЬНЫХ фильтров для zakupki.gov.ru"""
        params = {}
        
        if 'price_from' in filters and filters['price_from']:
            params['priceFromGeneral'] = str(filters['price_from'])
        
        if 'price_to' in filters and filters['price_to']:
            params['priceToGeneral'] = str(filters['price_to'])
        
        if 'date_from' in filters and filters['date_from']:
            params['publishDateFrom'] = str(filters['date_from'])
        
        if 'date_to' in filters and filters['date_to']:
            params['publishDateTo'] = str(filters['date_to'])
        
        # Дополнительные фильтры специфичные для zakupki.gov.ru
        if 'region' in filters and filters['region']:
            params['selectedSubjectsIdNameHidden'] = str(filters['region'])
        
        return params