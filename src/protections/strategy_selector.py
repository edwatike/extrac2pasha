"""
Модуль для выбора стратегий обхода защиты на основе правил.
"""

from typing import Dict, Optional
from src.logger import logger


class StrategySelector:
    """Класс для выбора стратегий обхода защиты."""

    def __init__(self):
        """Инициализация селектора стратегий."""
        self.strategies = {
            "cloudflare": ["playwright_interactive", "selenium_stealth", "requests_rotating_proxy"],
            "ddos_guard": ["selenium_stealth", "playwright_interactive", "requests_rotating_proxy"],
            "recaptcha": ["playwright_interactive", "selenium_stealth"],
            "ip_block": ["requests_rotating_proxy", "selenium_stealth"],
        }

    def get_best_strategy(self, protection_type: str) -> str:
        """
        Возвращает лучшую стратегию для данного типа защиты.

        Args:
            protection_type: Тип защиты

        Returns:
            str: Название стратегии
        """
        try:
            # Получаем список стратегий для данного типа защиты
            strategies = self.strategies.get(protection_type, [])

            if not strategies:
                # Если тип защиты неизвестен, используем стандартную стратегию
                logger.warning(f"Неизвестный тип защиты: {protection_type}")
                return "selenium_stealth"

            # Возвращаем первую (лучшую) стратегию из списка
            return strategies[0]

        except Exception as e:
            logger.error(f"Ошибка выбора стратегии: {e}")
            return "selenium_stealth"
