# domain/value_objects/search.py
from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime

@dataclass
class SearchCriteria:
    """Критерии поиска тендеров"""
    query: str
    limit: int = 20
    filters: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.limit <= 0:
            raise ValueError("Limit must be positive")
        if not self.query.strip():
            raise ValueError("Query cannot be empty")

@dataclass
class SearchResult:
    """Результат поиска одного тендера"""
    reg_number: str
    title: str
    customer: str
    price: str
    tender_type: str
    status: str = "active"
    deadline: Optional[datetime] = None
    source_url: str = ""
    parsed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь"""
        return {
            'reg_number': self.reg_number,
            'title': self.title,
            'customer': self.customer,
            'price': self.price,
            'tender_type': self.tender_type,
            'status': self.status,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'source_url': self.source_url,
            'parsed_at': self.parsed_at.isoformat()
        }
