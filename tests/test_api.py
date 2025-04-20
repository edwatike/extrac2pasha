"""
Тесты для FastAPI приложения.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from src.api.app import app
from src.agent.auto_extractor import AutoExtractor

# Создаем тестового клиента
client = TestClient(app)


def test_health_check():
    """Тест проверки работоспособности API."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "timestamp" in response.json()


def test_extract_success():
    """Тест успешного извлечения."""
    test_url = "https://example.com"
    test_result = {
        "status": "success",
        "strategy": "solve_with_playwright",
        "html": "<html>Test content</html>",
        "has_protection": True,
        "protection_type": "cloudflare",
        "output_file": "output/test.json",
    }

    with patch.object(AutoExtractor, "run_agent", return_value=test_result):
        response = client.post("/extract", json={"url": test_url})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["strategy_used"] == test_result["strategy"]
        assert data["html_snippet"] == test_result["html"][:500]
        assert data["has_protection"] == test_result["has_protection"]
        assert data["protection_type"] == test_result["protection_type"]
        assert data["output_file"] == test_result["output_file"]
        assert "timestamp" in data


def test_extract_error():
    """Тест обработки ошибки при извлечении."""
    test_url = "https://example.com"
    test_error = "Test error"

    with patch.object(AutoExtractor, "run_agent", side_effect=Exception(test_error)):
        response = client.post("/extract", json={"url": test_url})

        assert response.status_code == 500
        data = response.json()
        assert data["status"] == "error"
        assert data["error"] == test_error
        assert "timestamp" in data


def test_extract_invalid_url():
    """Тест обработки неверного URL."""
    response = client.post("/extract", json={"url": "not-a-url"})

    assert response.status_code == 422  # Validation Error


def test_extract_with_options():
    """Тест извлечения с дополнительными опциями."""
    test_url = "https://example.com"
    test_options = {"timeout": 60, "user_agent": "Test Agent"}
    test_result = {
        "status": "success",
        "strategy": "solve_with_headers_tweaking",
        "html": "<html>Test content</html>",
        "has_protection": False,
        "protection_type": None,
        "output_file": "output/test.json",
    }

    with patch.object(AutoExtractor, "run_agent", return_value=test_result) as mock_run:
        response = client.post("/extract", json={"url": test_url, "options": test_options})

        assert response.status_code == 200
        mock_run.assert_called_once_with(test_url, **test_options)


def test_get_stats():
    """Тест получения статистики."""
    response = client.get("/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "total_requests" in data
    assert "success_rate" in data
    assert "most_common_protection" in data
