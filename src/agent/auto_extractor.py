"""
Модуль авто-экстрактора для автоматического обхода защит веб-сайтов.
"""

import os
import json
import argparse
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
import requests
from src.logger import setup_logger
from src.protections import ProtectionDetector
from src.protections.strategy_handler import StrategyHandler

logger = setup_logger(__name__)


class AutoExtractor:
    """Агент для автоматического обхода защит веб-сайтов."""

    def __init__(self, db_path: str = "data/strategies.db"):
        """
        Инициализация авто-экстрактора.

        Args:
            db_path: путь к файлу базы данных SQLite
        """
        self.detector = ProtectionDetector()
        self.handler = StrategyHandler(db_path)

        # Создаем директорию для результатов
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)

        logger.info("Инициализирован AutoExtractor")

    def _detect_protection(self, url: str) -> tuple[bool, Optional[str], Optional[List[str]]]:
        """
        Определяет наличие защиты на странице.

        Args:
            url: URL для проверки

        Returns:
            tuple: (найдена_защита, тип_защиты, признаки_защиты)
        """
        try:
            # Пробуем сделать обычный запрос
            response = requests.get(url, timeout=30)

            # Проверяем признаки защиты
            protection_type, protection_signs = self.detector.detect_protection(response)

            if protection_type:
                logger.info(f"Обнаружена защита {protection_type} на {url}")
                return True, protection_type, protection_signs
            else:
                logger.info(f"Защита не обнаружена на {url}")
                return False, None, None

        except requests.RequestException as e:
            logger.error(f"Ошибка при проверке защиты на {url}: {str(e)}")
            return True, "unknown", ["request_error"]

    def _save_result(self, url: str, html: str, status: str, strategy: Optional[str] = None) -> str:
        """
        Сохраняет результат в файл.

        Args:
            url: URL страницы
            html: полученный HTML
            status: статус операции
            strategy: примененная стратегия

        Returns:
            str: путь к сохраненному файлу
        """
        # Создаем имя файла из URL и timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{url.replace('://', '_').replace('/', '_')}_{timestamp}.json"
        filepath = self.output_dir / filename

        # Формируем данные для сохранения
        data = {
            "url": url,
            "timestamp": timestamp,
            "status": status,
            "strategy": strategy,
            "html": html,
        }

        # Сохраняем в JSON
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"Результат сохранен в {filepath}")
        return str(filepath)

    def run_agent(self, url: str, **kwargs) -> Dict[str, Any]:
        """
        Запускает агента для обработки URL.

        Args:
            url: URL для обработки
            **kwargs: дополнительные параметры

        Returns:
            Dict: результат работы агента
        """
        logger.info(f"Запуск агента для {url}")

        # Проверяем защиту
        has_protection, protection_type, protection_signs = self._detect_protection(url)

        if not has_protection:
            # Если защиты нет, просто получаем HTML
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                html = response.text
                status = "success"
                strategy = None
            except requests.RequestException as e:
                logger.error(f"Ошибка при получении HTML с {url}: {str(e)}")
                html = ""
                status = "error"
                strategy = None
        else:
            # Если защита есть, пробуем стратегии
            html = self.handler.try_strategies(protection_type, protection_signs, url, **kwargs)

            if html:
                status = "success"
                strategy = self.handler.find_strategy(protection_type, protection_signs)
            else:
                status = "error"
                strategy = None

        # Сохраняем результат
        output_file = self._save_result(url, html, status, strategy)

        return {
            "url": url,
            "status": status,
            "strategy": strategy,
            "output_file": output_file,
            "has_protection": has_protection,
            "protection_type": protection_type,
        }


def main():
    """Точка входа для CLI."""
    parser = argparse.ArgumentParser(description="Авто-экстрактор для обхода защит веб-сайтов")
    parser.add_argument("--url", required=True, help="URL для обработки")
    parser.add_argument("--db", default="data/strategies.db", help="Путь к базе данных стратегий")

    args = parser.parse_args()

    extractor = AutoExtractor(args.db)
    result = extractor.run_agent(args.url)

    print(f"Результат обработки {args.url}:")
    print(f"Статус: {result['status']}")
    print(f"Защита: {'да' if result['has_protection'] else 'нет'}")
    if result["strategy"]:
        print(f"Стратегия: {result['strategy']}")
    print(f"Результат сохранен в: {result['output_file']}")


if __name__ == "__main__":
    main()
