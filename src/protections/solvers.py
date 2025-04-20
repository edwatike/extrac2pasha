"""
Модуль содержит функции-обходчики для различных типов защит веб-сайтов.
Каждая функция реализует конкретную стратегию обхода защиты.
"""

import time
import random
import logging
from typing import Optional, Dict, Any
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import requests
from src.logger import setup_logger

logger = setup_logger(__name__)


def solve_with_playwright(url: str, timeout: int = 30000, **kwargs) -> Optional[str]:
    """
    Открывает страницу в headless-браузере, дожидается полного рендера и возвращает HTML.

    Args:
        url: URL страницы для обхода
        timeout: таймаут ожидания загрузки страницы в миллисекундах
        **kwargs: дополнительные параметры для playwright (например, user_agent)

    Returns:
        str: HTML страницы или None в случае ошибки
    """
    logger.info(f"Попытка обхода защиты через playwright для {url}")

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()

            if "user_agent" in kwargs:
                context.set_extra_http_headers({"User-Agent": kwargs["user_agent"]})

            page = context.new_page()
            page.goto(url, timeout=timeout)

            # Ждем полной загрузки страницы
            page.wait_for_load_state("networkidle")

            html = page.content()
            browser.close()

            logger.info(f"Успешно получен HTML через playwright для {url}")
            return html

    except PlaywrightTimeoutError:
        logger.error(f"Таймаут при загрузке страницы {url} через playwright")
    except Exception as e:
        logger.error(f"Ошибка при обходе через playwright для {url}: {str(e)}")

    return None


def solve_with_headers_tweaking(url: str, **kwargs) -> Optional[str]:
    """
    Отправляет запрос с модифицированными заголовками.

    Args:
        url: URL страницы для обхода
        **kwargs: дополнительные параметры для заголовков

    Returns:
        str: HTML страницы или None в случае ошибки
    """
    logger.info(f"Попытка обхода защиты через модификацию заголовков для {url}")

    headers = {
        "User-Agent": kwargs.get(
            "user_agent",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }

    if "referer" in kwargs:
        headers["Referer"] = kwargs["referer"]

    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        logger.info(f"Успешно получен HTML через модификацию заголовков для {url}")
        return response.text

    except requests.RequestException as e:
        logger.error(f"Ошибка при обходе через модификацию заголовков для {url}: {str(e)}")

    return None


def solve_with_proxy(url: str, proxy: Dict[str, str], **kwargs) -> Optional[str]:
    """
    Делает запрос через внешний прокси.

    Args:
        url: URL страницы для обхода
        proxy: словарь с параметрами прокси (scheme, host, port, username, password)
        **kwargs: дополнительные параметры

    Returns:
        str: HTML страницы или None в случае ошибки
    """
    logger.info(f"Попытка обхода защиты через прокси для {url}")

    proxy_url = f"{proxy['scheme']}://"
    if "username" in proxy and "password" in proxy:
        proxy_url += f"{proxy['username']}:{proxy['password']}@"
    proxy_url += f"{proxy['host']}:{proxy['port']}"

    proxies = {"http": proxy_url, "https": proxy_url}

    try:
        response = requests.get(url, proxies=proxies, timeout=30)
        response.raise_for_status()

        logger.info(f"Успешно получен HTML через прокси для {url}")
        return response.text

    except requests.RequestException as e:
        logger.error(f"Ошибка при обходе через прокси для {url}: {str(e)}")

    return None


def solve_with_retry_and_delay(url: str, max_retries: int = 3, **kwargs) -> Optional[str]:
    """
    Повторяет запрос через случайные интервалы времени.

    Args:
        url: URL страницы для обхода
        max_retries: максимальное количество попыток
        **kwargs: дополнительные параметры

    Returns:
        str: HTML страницы или None в случае ошибки
    """
    logger.info(f"Попытка обхода защиты через повторные запросы для {url}")

    for attempt in range(max_retries):
        try:
            # Случайная задержка от 5 до 10 секунд
            delay = random.uniform(5, 10)
            logger.info(f"Попытка {attempt + 1}/{max_retries}, ожидание {delay:.2f} секунд")
            time.sleep(delay)

            response = requests.get(url, timeout=30)
            response.raise_for_status()

            logger.info(f"Успешно получен HTML после {attempt + 1} попытки для {url}")
            return response.text

        except requests.RequestException as e:
            logger.warning(f"Попытка {attempt + 1} не удалась для {url}: {str(e)}")
            if attempt == max_retries - 1:
                logger.error(f"Все попытки обхода защиты не удались для {url}")

    return None
