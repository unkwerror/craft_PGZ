# domain/value_objects/economics.py (исправленная версия с закрытыми скобками)

from typing import Dict, Optional, List
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum

class ProjectType(str, Enum):
    """Тип проекта"""
    ARCHITECTURE = "architecture"
    ENGINEERING = "engineering"
    LANDSCAPING = "landscaping"
    COMPLEX = "complex"
    RESTAVRATION = "restoration"
    INFRASTRUCTURE = "infrastructure"

class RiskLevel(str, Enum):
    """Уровень риска"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class TeamRole:
    """Роль в команде проекта"""
    name: str
    percentage: float  # Процент от общей стоимости (0.0-1.0)
    hourly_rate: Optional[int] = None
    hours_per_month: Optional[int] = None
    description: str = ""
    
    def __post_init__(self):
        if not 0 <= self.percentage <= 1:
            raise ValueError(f"Percentage must be between 0 and 1, got {self.percentage}")

@dataclass
class ProjectConfig:
    """Конфигурация проекта для расчета экономики"""
    project_name: str
    total_amount: Decimal
    duration_months: int
    project_type: ProjectType
    team: Dict[str, TeamRole]
    overhead_costs: Dict[str, Decimal] = field(default_factory=dict)
    taxes: Dict[str, float] = field(default_factory=dict)
    
    def __post_init__(self):
        # Проверяем, что общий процент команды не превышает 100%
        total_percentage = sum(role.percentage for role in self.team.values())
        if total_percentage > 1.0:
            raise ValueError(f"Total team percentage exceeds 100%: {total_percentage * 100:.1f}%")

@dataclass
class EconomicsResult:
    """Результат расчета экономики проекта"""
    # Основные финансовые показатели
    total_revenue: Decimal
    total_costs: Decimal
    gross_profit: Decimal
    net_profit: Decimal
    profit_margin: float  # В процентах
    
    # Показатели эффективности
    roi: float  # Return on Investment в процентах
    payback_period_months: Optional[float] = None
    
    # Разбивка затрат
    team_costs: Decimal = Decimal(0)
    overhead_costs: Decimal = Decimal(0)
    tax_costs: Decimal = Decimal(0)
    team_breakdown: Dict[str, Decimal] = field(default_factory=dict)
    
    # Анализ рисков
    risk_level: RiskLevel = RiskLevel.MEDIUM
    risk_score: float = 0.5  # 0.0-1.0
    risk_factors: List[str] = field(default_factory=list)
    
    # Сравнение с рынком
    market_comparison: Dict[str, float] = field(default_factory=dict)
    
    def is_profitable(self) -> bool:
        """Проверить прибыльность проекта"""
        return self.net_profit > 0
    
    def get_profit_grade(self) -> str:
        """Получить оценку прибыльности"""
        if self.profit_margin >= 20:
            return "Отличная"
        elif self.profit_margin >= 15:
            return "Хорошая"
        elif self.profit_margin >= 10:
            return "Удовлетворительная"
        elif self.profit_margin >= 5:
            return "Низкая"
        else:
            return "Убыточная"
    
    def to_dict(self) -> Dict:
        """Преобразовать в словарь для JSON"""
        return {
            'total_revenue': float(self.total_revenue),
            'total_costs': float(self.total_costs),
            'gross_profit': float(self.gross_profit),
            'net_profit': float(self.net_profit),
            'profit_margin': self.profit_margin,
            'roi': self.roi,
            'payback_period_months': self.payback_period_months,
            'team_costs': float(self.team_costs),
            'overhead_costs': float(self.overhead_costs),
            'tax_costs': float(self.tax_costs),
            'team_breakdown': {k: float(v) for k, v in self.team_breakdown.items()},
            'risk_level': self.risk_level.value,
            'risk_score': self.risk_score,
            'risk_factors': self.risk_factors,
            'profit_grade': self.get_profit_grade(),
            'is_profitable': self.is_profitable()
        }

# Предустановленные шаблоны команд
DEFAULT_TEAM_TEMPLATES = {
    "standard_architecture": {
        "ГИП": TeamRole("ГИП", 0.15, 3000, 80),
        "Архитектор": TeamRole("Архитектор", 0.25, 2500, 120),
        "Конструктор": TeamRole("Конструктор", 0.12, 2200, 100),
        "Инженер ОВ": TeamRole("Инженер ОВ", 0.08, 2000, 80),
        "Инженер ЭС": TeamRole("Инженер ЭС", 0.08, 2000, 80),
        "Сметчик": TeamRole("Сметчик", 0.12, 1800, 60)
    },
    "complex_project": {
        "ГИП": TeamRole("ГИП", 0.12, 3500, 100),
        "Главный архитектор": TeamRole("Главный архитектор", 0.18, 3000, 120),
        "Архитектор": TeamRole("Архитектор", 0.15, 2500, 100),
        "Конструктор": TeamRole("Конструктор", 0.15, 2200, 120),
        "Инженер ОВ": TeamRole("Инженер ОВ", 0.10, 2000, 100),
        "Инженер ЭС": TeamRole("Инженер ЭС", 0.10, 2000, 100),
        "Инженер ВК": TeamRole("Инженер ВК", 0.08, 1900, 80),
        "Сметчик": TeamRole("Сметчик", 0.12, 1800, 80)
    },
    "small_project": {
        "ГИП": TeamRole("ГИП", 0.20, 2500, 60),
        "Архитектор": TeamRole("Архитектор", 0.30, 2200, 80),
        "Инженер": TeamRole("Инженер", 0.25, 1800, 100),
        "Сметчик": TeamRole("Сметчик", 0.15, 1600, 40)
    }
}