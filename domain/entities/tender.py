# domain/entities/tender.py
from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

class TenderStatus(str, Enum):
    """Статус тендера"""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DRAFT = "draft"

class TenderType(str, Enum):
    """Тип тендера по 44-ФЗ/223-ФЗ"""
    FZ_44 = "44-fz"
    FZ_223 = "223-fz"
    COMMERCIAL = "commercial"

class ProcurementMethod(str, Enum):
    """Способ закупки"""
    AUCTION = "auction"
    CONTEST = "contest" 
    REQUEST = "request"
    SOLE_SOURCE = "sole_source"

@dataclass
class TenderDocument:
    """Документ тендера"""
    name: str
    url: str
    file_size: Optional[int] = None
    file_type: Optional[str] = None
    download_path: Optional[str] = None
    processed: bool = False
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class TenderParticipant:
    """Участник тендера"""
    name: str
    inn: Optional[str] = None
    kpp: Optional[str] = None
    address: Optional[str] = None
    is_winner: bool = False

@dataclass
class Tender:
    """Основная сущность - Тендер"""
    # Обязательные поля
    reg_number: str
    title: str
    customer: str
    initial_price: Decimal
    status: TenderStatus
    tender_type: TenderType
    
    # Опциональные поля
    description: Optional[str] = None
    procurement_method: Optional[ProcurementMethod] = None
    application_deadline: Optional[datetime] = None
    contract_execution_deadline: Optional[datetime] = None
    winner_price: Optional[Decimal] = None
    
    # Требования к участникам
    participant_requirements: Dict[str, Any] = field(default_factory=dict)
    application_security: Optional[Decimal] = None
    contract_security: Optional[Decimal] = None
    
    # Связанные объекты
    documents: List[TenderDocument] = field(default_factory=list)
    participants: List[TenderParticipant] = field(default_factory=list)
    
    # Метаданные
    source_url: str = ""
    parsed_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_document(self, document: TenderDocument) -> None:
        """Добавить документ к тендеру"""
        self.documents.append(document)
    
    def add_participant(self, participant: TenderParticipant) -> None:
        """Добавить участника тендера"""
        self.participants.append(participant)
    
    def get_winner(self) -> Optional[TenderParticipant]:
        """Получить победителя тендера"""
        for participant in self.participants:
            if participant.is_winner:
                return participant
        return None
    
    def is_active(self) -> bool:
        """Проверить, активен ли тендер"""
        return (self.status == TenderStatus.ACTIVE and 
                self.application_deadline and 
                self.application_deadline > datetime.now())
    
    def calculate_discount(self) -> Optional[float]:
        """Рассчитать размер скидки (если есть победитель)"""
        if self.winner_price and self.initial_price:
            discount = (self.initial_price - self.winner_price) / self.initial_price
            return float(discount * 100)
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Преобразовать в словарь для сериализации"""
        return {
            'reg_number': self.reg_number,
            'title': self.title,
            'customer': self.customer,
            'initial_price': float(self.initial_price),
            'winner_price': float(self.winner_price) if self.winner_price else None,
            'status': self.status.value,
            'tender_type': self.tender_type.value,
            'application_deadline': self.application_deadline.isoformat() if self.application_deadline else None,
            'contract_execution_deadline': self.contract_execution_deadline.isoformat() if self.contract_execution_deadline else None,
            'documents_count': len(self.documents),
            'participants_count': len(self.participants),
            'discount_percent': self.calculate_discount(),
            'source_url': self.source_url,
            'parsed_at': self.parsed_at.isoformat()
        }