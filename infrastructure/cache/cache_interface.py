# infrastructure/cache/cache_interface.py
from abc import ABC, abstractmethod
from typing import Any, Optional

class CacheInterface(ABC):
    """Интерфейс для кеширования"""
    
    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кеша"""
        pass
    
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Сохранить значение в кеш"""
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> None:
        """Удалить значение из кеша"""
        pass
    
    @abstractmethod
    async def clear(self) -> None:
        """Очистить весь кеш"""
        pass