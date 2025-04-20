"""
Модуль с тестами для strategy_selector.py.
"""

import os
import tempfile
from datetime import datetime
import pytest
from src.protections.strategy_selector import StrategySelector, StrategyStats


def test_strategy_stats_model():
    """Проверяет создание модели StrategyStats."""
    stats = StrategyStats(
        strategy_name="test_strategy",
        success_count=5,
        fail_count=2,
        avg_time=1.5,
        last_used=datetime.now(),
        protection_type="cloudflare",
    )

    assert stats.strategy_name == "test_strategy"
    assert stats.success_count == 5
    assert stats.fail_count == 2
    assert stats.avg_time == 1.5
    assert stats.protection_type == "cloudflare"


def test_evaluate_strategy_result():
    """Проверяет обновление статистики стратегии."""
    with tempfile.NamedTemporaryFile() as tmp:
        selector = StrategySelector(tmp.name)

        # Первое применение стратегии
        selector.evaluate_strategy_result("test_strategy", True, 1.0, "cloudflare")

        stats = selector.get_strategy_stats("test_strategy")
        assert stats.success_count == 1
        assert stats.fail_count == 0
        assert stats.avg_time == 1.0

        # Второе применение (неудачное)
        selector.evaluate_strategy_result("test_strategy", False, 2.0, "cloudflare")

        stats = selector.get_strategy_stats("test_strategy")
        assert stats.success_count == 1
        assert stats.fail_count == 1
        assert stats.avg_time == 1.5  # Среднее время


def test_rank_strategies():
    """Проверяет ранжирование стратегий."""
    with tempfile.NamedTemporaryFile() as tmp:
        selector = StrategySelector(tmp.name)

        # Добавляем несколько стратегий
        selector.evaluate_strategy_result("strategy1", True, 1.0, "cloudflare")
        selector.evaluate_strategy_result("strategy1", True, 1.0, "cloudflare")
        selector.evaluate_strategy_result("strategy2", True, 0.5, "cloudflare")
        selector.evaluate_strategy_result("strategy2", False, 0.5, "cloudflare")
        selector.evaluate_strategy_result("strategy3", True, 2.0, "cloudflare")

        # Получаем ранжированный список
        ranked = selector.rank_strategies("cloudflare")

        # Проверяем порядок (стратегия2 должна быть первой из-за меньшего времени)
        assert ranked[0] == "strategy2"
        assert ranked[1] == "strategy1"
        assert ranked[2] == "strategy3"


def test_get_best_strategy():
    """Проверяет получение лучшей стратегии."""
    with tempfile.NamedTemporaryFile() as tmp:
        selector = StrategySelector(tmp.name)

        # Добавляем стратегии
        selector.evaluate_strategy_result("strategy1", True, 1.0, "cloudflare")
        selector.evaluate_strategy_result("strategy2", True, 0.5, "cloudflare")

        # Получаем лучшую стратегию
        best = selector.get_best_strategy("cloudflare")
        assert best == "strategy2"  # Должна быть выбрана как более быстрая

        # Проверяем для неизвестного типа защиты
        assert selector.get_best_strategy("unknown") is None


def test_get_strategy_stats():
    """Проверяет получение статистики стратегии."""
    with tempfile.NamedTemporaryFile() as tmp:
        selector = StrategySelector(tmp.name)

        # Добавляем стратегию
        selector.evaluate_strategy_result("test_strategy", True, 1.0, "cloudflare")

        # Получаем статистику
        stats = selector.get_strategy_stats("test_strategy")
        assert stats is not None
        assert stats.strategy_name == "test_strategy"
        assert stats.success_count == 1
        assert stats.fail_count == 0
        assert stats.avg_time == 1.0
        assert stats.protection_type == "cloudflare"

        # Проверяем для несуществующей стратегии
        assert selector.get_strategy_stats("unknown") is None
