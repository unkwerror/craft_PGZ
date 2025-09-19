# application/services/economics_service.py
from typing import Dict, List, Optional
from decimal import Decimal
import logging
from datetime import datetime

from domain.value_objects.economics import (
    ProjectConfig, EconomicsResult, TeamRole, ProjectType, 
    RiskLevel, DEFAULT_TEAM_TEMPLATES
)
from core.config import get_settings

logger = logging.getLogger(__name__)

class EconomicsService:
    """Сервис для расчета экономики проектов"""
    
    def __init__(self):
        self.settings = get_settings()
        self.templates = DEFAULT_TEAM_TEMPLATES
    
    def calculate_project_economics(self, 
                                  tender_amount: Decimal,
                                  config: ProjectConfig) -> EconomicsResult:
        """
        Основной метод расчета экономики проекта
        
        Args:
            tender_amount: Стоимость тендера
            config: Конфигурация проекта
            
        Returns:
            EconomicsResult: Результат расчета экономики
        """
        logger.info(f"Calculating economics for project: {config.project_name}")
        
        try:
            # 1. Расчет затрат по команде
            team_costs, team_breakdown = self._calculate_team_costs(config)
            
            # 2. Накладные расходы
            overhead_costs = sum(config.overhead_costs.values())
            
            # 3. Валовая прибыль
            gross_profit = tender_amount - team_costs - overhead_costs
            
            # 4. Налоги
            tax_costs = self._calculate_taxes(gross_profit, config.taxes)
            
            # 5. Чистая прибыль
            net_profit = gross_profit - tax_costs
            
            # 6. Расчет показателей
            total_costs = team_costs + overhead_costs + tax_costs
            profit_margin = self._calculate_profit_margin(net_profit, tender_amount)
            roi = self._calculate_roi(total_costs, net_profit)
            payback_period = self._calculate_payback_period(config, net_profit)
            
            # 7. Анализ рисков
            risk_level, risk_score, risk_factors = self._assess_risk(config, profit_margin)
            
            # 8. Сравнение с рынком
            market_comparison = self._get_market_comparison(config.project_type, profit_margin)
            
            result = EconomicsResult(
                total_revenue=tender_amount,
                total_costs=total_costs,
                gross_profit=gross_profit,
                net_profit=net_profit,
                profit_margin=profit_margin,
                roi=roi,
                payback_period_months=payback_period,
                team_costs=team_costs,
                overhead_costs=overhead_costs,
                tax_costs=tax_costs,
                team_breakdown=team_breakdown,
                risk_level=risk_level,
                risk_score=risk_score,
                risk_factors=risk_factors,
                market_comparison=market_comparison
            )
            
            logger.info(f"Economics calculated successfully. Net profit: {net_profit}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating economics: {str(e)}")
            raise
    
    def _calculate_team_costs(self, config: ProjectConfig) -> tuple[Decimal, Dict[str, Decimal]]:
        """Расчет затрат по команде"""
        team_breakdown = {}
        total_team_costs = Decimal(0)
        
        for role_name, role in config.team.items():
            role_cost = config.total_amount * Decimal(str(role.percentage))
            team_breakdown[role_name] = role_cost
            total_team_costs += role_cost
        
        return total_team_costs, team_breakdown
    
    def _calculate_taxes(self, gross_profit: Decimal, taxes: Dict[str, float]) -> Decimal:
        """Расчет налогов"""
        tax_amount = Decimal(0)
        
        for tax_type, rate in taxes.items():
            tax = gross_profit * Decimal(str(rate))
            tax_amount += tax
            logger.debug(f"Tax {tax_type}: {tax} (rate: {rate * 100}%)")
        
        return tax_amount
    
    def _calculate_profit_margin(self, net_profit: Decimal, total_revenue: Decimal) -> float:
        """Расчет маржи прибыли в процентах"""
        if total_revenue <= 0:
            return 0.0
        return float((net_profit / total_revenue) * 100)
    
    def _calculate_roi(self, investment: Decimal, profit: Decimal) -> float:
        """Расчет ROI в процентах"""
        if investment <= 0:
            return 0.0
        return float((profit / investment) * 100)
    
    def _calculate_payback_period(self, config: ProjectConfig, net_profit: Decimal) -> Optional[float]:
        """Расчет периода окупаемости в месяцах"""
        if net_profit <= 0:
            return None
        
        monthly_profit = net_profit / config.duration_months
        if monthly_profit <= 0:
            return None
        
        total_investment = config.total_amount
        return float(total_investment / monthly_profit)
    
    def _assess_risk(self, config: ProjectConfig, profit_margin: float) -> tuple[RiskLevel, float, List[str]]:
        """Оценка рисков проекта"""
        risk_factors = []
        risk_score = 0.0
        
        # Базовый риск по типу проекта
        project_risk_map = {
            ProjectType.ARCHITECTURE: 0.3,
            ProjectType.ENGINEERING: 0.4,
            ProjectType.LANDSCAPING: 0.2,
            ProjectType.COMPLEX: 0.6,
            ProjectType.RESTAVRATION: 0.7,
            ProjectType.INFRASTRUCTURE: 0.5
        }
        
        base_risk = project_risk_map.get(config.project_type, 0.5)
        risk_score += base_risk
        
        # Риск по длительности проекта
        if config.duration_months > 12:
            risk_score += 0.2
            risk_factors.append("Длительный проект (> 12 месяцев)")
        elif config.duration_months > 6:
            risk_score += 0.1
            risk_factors.append("Проект средней длительности (6-12 месяцев)")
        
        # Риск по марже
        if profit_margin < 10:
            risk_score += 0.3
            risk_factors.append("Низкая маржа прибыли (< 10%)")
        elif profit_margin < 15:
            risk_score += 0.1
            risk_factors.append("Средняя маржа прибыли (10-15%)")
        
        # Риск по размеру команды
        if len(config.team) > 8:
            risk_score += 0.1
            risk_factors.append("Большая команда (> 8 человек)")
        elif len(config.team) < 3:
            risk_score += 0.2
            risk_factors.append("Малая команда (< 3 человек)")
        
        # Определение уровня риска
        risk_score = min(risk_score, 1.0)  # Ограничиваем максимальным значением
        
        if risk_score >= 0.7:
            risk_level = RiskLevel.CRITICAL
        elif risk_score >= 0.5:
            risk_level = RiskLevel.HIGH
        elif risk_score >= 0.3:
            risk_level = RiskLevel.MEDIUM
        else:
            risk_level = RiskLevel.LOW
        
        return risk_level, risk_score, risk_factors
    
    def _get_market_comparison(self, project_type: ProjectType, profit_margin: float) -> Dict[str, float]:
        """Сравнение с рыночными показателями"""
        # Средние рыночные показатели по типам проектов
        market_averages = {
            ProjectType.ARCHITECTURE: {'profit_margin': 15.0, 'roi': 25.0},
            ProjectType.ENGINEERING: {'profit_margin': 12.0, 'roi': 20.0},
            ProjectType.LANDSCAPING: {'profit_margin': 18.0, 'roi': 30.0},
            ProjectType.COMPLEX: {'profit_margin': 10.0, 'roi': 15.0},
            ProjectType.RESTAVRATION: {'profit_margin': 8.0, 'roi': 12.0},
            ProjectType.INFRASTRUCTURE: {'profit_margin': 13.0, 'roi': 22.0}
        }
        
        market_avg = market_averages.get(project_type, {'profit_margin': 12.0, 'roi': 20.0})
        
        return {
            'market_avg_profit_margin': market_avg['profit_margin'],
            'market_avg_roi': market_avg['roi'],
            'profit_margin_diff': profit_margin - market_avg['profit_margin'],
            'market_position': self._get_market_position(profit_margin, market_avg['profit_margin'])
        }
    
    def _get_market_position(self, our_margin: float, market_avg: float) -> str:
        """Определение позиции относительно рынка"""
        diff_percent = (our_margin - market_avg) / market_avg * 100 if market_avg > 0 else 0
        
        if diff_percent >= 20:
            return "Значительно выше рынка"
        elif diff_percent >= 10:
            return "Выше рынка"
        elif diff_percent >= -10:
            return "На уровне рынка"
        elif diff_percent >= -20:
            return "Ниже рынка"
        else:
            return "Значительно ниже рынка"
    
    def get_team_template(self, template_name: str) -> Optional[Dict[str, TeamRole]]:
        """Получить шаблон команды"""
        return self.templates.get(template_name)
    
    def get_available_templates(self) -> List[str]:
        """Получить список доступных шаблонов"""
        return list(self.templates.keys())
    
    def save_custom_template(self, name: str, team: Dict[str, TeamRole]) -> None:
        """Сохранить пользовательский шаблон команды"""
        # TODO: Реализовать сохранение в базу данных
        self.templates[name] = team
        logger.info(f"Custom template '{name}' saved")