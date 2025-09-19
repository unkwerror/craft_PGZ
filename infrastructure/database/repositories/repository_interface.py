# infrastructure/database/repositories/repository_interface.py
from abc import ABC, abstractmethod
from typing import List, Optional
from domain.entities.tender import Tender

class TenderRepositoryInterface(ABC):
    """Интерфейс репозитория для тендеров"""
    
    @abstractmethod
    async def save(self, tender: Tender) -> None:
        """Сохранить тендер"""
        pass
    
    @abstractmethod
    async def get_by_id(self, tender_id: str) -> Optional[Tender]:
        """Получить тендер по ID"""
        pass
    
    @abstractmethod
    async def get_by_reg_number(self, reg_number: str) -> Optional[Tender]:
        """Получить тендер по номеру"""
        pass
    
    @abstractmethod
    async def get_all(self, limit: int = 100) -> List[Tender]:
        """Получить все тендеры"""
        pass
    
    @abstractmethod
    async def delete(self, tender_id: str) -> None:
        """Удалить тендер"""
        pass