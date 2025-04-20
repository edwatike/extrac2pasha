"""
Тесты для модуля исследования новых стратегий.
"""

import pytest
from unittest.mock import MagicMock, patch
from src.protections.strategy_discovery import StrategyDiscovery
from src.protections.strategy_handler import StrategyHandler


@pytest.fixture
def strategy_handler():
    """Фикстура для создания мока StrategyHandler."""
    handler = MagicMock(spec=StrategyHandler)
    return handler


@pytest.fixture
def strategy_discovery(strategy_handler):
    """Фикстура для создания StrategyDiscovery."""
    return StrategyDiscovery(strategy_handler)


def test_discover_new_strategy_success(strategy_discovery, strategy_handler):
    """Тест успешного открытия новой стратегии."""
    url = "https://example.com"
    context = {"protection_type": "test_protection"}

    # Мокаем успешный ответ
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.text = "<html>Test content</html>"

        strategy_name = strategy_discovery.discover_new_strategy(url, context)

        assert strategy_name is not None
        assert strategy_name.startswith("custom_user_agent_")
        strategy_handler.save_strategy.assert_called_once()


def test_discover_new_strategy_failure(strategy_discovery, strategy_handler):
    """Тест неудачного открытия новой стратегии."""
    url = "https://example.com"
    context = {"protection_type": "test_protection"}

    # Мокаем неудачные ответы
    with patch("requests.get") as mock_get:
        mock_get.side_effect = Exception("Test error")

        strategy_name = strategy_discovery.discover_new_strategy(url, context)

        assert strategy_name is None
        strategy_handler.save_strategy.assert_not_called()


def test_try_different_user_agents(strategy_discovery):
    """Тест перебора разных User-Agent'ов."""
    url = "https://example.com"
    context = {}

    with patch("requests.get") as mock_get:
        # Первые два User-Agent'а не сработают
        mock_get.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            MagicMock(status_code=200, text="<html>Success</html>"),
        ]

        strategy_name = strategy_discovery._try_different_user_agents(url, context)

        assert strategy_name is not None
        assert strategy_name.startswith("custom_user_agent_")


def test_try_playwright_with_interactions(strategy_discovery):
    """Тест использования Playwright с взаимодействиями."""
    url = "https://example.com"
    context = {}

    with patch("playwright.sync_api.sync_playwright") as mock_playwright:
        # Мокаем успешное взаимодействие
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.content.return_value = "<html>Success</html>"
        mock_browser.new_page.return_value = mock_page
        mock_playwright.return_value.chromium.launch.return_value = mock_browser

        strategy_name = strategy_discovery._try_playwright_with_interactions(url, context)

        assert strategy_name is not None
        assert strategy_name.startswith("playwright_interactive_")


def test_try_proxy_combinations(strategy_discovery):
    """Тест комбинаций прокси и заголовков."""
    url = "https://example.com"
    context = {}

    with patch("requests.get") as mock_get:
        # Первые комбинации не сработают
        mock_get.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            MagicMock(status_code=200, text="<html>Success</html>"),
        ]

        strategy_name = strategy_discovery._try_proxy_combinations(url, context)

        assert strategy_name is not None
        assert strategy_name.startswith("proxy_headers_")


def test_try_geolocation_emulation(strategy_discovery):
    """Тест эмуляции геолокации."""
    url = "https://example.com"
    context = {}

    with patch("playwright.sync_api.sync_playwright") as mock_playwright:
        # Мокаем успешную эмуляцию геолокации
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        mock_page.content.return_value = "<html>Success</html>"
        mock_context.new_page.return_value = mock_page
        mock_browser.new_context.return_value = mock_context
        mock_playwright.return_value.chromium.launch.return_value = mock_browser

        strategy_name = strategy_discovery._try_geolocation_emulation(url, context)

        assert strategy_name is not None
        assert strategy_name.startswith("geolocation_")


def test_try_viewport_changes(strategy_discovery):
    """Тест изменения разрешения экрана."""
    url = "https://example.com"
    context = {}

    with patch("playwright.sync_api.sync_playwright") as mock_playwright:
        # Мокаем успешное изменение viewport
        mock_browser = MagicMock()
        mock_page = MagicMock()
        mock_page.content.return_value = "<html>Success</html>"
        mock_browser.new_page.return_value = mock_page
        mock_playwright.return_value.chromium.launch.return_value = mock_browser

        strategy_name = strategy_discovery._try_viewport_changes(url, context)

        assert strategy_name is not None
        assert "viewport_" in strategy_name


def test_is_successful_response(strategy_discovery):
    """Тест проверки успешности ответа."""
    # Тест для requests.Response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = "<html>Content</html>"
    assert strategy_discovery._is_successful_response(mock_response) is True

    # Тест для неудачного ответа
    mock_response.status_code = 403
    assert strategy_discovery._is_successful_response(mock_response) is False

    # Тест для пустого ответа
    mock_response.status_code = 200
    mock_response.text = ""
    assert strategy_discovery._is_successful_response(mock_response) is False

    # Тест для Playwright page
    mock_page = MagicMock()
    mock_page.content.return_value = "<html>Content</html>"
    assert strategy_discovery._is_successful_response(mock_page) is True

    # Тест для пустой страницы
    mock_page.content.return_value = ""
    assert strategy_discovery._is_successful_response(mock_page) is False
