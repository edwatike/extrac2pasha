"""
Модуль для анализа структуры веб-сайтов и извлечения данных.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from playwright.async_api import async_playwright, Browser, Page
from src.logger import logger


class EnhancedSiteAnalyzer:
    """Класс для анализа структуры веб-сайтов."""

    def __init__(self, output_dir: str = "data"):
        """
        Инициализация анализатора.

        Args:
            output_dir: Директория для сохранения результатов
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.browser: Optional[Browser] = None
        self.request_log: List[Dict] = []

    async def __aenter__(self):
        """Создает браузер при входе в контекст."""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=True)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Закрывает браузер при выходе из контекста."""
        if self.browser:
            await self.browser.close()

    async def analyze(self, url: str) -> Dict:
        """
        Анализирует структуру сайта.

        Args:
            url: URL для анализа

        Returns:
            Dict: Результаты анализа
        """
        try:
            if not self.browser:
                raise RuntimeError("Браузер не инициализирован")

            page = await self.browser.new_page()

            # Настраиваем перехват запросов
            await page.route("**/*", self._log_request)

            # Загружаем страницу
            await page.goto(url, wait_until="networkidle")

            # Извлекаем структуру
            structure = await self._extract_structure(page)

            # Извлекаем категории
            categories = await self._extract_categories(page)

            # Извлекаем продукты
            products = await self._extract_products(page)

            # Извлекаем ссылки
            links = await self._extract_links(page)

            # Формируем результат
            result = {
                "url": url,
                "title": await page.title(),
                "structure": structure,
                "categories": categories,
                "products": products,
                "links": links,
                "request_log": self.request_log,
                "timestamp": datetime.now().isoformat(),
            }

            # Сохраняем результат
            await self._save_result(result)

            return result

        except Exception as e:
            logger.error(f"Ошибка анализа {url}: {e}")
            raise

    async def _log_request(self, route, request):
        """Логирует информацию о запросе."""
        self.request_log.append(
            {
                "url": request.url,
                "method": request.method,
                "headers": request.headers,
                "timestamp": datetime.now().isoformat(),
            }
        )
        await route.continue_()

    async def _extract_structure(self, page: Page) -> Dict:
        """Извлекает структуру страницы."""
        return {
            "navigation": await self._extract_navigation(page),
            "mainContent": await self._extract_main_content(page),
            "sidebar": await self._extract_sidebar(page),
            "footer": await self._extract_footer(page),
        }

    async def _extract_navigation(self, page: Page) -> List[Dict]:
        """Извлекает навигационное меню."""
        nav_items = await page.query_selector_all("nav a, .nav a, .menu a")
        return [
            {"text": await item.text_content(), "url": await item.get_attribute("href")}
            for item in nav_items
        ]

    async def _extract_main_content(self, page: Page) -> Dict:
        """Извлекает основной контент."""
        main = await page.query_selector("main, .main, #main")
        if main:
            return {"text": await main.text_content(), "html": await main.inner_html()}
        return {}

    async def _extract_sidebar(self, page: Page) -> Dict:
        """Извлекает боковую панель."""
        sidebar = await page.query_selector("aside, .sidebar, #sidebar")
        if sidebar:
            return {"text": await sidebar.text_content(), "html": await sidebar.inner_html()}
        return {}

    async def _extract_footer(self, page: Page) -> Dict:
        """Извлекает подвал."""
        footer = await page.query_selector("footer, .footer, #footer")
        if footer:
            return {"text": await footer.text_content(), "html": await footer.inner_html()}
        return {}

    async def _extract_categories(self, page: Page) -> List[Dict]:
        """Извлекает категории."""
        category_links = await page.query_selector_all(".category, .cat, [class*='category'] a")
        return [
            {"name": await link.text_content(), "url": await link.get_attribute("href")}
            for link in category_links
        ]

    async def _extract_products(self, page: Page) -> List[Dict]:
        """Извлекает продукты."""
        product_elements = await page.query_selector_all(".product, .item, [class*='product']")
        products = []

        for element in product_elements:
            name = await element.query_selector(".name, .title, h3")
            price = await element.query_selector(".price, .cost")
            url = await element.query_selector("a")

            products.append(
                {
                    "name": await name.text_content() if name else "",
                    "price": await price.text_content() if price else "",
                    "url": await url.get_attribute("href") if url else "",
                }
            )

        return products

    async def _extract_links(self, page: Page) -> List[str]:
        """Извлекает все ссылки."""
        links = await page.query_selector_all("a")
        return [
            await link.get_attribute("href") for link in links if await link.get_attribute("href")
        ]

    async def _save_result(self, result: Dict) -> None:
        """Сохраняет результат в JSON файл."""
        filename = f"{result['url'].replace('https://', '').replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"Результаты сохранены в {filepath}")
