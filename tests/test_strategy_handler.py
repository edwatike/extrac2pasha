"""
Модуль с тестами для strategy_handler.py.
"""

import os
import tempfile
import json
from datetime import datetime
import pytest
from unittest.mock import patch, MagicMock
from src.protections.strategy_handler import StrategyHandler


def test_save_and_find_strategy():
    """Проверяет сохранение и поиск стратегии."""
    with tempfile.NamedTemporaryFile() as tmp:
        handler = StrategyHandler(tmp.name)

        # Создаем тестовую стратегию
        strategy = {
            "name": "test_strategy",
            "protection_type": "cloudflare",
            "steps": [{"action": "wait", "timeout": 5}, {"action": "click", "selector": "#button"}],
        }

        # Сохраняем стратегию
        handler.save_strategy(strategy)

        # Ищем стратегию
        found = handler.find_strategy("cloudflare")
        assert found is not None
        assert found["name"] == "test_strategy"
        assert found["protection_type"] == "cloudflare"
        assert len(found["steps"]) == 2


def test_default_strategies():
    """Проверяет применение стратегий по умолчанию."""
    with tempfile.NamedTemporaryFile() as tmp:
        handler = StrategyHandler(tmp.name)

        # Проверяем для известного типа защиты
        strategy = handler.find_strategy("cloudflare")
        assert strategy is not None
        assert strategy["name"] == "default_cloudflare"

        # Проверяем для неизвестного типа защиты
        strategy = handler.find_strategy("unknown")
        assert strategy is not None
        assert strategy["name"] == "default_generic"


def test_update_strategy_stats():
    """Проверяет обновление статистики стратегии."""
    with tempfile.NamedTemporaryFile() as tmp:
        handler = StrategyHandler(tmp.name)

        # Создаем тестовую стратегию
        strategy = {"name": "test_strategy", "protection_type": "cloudflare", "steps": []}
        handler.save_strategy(strategy)

        # Обновляем статистику
        handler.update_strategy_stats("test_strategy", True, 1.0)

        # Проверяем, что статистика обновилась
        found = handler.find_strategy("cloudflare")
        assert found is not None
        assert found["name"] == "test_strategy"

        # Проверяем, что статистика сохранилась в селекторе
        stats = handler.selector.get_strategy_stats("test_strategy")
        assert stats is not None
        assert stats.success_count == 1
        assert stats.fail_count == 0
        assert stats.avg_time == 1.0


def test_strategy_application():
    """Проверяет применение стратегии."""
    with tempfile.NamedTemporaryFile() as tmp:
        handler = StrategyHandler(tmp.name)

        # Создаем тестовую стратегию
        strategy = {
            "name": "test_strategy",
            "protection_type": "cloudflare",
            "steps": [{"action": "wait", "timeout": 1}, {"action": "click", "selector": "#button"}],
        }
        handler.save_strategy(strategy)

        # Применяем стратегию
        result = handler.apply_strategy("cloudflare")
        assert result is not None
        assert result["success"] is True
        assert result["strategy_name"] == "test_strategy"

        # Проверяем, что статистика обновилась
        stats = handler.selector.get_strategy_stats("test_strategy")
        assert stats is not None
        assert stats.success_count == 1


def test_apply_nonexistent_strategy():
    """Проверяет обработку несуществующей стратегии."""
    with tempfile.NamedTemporaryFile() as tmp:
        handler = StrategyHandler(tmp.name)

        # Пробуем применить несуществующую стратегию
        result = handler.apply_strategy("nonexistent_protection")

        # Проверяем, что результат содержит информацию о неудаче
        assert result is not None
        assert result["success"] is False
        assert "error" in result
        assert result["strategy_name"] == "default_generic"


def test_ranked_strategy_selection():
    """Проверяет выбор стратегии на основе рейтинга."""
    with tempfile.NamedTemporaryFile() as tmp:
        handler = StrategyHandler(tmp.name)

        # Создаем две стратегии для одного типа защиты
        strategy1 = {"name": "high_success_strategy", "protection_type": "cloudflare", "steps": []}
        strategy2 = {"name": "low_success_strategy", "protection_type": "cloudflare", "steps": []}

        handler.save_strategy(strategy1)
        handler.save_strategy(strategy2)

        # Обновляем статистику для первой стратегии (высокий успех)
        for _ in range(5):
            handler.update_strategy_stats("high_success_strategy", True, 1.0)

        # Обновляем статистику для второй стратегии (низкий успех)
        for _ in range(3):
            handler.update_strategy_stats("low_success_strategy", True, 2.0)
        for _ in range(2):
            handler.update_strategy_stats("low_success_strategy", False, 2.0)

        # Получаем лучшую стратегию
        best_strategy = handler.selector.get_best_strategy("cloudflare")
        assert best_strategy == "high_success_strategy"


def test_demotion_of_failed_strategy():
    """Проверяет понижение рейтинга неудачной стратегии."""
    with tempfile.NamedTemporaryFile() as tmp:
        handler = StrategyHandler(tmp.name)

        # Создаем стратегию
        strategy = {"name": "test_strategy", "protection_type": "cloudflare", "steps": []}
        handler.save_strategy(strategy)

        # Добавляем успешные применения
        for _ in range(3):
            handler.update_strategy_stats("test_strategy", True, 1.0)

        # Добавляем неудачные применения
        for _ in range(5):
            handler.update_strategy_stats("test_strategy", False, 1.0)

        # Создаем новую стратегию с лучшей статистикой
        better_strategy = {"name": "better_strategy", "protection_type": "cloudflare", "steps": []}
        handler.save_strategy(better_strategy)
        handler.update_strategy_stats("better_strategy", True, 1.0)

        # Проверяем, что новая стратегия имеет более высокий приоритет
        best_strategy = handler.selector.get_best_strategy("cloudflare")
        assert best_strategy == "better_strategy"


def test_duplicate_strategy_prevention():
    """Проверяет предотвращение дублирования стратегий."""
    with tempfile.NamedTemporaryFile() as tmp:
        handler = StrategyHandler(tmp.name)

        # Создаем начальную стратегию
        initial_strategy = {
            "name": "test_strategy",
            "protection_type": "cloudflare",
            "steps": [{"action": "wait", "timeout": 5}],
        }
        handler.save_strategy(initial_strategy)

        # Пробуем сохранить стратегию с тем же именем
        updated_strategy = {
            "name": "test_strategy",
            "protection_type": "cloudflare",
            "steps": [{"action": "click", "selector": "#button"}],
        }
        handler.save_strategy(updated_strategy)

        # Проверяем, что найдена обновленная версия
        found = handler.find_strategy("cloudflare")
        assert found is not None
        assert found["name"] == "test_strategy"
        assert len(found["steps"]) == 1
        assert found["steps"][0]["action"] == "click"


def test_strategy_success_rate():
    """Проверяет точность подсчета статистики стратегии."""
    with tempfile.NamedTemporaryFile() as tmp:
        handler = StrategyHandler(tmp.name)

        # Создаем стратегию
        strategy = {"name": "test_strategy", "protection_type": "cloudflare", "steps": []}
        handler.save_strategy(strategy)

        # Добавляем успешные применения
        success_times = [1.0, 1.5, 2.0]
        for time in success_times:
            handler.update_strategy_stats("test_strategy", True, time)

        # Добавляем неудачные применения
        fail_times = [0.5, 1.0]
        for time in fail_times:
            handler.update_strategy_stats("test_strategy", False, time)

        # Получаем статистику
        stats = handler.selector.get_strategy_stats("test_strategy")
        assert stats is not None
        assert stats.success_count == 3
        assert stats.fail_count == 2

        # Проверяем среднее время (только для успешных применений)
        expected_avg_time = sum(success_times) / len(success_times)
        assert abs(stats.avg_time - expected_avg_time) < 0.001
