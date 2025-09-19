# infrastructure/cache/simple_cache.py (заглушка для начала)
import asyncio
from typing import Any, Optional, Dict
from datetime import datetime, timedelta

class SimpleCache:
    """Простой in-memory кеш для начальной разработки"""
    
    def __init__(self):
        self._cache: Dict[str, tuple[Any, datetime]] = {}
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кеша"""
        if key in self._cache:
            value, expiry = self._cache[key]
            if datetime.now() < expiry:
                return value
            else:
                # Удаляем устаревшее значение
                del self._cache[key]
        return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> None:
        """Сохранить значение в кеш"""
        expiry = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = (value, expiry)
    
    async def delete(self, key: str) -> None:
        """Удалить значение из кеша"""
        self._cache.pop(key, None)
    
    async def clear(self) -> None:
        """Очистить весь кеш"""
        self._cache.clear()
