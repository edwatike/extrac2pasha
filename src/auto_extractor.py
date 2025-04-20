"""
Модуль для автоматического извлечения данных с учетом защиты.
"""

import asyncio
import aiohttp
from typing import Dict, Optional
from src.protections.strategy_selector import StrategySelector
from src.evaluation.ab_tester import ABTester
from src.logger import logger


class AutoExtractor:
    """Класс для автоматического извлечения данных."""

    def __init__(self):
        """Инициализация экстрактора."""
        self.selector = StrategySelector()
        self.tester = ABTester()
        self.session = None

    async def __aenter__(self):
        """Создает сессию при входе в контекст."""
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрывает сессию при выходе из контекста."""
        if self.session:
            await self.session.close()

    async def extract(self, url: str, options: Optional[Dict] = None) -> Dict:
        """
        Извлекает данные с учетом защиты.

        Args:
            url: URL для извлечения
            options: Дополнительные опции

        Returns:
            Dict: Результат извлечения
        """
        try:
            # Определяем тип защиты
            protection_type = await self._detect_protection(url)

            # Формируем контекст для A/B тестирования
            context = {"url": url, "protection_type": protection_type, "options": options or {}}

            # Выбираем стратегию через A/B тестер
            strategy_name, method = self.tester.select_strategy(
                protection_type=protection_type, context=context
            )

            # Применяем стратегию
            start_time = asyncio.get_event_loop().time()
            result = await self._apply_strategy(strategy_name, url, options)
            duration = asyncio.get_event_loop().time() - start_time

            # Логируем результат
            self.tester.log_result(
                strategy_name=strategy_name,
                method=method,
                success=result.get("success", False),
                duration=duration,
                metadata={
                    "protection_type": protection_type,
                    "url": url,
                    "ip_region": result.get("ip_region", ""),
                    "user_agent": options.get("user_agent", ""),
                    "has_captcha": result.get("has_captcha", False),
                },
            )

            return result

        except Exception as e:
            logger.error(f"Ошибка извлечения данных: {e}")
            return {"success": False, "error": str(e)}

    async def _detect_protection(self, url: str) -> str:
        """
        Определяет тип защиты.

        Args:
            url: URL для проверки

        Returns:
            str: Тип защиты
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            async with self.session.get(url) as response:
                html = await response.text()

                # Проверяем признаки различных защит
                if "cloudflare" in html.lower():
                    return "cloudflare"
                elif "ddos-guard" in html.lower():
                    return "ddos_guard"
                elif "recaptcha" in html.lower():
                    return "recaptcha"
                elif response.status == 403:
                    return "ip_block"
                else:
                    return "unknown"

        except Exception as e:
            logger.error(f"Ошибка определения защиты: {e}")
            return "unknown"

    async def _apply_strategy(
        self, strategy_name: str, url: str, options: Optional[Dict] = None
    ) -> Dict:
        """
        Применяет выбранную стратегию.

        Args:
            strategy_name: Название стратегии
            url: URL для обработки
            options: Дополнительные опции

        Returns:
            Dict: Результат применения
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            # Формируем заголовки
            headers = {
                "User-Agent": options.get(
                    "user_agent",
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }

            # Пробуем получить страницу
            async with self.session.get(
                url, headers=headers, timeout=options.get("timeout", 30)
            ) as response:
                if response.status == 200:
                    html = await response.text()
                    return {
                        "success": True,
                        "data": html,
                        "ip_region": "RU",  # TODO: Определять реальный регион
                        "has_captcha": "recaptcha" in html.lower(),
                    }
                else:
                    return {
                        "success": False,
                        "error": f"HTTP {response.status}",
                        "ip_region": "RU",
                        "has_captcha": False,
                    }

        except Exception as e:
            logger.error(f"Ошибка применения стратегии: {e}")
            return {"success": False, "error": str(e), "ip_region": "RU", "has_captcha": False}
