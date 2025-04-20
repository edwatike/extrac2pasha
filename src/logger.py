"""
Модуль для логирования.
"""

import os
import sys
from loguru import logger

# Удаляем стандартный обработчик
logger.remove()

# Добавляем обработчик для вывода в файл
logger.add(
    "logs/app.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
    level="INFO",
    rotation="1 day",
    compression="zip",
)

# Добавляем обработчик для вывода в консоль
logger.add(sys.stderr, format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}", level="INFO")
