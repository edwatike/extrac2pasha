"""
Модуль для A/B тестирования ML и Rule-Based стратегий.
"""

import os
import random
import pandas as pd
from typing import Dict, Tuple
from datetime import datetime
from src.protections.strategy_selector import StrategySelector
from src.protections.strategy_predictor import StrategyPredictor
from src.logger import logger


class ABTester:
    """Класс для A/B тестирования стратегий."""

    def __init__(self, results_path: str = "data/ab_test_results.csv", ml_weight: float = 0.5):
        """
        Инициализация A/B тестера.

        Args:
            results_path: Путь к файлу с результатами
            ml_weight: Вероятность выбора ML-стратегии (0-1)
        """
        self.results_path = results_path
        self.ml_weight = ml_weight
        self.selector = StrategySelector()
        self.predictor = StrategyPredictor()

        # Создаем директорию для результатов
        os.makedirs(os.path.dirname(results_path), exist_ok=True)

        # Инициализируем файл с результатами, если его нет
        if not os.path.exists(results_path):
            self._init_results_file()

    def _init_results_file(self) -> None:
        """Создает файл с результатами тестирования."""
        df = pd.DataFrame(
            columns=[
                "timestamp",
                "strategy_name",
                "method",
                "success",
                "duration",
                "protection_type",
                "url",
                "ip_region",
                "user_agent",
                "has_captcha",
            ]
        )
        df.to_csv(self.results_path, index=False)

    def select_strategy(self, protection_type: str, context: Dict) -> Tuple[str, str]:
        """
        Выбирает стратегию для тестирования.

        Args:
            protection_type: Тип защиты
            context: Контекст запроса

        Returns:
            Tuple[str, str]: (название стратегии, метод выбора)
        """
        # Выбираем метод случайно
        if random.random() < self.ml_weight:
            # ML-стратегия
            strategy = self.predictor.predict_best_strategy(context)
            method = "ML"
        else:
            # Rule-based стратегия
            strategy = self.selector.get_best_strategy(protection_type)
            method = "RuleBased"

        logger.info(f"Выбрана стратегия {strategy} методом {method}")
        return strategy, method

    def log_result(
        self, strategy_name: str, method: str, success: bool, duration: float, metadata: Dict
    ) -> None:
        """
        Логирует результат применения стратегии.

        Args:
            strategy_name: Название стратегии
            method: Метод выбора ("ML" или "RuleBased")
            success: Успешность применения
            duration: Время выполнения в секундах
            metadata: Дополнительные метаданные
        """
        try:
            # Формируем запись
            record = {
                "timestamp": datetime.now().isoformat(),
                "strategy_name": strategy_name,
                "method": method,
                "success": success,
                "duration": duration,
                "protection_type": metadata.get("protection_type", ""),
                "url": metadata.get("url", ""),
                "ip_region": metadata.get("ip_region", ""),
                "user_agent": metadata.get("user_agent", ""),
                "has_captcha": metadata.get("has_captcha", False),
            }

            # Добавляем запись в файл
            df = pd.DataFrame([record])
            df.to_csv(self.results_path, mode="a", header=False, index=False)

            logger.info(f"Записан результат A/B теста: {strategy_name} ({method})")

        except Exception as e:
            logger.error(f"Ошибка записи результата A/B теста: {e}")

    def get_statistics(self) -> Dict:
        """
        Возвращает статистику по результатам тестирования.

        Returns:
            Dict: Статистика по методам
        """
        try:
            df = pd.read_csv(self.results_path)

            stats = {
                "ML": {
                    "total": len(df[df["method"] == "ML"]),
                    "success_rate": df[df["method"] == "ML"]["success"].mean(),
                    "avg_duration": df[df["method"] == "ML"]["duration"].mean(),
                },
                "RuleBased": {
                    "total": len(df[df["method"] == "RuleBased"]),
                    "success_rate": df[df["method"] == "RuleBased"]["success"].mean(),
                    "avg_duration": df[df["method"] == "RuleBased"]["duration"].mean(),
                },
            }

            return stats

        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
