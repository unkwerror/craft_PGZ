# infrastructure/parsers/parser_interface.py
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any

class ParserInterface(ABC):
    """Интерфейс для парсеров тендеров"""
    
    @abstractmethod
    async def search_tenders(self, 
                           query: str, 
                           limit: int = 20,
                           filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Поиск тендеров по запросу
        
        Args:
            query: Поисковый запрос
            limit: Максимальное количество результатов
            filters: Дополнительные фильтры
            
        Returns:
            List[Dict]: Список найденных тендеров
        """
        pass
    
    @abstractmethod
    async def parse_tender_details(self, reg_number: str) -> Optional[Dict[str, Any]]:
        """
        Получить детальную информацию о тендере
        
        Args:
            reg_number: Номер тендера
            
        Returns:
            Optional[Dict]: Детальная информация о тендере
        """
        pass