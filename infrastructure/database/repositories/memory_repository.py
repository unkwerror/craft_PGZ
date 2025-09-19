# infrastructure/database/repositories/memory_repository.py (заглушка)
from typing import List, Optional, Dict
from domain.entities.tender import Tender

class MemoryTenderRepository:
    """In-memory репозиторий для начальной разработки"""
    
    def __init__(self):
        self._tenders: Dict[str, Tender] = {}
    
    async def save(self, tender: Tender) -> None:
        """Сохранить тендер"""
        self._tenders[tender.reg_number] = tender
    
    async def get_by_id(self, tender_id: str) -> Optional[Tender]:
        """Получить тендер по ID"""
        return self._tenders.get(tender_id)
    
    async def get_by_reg_number(self, reg_number: str) -> Optional[Tender]:
        """Получить тендер по номеру"""
        return self._tenders.get(reg_number)
    
    async def get_all(self, limit: int = 100) -> List[Tender]:
        """Получить все тендеры"""
        return list(self._tenders.values())[:limit]
    
    async def delete(self, tender_id: str) -> None:
        """Удалить тендер"""
        self._tenders.pop(tender_id, None)
