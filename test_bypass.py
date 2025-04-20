"""
Тестовый скрипт для проверки стратегий обхода защиты.
"""

import asyncio
from src.auto_extractor import AutoExtractor
from src.evaluation.ab_tester import ABTester
from src.logger import logger


async def test_bypass(url: str) -> None:
    """
    Тестирует обход защиты для указанного URL.

    Args:
        url: URL для тестирования
    """
    try:
        logger.info(f"Тестирование обхода для {url}")

        # Создаем экстрактор
        extractor = AutoExtractor()

        # Пробуем извлечь данные
        result = await extractor.extract(
            url=url,
            options={
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "timeout": 30,
            },
        )

        # Выводим результат
        if result["success"]:
            logger.info(f"Успешный обход для {url}")
            logger.info(f"Данные: {result.get('data', 'Нет данных')}")
        else:
            logger.error(f"Ошибка обхода для {url}: {result.get('error', 'Неизвестная ошибка')}")

        # Выводим статистику A/B тестирования
        tester = ABTester()
        stats = tester.get_statistics()
        logger.info(f"Статистика A/B тестирования: {stats}")

    except Exception as e:
        logger.error(f"Ошибка при тестировании {url}: {e}")


async def main():
    """Основная функция тестирования."""
    urls = [
        "https://cvetmetall.ru",
        "https://www.kirelis.ru",
        "https://medexe.ru",
        "https://mc.ru/",
        "https://www.metallotorg.ru",
    ]

    # Тестируем каждый URL
    for url in urls:
        await test_bypass(url)
        await asyncio.sleep(5)  # Пауза между запросами


if __name__ == "__main__":
    asyncio.run(main())
