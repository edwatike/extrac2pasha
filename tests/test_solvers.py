"""
Тесты для модуля solvers.py
"""

import pytest
from unittest.mock import patch, MagicMock
from src.protections.solvers import solve_with_headers_tweaking, solve_with_retry_and_delay


def test_solve_with_headers_tweaking_success():
    """Тест успешного обхода через модификацию заголовков."""
    test_url = "https://example.com"
    test_html = "<html>Test content</html>"

    # Мокаем requests.get
    mock_response = MagicMock()
    mock_response.text = test_html
    mock_response.raise_for_status.return_value = None

    with patch("requests.get", return_value=mock_response) as mock_get:
        result = solve_with_headers_tweaking(test_url)

        # Проверяем, что функция вернула правильный HTML
        assert result == test_html

        # Проверяем, что requests.get был вызван с правильными заголовками
        mock_get.assert_called_once()
        call_args = mock_get.call_args[1]
        assert "headers" in call_args
        headers = call_args["headers"]
        assert "User-Agent" in headers
        assert "Accept" in headers
        assert "Accept-Language" in headers


def test_solve_with_headers_tweaking_failure():
    """Тест неудачного обхода через модификацию заголовков."""
    test_url = "https://example.com"

    # Мокаем requests.get, чтобы он вызвал исключение
    with patch("requests.get", side_effect=Exception("Test error")):
        result = solve_with_headers_tweaking(test_url)
        assert result is None


def test_solve_with_retry_and_delay_success():
    """Тест успешного обхода через повторные запросы."""
    test_url = "https://example.com"
    test_html = "<html>Test content</html>"

    # Мокаем requests.get и time.sleep
    mock_response = MagicMock()
    mock_response.text = test_html
    mock_response.raise_for_status.return_value = None

    with patch("requests.get", return_value=mock_response) as mock_get, patch(
        "time.sleep"
    ) as mock_sleep:
        result = solve_with_retry_and_delay(test_url)

        # Проверяем, что функция вернула правильный HTML
        assert result == test_html

        # Проверяем, что requests.get был вызван
        mock_get.assert_called_once()

        # Проверяем, что time.sleep был вызван
        mock_sleep.assert_called_once()


def test_solve_with_retry_and_delay_failure():
    """Тест неудачного обхода через повторные запросы."""
    test_url = "https://example.com"

    # Мокаем requests.get, чтобы он всегда вызывал исключение
    with patch("requests.get", side_effect=Exception("Test error")), patch(
        "time.sleep"
    ) as mock_sleep:
        result = solve_with_retry_and_delay(test_url, max_retries=2)

        # Проверяем, что функция вернула None после всех попыток
        assert result is None

        # Проверяем, что было сделано правильное количество попыток
        assert mock_sleep.call_count == 2
