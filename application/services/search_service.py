# application/services/search_service.py - Исправленная версия для реальных данных
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
import asyncio

from domain.entities.tender import Tender, TenderStatus, TenderType
from domain.value_objects.search import SearchCriteria, SearchResult
from infrastructure.parsers.parser_interface import ParserInterface
from infrastructure.cache.cache_interface import CacheInterface
from infrastructure.database.repositories.repository_interface import TenderRepositoryInterface
from core.config import get_settings

logger = logging.getLogger(__name__)

class SearchService:
    """Сервис для поиска тендеров - ТОЛЬКО РЕАЛЬНЫЕ ДАННЫЕ"""
    
    def __init__(self, 
                 parser: ParserInterface,
                 cache: CacheInterface,
                 repository: TenderRepositoryInterface):
        self.parser = parser
        self.cache = cache
        self.repository = repository
        self.settings = get_settings()
    
    async def search_tenders(self, 
                           criteria: SearchCriteria,
                           use_cache: bool = True) -> List[SearchResult]:
        """
        Поиск тендеров по критериям - ТОЛЬКО РЕАЛЬНЫЕ ДАННЫЕ с zakupki.gov.ru
        
        Args:
            criteria: Критерии поиска
            use_cache: Использовать кеширование
            
        Returns:
            List[SearchResult]: Список результатов поиска с реального сайта
        """
        logger.info(f"🔍 Searching REAL tenders on zakupki.gov.ru: '{criteria.query}', limit: {criteria.limit}")
        
        # Проверяем кеш
        if use_cache:
            cache_key = self._get_cache_key(criteria)
            cached_results = await self.cache.get(cache_key)
            if cached_results:
                logger.info("📦 Returning cached search results")
                return cached_results
        
        try:
            # Выполняем РЕАЛЬНЫЙ поиск через HTTP парсер
            logger.info("🌐 Fetching REAL data from zakupki.gov.ru...")
            
            async with self.parser:
                raw_results = await self.parser.search_tenders(
                    query=criteria.query,
                    limit=criteria.limit,
                    filters=criteria.filters or {}
                )
            
            if not raw_results:
                logger.warning(f"⚠️ No tenders found for query: '{criteria.query}'")
                return []
            
            # Преобразуем реальные данные в SearchResult объекты
            search_results = []
            for raw_result in raw_results:
                try:
                    search_result = SearchResult(
                        reg_number=raw_result.get('reg_number', ''),
                        title=raw_result.get('title', 'Без названия'),
                        customer=raw_result.get('customer', 'Заказчик не указан'),
                        price=str(raw_result.get('initial_price', 0)),
                        tender_type=raw_result.get('tender_type', 'unknown'),
                        status=raw_result.get('status', 'active'),
                        deadline=raw_result.get('deadline'),
                        source_url=raw_result.get('source_url', ''),
                        parsed_at=datetime.now()
                    )
                    search_results.append(search_result)
                    logger.debug(f"✅ Processed tender: {search_result.reg_number}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing tender result: {e}")
                    continue
            
            # Сохраняем в кеш только реальные результаты
            if use_cache and search_results:
                await self.cache.set(
                    cache_key, 
                    search_results, 
                    ttl=self.settings.cache.search_results_ttl
                )
                logger.info(f"💾 Cached {len(search_results)} real search results")
            
            logger.info(f"✅ Found {len(search_results)} REAL tenders from zakupki.gov.ru")
            return search_results
            
        except Exception as e:
            logger.error(f"❌ Error searching REAL tenders: {str(e)}")
            raise Exception(f"Не удалось получить данные с zakupki.gov.ru: {str(e)}")
    
    async def get_tender_details(self, 
                               reg_number: str,
                               force_refresh: bool = False) -> Optional[Tender]:
        """
        Получить РЕАЛЬНУЮ детальную информацию о тендере с zakupki.gov.ru
        
        Args:
            reg_number: Номер тендера
            force_refresh: Принудительно обновить данные
            
        Returns:
            Optional[Tender]: Детальная информация о тендере с реального сайта
        """
        logger.info(f"📋 Getting REAL tender details for: {reg_number}")
        
        # Проверяем базу данных
        if not force_refresh:
            tender = await self.repository.get_by_reg_number(reg_number)
            if tender and self._is_tender_fresh(tender):
                logger.info("📦 Returning tender from database")
                return tender
        
        try:
            # Получаем РЕАЛЬНЫЕ данные через парсер
            logger.info(f"🌐 Fetching REAL tender details from zakupki.gov.ru...")
            
            async with self.parser:
                tender_data = await self.parser.parse_tender_details(reg_number)
            
            if tender_data:
                # Создаем объект Tender из РЕАЛЬНЫХ данных
                tender = self._create_tender_from_real_data(tender_data)
                
                # Сохраняем в базу данных
                await self.repository.save(tender)
                
                logger.info(f"✅ REAL tender details loaded and saved: {reg_number}")
                return tender
            else:
                logger.warning(f"⚠️ No REAL data found for tender: {reg_number}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error getting REAL tender details: {str(e)}")
            raise Exception(f"Не удалось получить детали тендера с zakupki.gov.ru: {str(e)}")
    
    async def search_with_auto_retry(self, 
                                   criteria: SearchCriteria,
                                   max_attempts: int = 3) -> List[SearchResult]:
        """
        Поиск с автоматическими повторными попытками для обеспечения получения реальных данных
        """
        for attempt in range(max_attempts):
            try:
                logger.info(f"🔄 Search attempt {attempt + 1}/{max_attempts}")
                
                results = await self.search_tenders(criteria)
                
                if results:
                    logger.info(f"✅ Successfully got {len(results)} REAL results on attempt {attempt + 1}")
                    return results
                else:
                    logger.warning(f"⚠️ No results on attempt {attempt + 1}")
                    
                # Задержка между попытками
                if attempt < max_attempts - 1:
                    delay = (attempt + 1) * 2  # 2, 4, 6 секунд
                    logger.info(f"⏱️ Waiting {delay} seconds before retry...")
                    await asyncio.sleep(delay)
                    
            except Exception as e:
                logger.error(f"❌ Search attempt {attempt + 1} failed: {str(e)}")
                
                if attempt == max_attempts - 1:
                    raise Exception(f"Не удалось получить данные после {max_attempts} попыток: {str(e)}")
                
                # Задержка перед повторной попыткой
                delay = (attempt + 1) * 3
                logger.info(f"⏱️ Waiting {delay} seconds before retry...")
                await asyncio.sleep(delay)
        
        return []
    
    async def get_search_statistics(self, criteria: SearchCriteria) -> Dict[str, Any]:
        """Получить статистику по результатам поиска реальных данных"""
        try:
            results = await self.search_tenders(criteria, use_cache=True)
            
            if not results:
                return {
                    'total_count': 0,
                    'message': 'Тендеры не найдены'
                }
            
            # Анализируем реальные данные
            type_counts = {}
            status_counts = {}
            total_value = 0
            price_range = {'min': float('inf'), 'max': 0}
            
            for result in results:
                # Подсчет по типам
                tender_type = result.tender_type
                type_counts[tender_type] = type_counts.get(tender_type, 0) + 1
                
                # Подсчет по статусам
                status = result.status
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Финансовая статистика
                try:
                    price = float(result.price.replace(',', '').replace(' ', '') if result.price else 0)
                    total_value += price
                    price_range['min'] = min(price_range['min'], price)
                    price_range['max'] = max(price_range['max'], price)
                except (ValueError, AttributeError):
                    pass
            
            avg_value = total_value / len(results) if results else 0
            
            return {
                'total_count': len(results),
                'type_distribution': type_counts,
                'status_distribution': status_counts,
                'financial_stats': {
                    'total_value': total_value,
                    'average_value': avg_value,
                    'min_value': price_range['min'] if price_range['min'] != float('inf') else 0,
                    'max_value': price_range['max']
                },
                'data_source': 'zakupki.gov.ru (REAL DATA)',
                'search_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting search statistics: {e}")
            return {
                'total_count': 0,
                'error': str(e),
                'message': 'Ошибка получения статистики'
            }
    
    def _get_cache_key(self, criteria: SearchCriteria) -> str:
        """Создать ключ для кеширования"""
        import hashlib
        
        key_data = f"REAL:{criteria.query}_{criteria.limit}_{str(sorted(criteria.filters.items()) if criteria.filters else [])}"
        return f"real_search:{hashlib.md5(key_data.encode()).hexdigest()}"
    
    def _is_tender_fresh(self, tender: Tender) -> bool:
        """Проверить, актуальны ли данные тендера (для реальных данных - 30 минут)"""
        return (datetime.now() - tender.updated_at) < timedelta(minutes=30)
    
    def _create_tender_from_real_data(self, data: Dict[str, Any]) -> Tender:
        """Создать объект Tender из РЕАЛЬНЫХ данных парсера"""
        from decimal import Decimal
        
        tender = Tender(
            reg_number=data.get('reg_number', ''),
            title=data.get('title', ''),
            customer=data.get('customer', ''),
            initial_price=Decimal(str(data.get('initial_price', 0))),
            status=self._map_real_status(data.get('status', 'active')),
            tender_type=self._map_real_tender_type(data.get('tender_type', 'unknown')),
            description=data.get('description', ''),
            procurement_method=data.get('procurement_method'),
            application_deadline=data.get('deadline'),
            contract_execution_deadline=data.get('contract_execution_deadline'),
            winner_price=Decimal(str(data.get('winner_price', 0))) if data.get('winner_price') else None,
            participant_requirements=data.get('participant_requirements', {}),
            application_security=Decimal(str(data.get('application_security', 0))) if data.get('application_security') else None,
            contract_security=Decimal(str(data.get('contract_security', 0))) if data.get('contract_security') else None,
            source_url=data.get('source_url', ''),
            parsed_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Добавляем документы из реальных данных
        documents_data = data.get('documents', [])
        for doc_data in documents_data:
            from domain.entities.tender import TenderDocument
            document = TenderDocument(
                name=doc_data.get('name', ''),
                url=doc_data.get('url', ''),
                file_size=doc_data.get('file_size'),
                file_type=doc_data.get('file_type')
            )
            tender.add_document(document)
        
        # Добавляем участников из реальных данных
        participants_data = data.get('participants', [])
        for part_data in participants_data:
            from domain.entities.tender import TenderParticipant
            participant = TenderParticipant(
                name=part_data.get('name', ''),
                inn=part_data.get('inn'),
                kpp=part_data.get('kpp'),
                address=part_data.get('address'),
                is_winner=part_data.get('is_winner', False)
            )
            tender.add_participant(participant)
        
        return tender
    
    def _map_real_status(self, status_str: str) -> TenderStatus:
        """Маппинг реального статуса с сайта в enum"""
        status_mapping = {
            'active': TenderStatus.ACTIVE,
            'completed': TenderStatus.COMPLETED,
            'cancelled': TenderStatus.CANCELLED,
            'draft': TenderStatus.DRAFT
        }
        return status_mapping.get(status_str.lower(), TenderStatus.ACTIVE)
    
    def _map_real_tender_type(self, type_str: str) -> TenderType:
        """Маппинг реального типа тендера с сайта в enum"""
        type_mapping = {
            '44-fz': TenderType.FZ_44,
            '223-fz': TenderType.FZ_223,
            'commercial': TenderType.COMMERCIAL
        }
        return type_mapping.get(type_str.lower(), TenderType.FZ_44)