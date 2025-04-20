"""
Тесты для модуля auto_extractor.py
"""

import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.agent.auto_extractor import AutoExtractor
import json


def test_run_agent_no_protection():
    """Тест работы агента без защиты."""
    test_url = "https://example.com"
    test_html = "<html>Test content</html>"

    # Мокаем requests.get
    mock_response = MagicMock()
    mock_response.text = test_html
    mock_response.raise_for_status.return_value = None

    with patch("requests.get", return_value=mock_response), patch(
        "src.protections.ProtectionDetector.detect_protection", return_value=(None, None)
    ):
        extractor = AutoExtractor()
        result = extractor.run_agent(test_url)

        assert result["status"] == "success"
        assert result["has_protection"] is False
        assert result["strategy"] is None
        assert result["protection_type"] is None
        assert Path(result["output_file"]).exists()


def test_run_agent_with_protection():
    """Тест работы агента с защитой."""
    test_url = "https://example.com"
    test_html = "<html>Protected content</html>"
    protection_type = "cloudflare"
    protection_signs = ["cf-browser-verification"]

    # Мокаем requests.get
    mock_response = MagicMock()
    mock_response.text = test_html
    mock_response.raise_for_status.return_value = None

    with patch("requests.get", return_value=mock_response), patch(
        "src.protections.ProtectionDetector.detect_protection",
        return_value=(protection_type, protection_signs),
    ), patch(
        "src.protections.strategy_handler.StrategyHandler.try_strategies", return_value=test_html
    ), patch(
        "src.protections.strategy_handler.StrategyHandler.find_strategy",
        return_value="solve_with_playwright",
    ):
        extractor = AutoExtractor()
        result = extractor.run_agent(test_url)

        assert result["status"] == "success"
        assert result["has_protection"] is True
        assert result["strategy"] == "solve_with_playwright"
        assert result["protection_type"] == protection_type
        assert Path(result["output_file"]).exists()


def test_run_agent_error():
    """Тест обработки ошибок агентом."""
    test_url = "https://example.com"

    # Мокаем requests.get, чтобы он вызвал исключение
    with patch("requests.get", side_effect=Exception("Test error")), patch(
        "src.protections.ProtectionDetector.detect_protection",
        return_value=("unknown", ["request_error"]),
    ):
        extractor = AutoExtractor()
        result = extractor.run_agent(test_url)

        assert result["status"] == "error"
        assert result["has_protection"] is True
        assert result["strategy"] is None
        assert result["protection_type"] == "unknown"
        assert Path(result["output_file"]).exists()


def test_save_result():
    """Тест сохранения результатов."""
    test_url = "https://example.com"
    test_html = "<html>Test content</html>"
    test_status = "success"
    test_strategy = "solve_with_playwright"

    extractor = AutoExtractor()
    output_file = extractor._save_result(test_url, test_html, test_status, test_strategy)

    assert Path(output_file).exists()

    # Проверяем содержимое файла
    with open(output_file, "r", encoding="utf-8") as f:
        data = json.load(f)
        assert data["url"] == test_url
        assert data["status"] == test_status
        assert data["strategy"] == test_strategy
        assert data["html"] == test_html
