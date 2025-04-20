"""
Модуль для исследования и открытия новых стратегий обхода защит.
"""

from typing import Optional, Dict, List
import random
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
import requests
from src.logger import logger
from src.protections.strategy_handler import StrategyHandler


class StrategyDiscovery:
    """Класс для исследования новых стратегий обхода защит."""

    def __init__(self, strategy_handler: StrategyHandler):
        self.strategy_handler = strategy_handler
        self.experimental_approaches = [
            self._try_different_user_agents,
            self._try_playwright_with_interactions,
            self._try_proxy_combinations,
            self._try_geolocation_emulation,
            self._try_viewport_changes,
        ]

        # Базовые User-Agent'ы для экспериментов
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
        ]

        # Базовые прокси для экспериментов
        self.proxies = [
            None,  # Без прокси
            {"http": "http://proxy1.example.com:8080"},
            {"http": "http://proxy2.example.com:8080"},
        ]

        # Геолокации для эмуляции
        self.geolocations = [
            {"latitude": 40.7128, "longitude": -74.0060},  # Нью-Йорк
            {"latitude": 51.5074, "longitude": -0.1278},  # Лондон
            {"latitude": 35.6762, "longitude": 139.6503},  # Токио
        ]

        # Разрешения экрана для тестирования
        self.viewports = [
            {"width": 1920, "height": 1080},
            {"width": 1366, "height": 768},
            {"width": 1536, "height": 864},
        ]

    def discover_new_strategy(self, url: str, context: Dict) -> Optional[str]:
        """
        Исследует новые стратегии обхода защит.

        Args:
            url: URL для исследования
            context: Контекст запроса

        Returns:
            Optional[str]: Название найденной стратегии или None
        """
        logger.log_event("strategy_discovery", "start", {"url": url, "context": context})

        # Перебираем экспериментальные подходы
        for approach in self.experimental_approaches:
            try:
                strategy_name = approach(url, context)
                if strategy_name:
                    logger.log_event(
                        "strategy_discovery",
                        "success",
                        {"url": url, "strategy": strategy_name, "approach": approach.__name__},
                    )
                    return strategy_name
            except Exception as e:
                logger.log_event(
                    "strategy_discovery",
                    "error",
                    {"url": url, "approach": approach.__name__, "error": str(e)},
                )

        logger.log_event("strategy_discovery", "failure", {"url": url, "context": context})
        return None

    def _try_different_user_agents(self, url: str, context: Dict) -> Optional[str]:
        """Пробует разные User-Agent'ы."""
        for user_agent in self.user_agents:
            try:
                headers = {**context.get("headers", {}), "User-Agent": user_agent}
                response = requests.get(url, headers=headers, timeout=30)

                if self._is_successful_response(response):
                    strategy_name = f"custom_user_agent_{hash(user_agent)}"
                    self.strategy_handler.save_strategy(
                        strategy_name, {"headers": {"User-Agent": user_agent}}, "custom_user_agent"
                    )
                    return strategy_name
            except Exception as e:
                logger.log_event(
                    "strategy_discovery",
                    "error",
                    {"url": url, "approach": "user_agent", "error": str(e)},
                )
        return None

    def _try_playwright_with_interactions(self, url: str, context: Dict) -> Optional[str]:
        """Пробует Playwright с различными взаимодействиями."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                # Устанавливаем случайный viewport
                viewport = random.choice(self.viewports)
                page.set_viewport_size(viewport)

                # Добавляем случайные задержки
                page.goto(url, wait_until="networkidle")
                time.sleep(random.uniform(1, 3))

                # Имитируем прокрутку
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(random.uniform(0.5, 1.5))

                # Имитируем клики
                page.mouse.click(
                    random.randint(0, viewport["width"]), random.randint(0, viewport["height"])
                )

                if self._is_successful_response(page):
                    strategy_name = (
                        f"playwright_interactive_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    )
                    self.strategy_handler.save_strategy(
                        strategy_name,
                        {
                            "viewport": viewport,
                            "interactions": ["scroll", "click"],
                            "delays": [1, 3],
                        },
                        "playwright_interactive",
                    )
                    return strategy_name
            except Exception as e:
                logger.log_event(
                    "strategy_discovery",
                    "error",
                    {"url": url, "approach": "playwright", "error": str(e)},
                )
            finally:
                browser.close()
        return None

    def _try_proxy_combinations(self, url: str, context: Dict) -> Optional[str]:
        """Пробует комбинации прокси и заголовков."""
        for proxy in self.proxies:
            for user_agent in self.user_agents:
                try:
                    headers = {**context.get("headers", {}), "User-Agent": user_agent}
                    response = requests.get(url, headers=headers, proxies=proxy, timeout=30)

                    if self._is_successful_response(response):
                        strategy_name = f"proxy_headers_{hash(str(proxy) + user_agent)}"
                        self.strategy_handler.save_strategy(
                            strategy_name, {"headers": headers, "proxies": proxy}, "proxy_headers"
                        )
                        return strategy_name
                except Exception as e:
                    logger.log_event(
                        "strategy_discovery",
                        "error",
                        {"url": url, "approach": "proxy_headers", "error": str(e)},
                    )
        return None

    def _try_geolocation_emulation(self, url: str, context: Dict) -> Optional[str]:
        """Пробует эмуляцию геолокации через Playwright."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                geolocation=random.choice(self.geolocations), locale="en-US"
            )
            page = context.new_page()

            try:
                page.goto(url, wait_until="networkidle")

                if self._is_successful_response(page):
                    strategy_name = f"geolocation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    self.strategy_handler.save_strategy(
                        strategy_name,
                        {"geolocation": page.context.geolocation, "locale": "en-US"},
                        "geolocation",
                    )
                    return strategy_name
            except Exception as e:
                logger.log_event(
                    "strategy_discovery",
                    "error",
                    {"url": url, "approach": "geolocation", "error": str(e)},
                )
            finally:
                browser.close()
        return None

    def _try_viewport_changes(self, url: str, context: Dict) -> Optional[str]:
        """Пробует разные разрешения экрана."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)

            for viewport in self.viewports:
                try:
                    page = browser.new_page()
                    page.set_viewport_size(viewport)
                    page.goto(url, wait_until="networkidle")

                    if self._is_successful_response(page):
                        strategy_name = f"viewport_{viewport['width']}x{viewport['height']}"
                        self.strategy_handler.save_strategy(
                            strategy_name, {"viewport": viewport}, "viewport"
                        )
                        return strategy_name
                except Exception as e:
                    logger.log_event(
                        "strategy_discovery",
                        "error",
                        {"url": url, "approach": "viewport", "error": str(e)},
                    )
            browser.close()
        return None

    def _is_successful_response(self, response) -> bool:
        """Проверяет успешность ответа."""
        if isinstance(response, requests.Response):
            return response.status_code == 200 and len(response.text) > 0
        else:  # Playwright page
            return len(response.content()) > 0
