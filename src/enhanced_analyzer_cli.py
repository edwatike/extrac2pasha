"""
CLI утилита для запуска анализатора сайтов.
"""

import asyncio
import argparse
from pathlib import Path
from src.enhanced_site_analyzer import EnhancedSiteAnalyzer
from src.logger import logger
from typing import List


async def analyze_site(url: str, output_dir: str) -> None:
    """
    Анализирует сайт и сохраняет результаты.

    Args:
        url: URL для анализа
        output_dir: Директория для сохранения результатов
    """
    try:
        async with EnhancedSiteAnalyzer(output_dir) as analyzer:
            result = await analyzer.analyze(url)
            logger.info(f"Анализ {url} завершен успешно")
            logger.info(f"Найдено {len(result['categories'])} категорий")
            logger.info(f"Найдено {len(result['products'])} продуктов")
            logger.info(f"Найдено {len(result['links'])} ссылок")
    except Exception as e:
        logger.error(f"Ошибка при анализе {url}: {e}")


async def analyze_multiple_sites(urls: List[str], output_dir: str) -> None:
    """
    Анализирует несколько сайтов параллельно.

    Args:
        urls: Список URL для анализа
        output_dir: Директория для сохранения результатов
    """
    tasks = [analyze_site(url, output_dir) for url in urls]
    await asyncio.gather(*tasks)


def main():
    """Основная функция CLI."""
    parser = argparse.ArgumentParser(description="Анализатор структуры веб-сайтов")
    parser.add_argument("urls", nargs="+", help="URL сайтов для анализа")
    parser.add_argument(
        "--output-dir", "-o", default="data", help="Директория для сохранения результатов"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Подробный вывод")

    args = parser.parse_args()

    # Создаем директорию для результатов
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Настраиваем уровень логирования
    if args.verbose:
        logger.setLevel("DEBUG")
    else:
        logger.setLevel("INFO")

    # Запускаем анализ
    asyncio.run(analyze_multiple_sites(args.urls, str(output_dir)))


if __name__ == "__main__":
    main()
