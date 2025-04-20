import json
import os
import re
from typing import Dict, Optional, Any
from datetime import datetime
from logger import log_event
import undetected_chromedriver as uc
from selenium import webdriver
from playwright.sync_api import sync_playwright
import cloudscraper
from fake_useragent import UserAgent
import requests
from stem import Signal
from stem.control import Controller

# Путь к директории скрипта
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def detect_protection(html: str) -> str:
    """
    Определяет тип защиты на странице.
    
    Args:
        html: HTML-код страницы
        
    Returns:
        str: Тип защиты ("captcha", "cloudflare", "403", "js_challenge", "none")
    """
    protection_type = "none"
    
    # Проверяем различные типы защиты
    if re.search(r'captcha|recaptcha|g-recaptcha', html, re.I):
        protection_type = "captcha"
    elif re.search(r'cloudflare|cf-browser-verification', html, re.I):
        protection_type = "cloudflare"
    elif re.search(r'403 Forbidden|Access Denied', html, re.I):
        protection_type = "403"
    elif re.search(r'javascript challenge|js challenge', html, re.I):
        protection_type = "js_challenge"
    
    # Логируем обнаружение защиты
    log_event({
        "event": "protection_detection",
        "protection_detected": protection_type,
        "html_snippet": html[:200]  # Сохраняем начало HTML для анализа
    })
    
    return protection_type

def load_strategies() -> Dict:
    """
    Загружает стратегии обхода защит из файла.
    
    Returns:
        Dict: Словарь со стратегиями
    """
    strategies_path = os.path.join(SCRIPT_DIR, 'strategies.json')
    try:
        with open(strategies_path, 'r', encoding='utf-8') as f:
            strategies = json.load(f)
            print(f"Загружено {len(strategies)} стратегий из {strategies_path}")
    except FileNotFoundError:
        print(f"Файл стратегий не найден: {strategies_path}")
        strategies = []
    except json.JSONDecodeError as e:
        print(f"Ошибка при чтении файла стратегий: {e}")
        strategies = []
    
    log_event({
        "event": "strategies_loaded",
        "strategies_count": len(strategies)
    })
    
    return strategies

def save_strategy(strategy: Dict) -> None:
    """
    Сохраняет новую стратегию в файл.
    
    Args:
        strategy: Словарь с данными стратегии
    """
    strategies_path = os.path.join(SCRIPT_DIR, 'strategies.json')
    strategies = load_strategies()
    strategies.append(strategy)
    
    with open(strategies_path, 'w', encoding='utf-8') as f:
        json.dump(strategies, f, ensure_ascii=False, indent=2)
    
    log_event({
        "event": "strategy_saved",
        "strategy": strategy
    })

def get_strategy(protection_type: str) -> Optional[Dict]:
    """
    Получает стратегию для конкретного типа защиты.
    
    Args:
        protection_type: Тип защиты
        
    Returns:
        Optional[Dict]: Стратегия обхода или None
    """
    strategies = load_strategies()
    for strategy in strategies:
        if strategy["protection_type"] == protection_type:
            return strategy["strategy"]
    return None

def apply_strategy(url: str, strategy: Dict) -> Optional[str]:
    """
    Применяет стратегию обхода защиты.
    
    Args:
        url: URL страницы
        strategy: Стратегия обхода
        
    Returns:
        Optional[str]: HTML-код страницы или None в случае неудачи
    """
    method = strategy["method"]
    params = strategy.get("params", {})
    
    try:
        if method == "selenium":
            return _use_selenium(url, params)
        elif method == "playwright":
            return _use_playwright(url, params)
        elif method == "cloudscraper":
            return _use_cloudscraper(url, params)
        elif method == "rotating_proxy":
            return _use_rotating_proxy(url, params)
        elif method == "undetected_chromedriver":
            return _use_undetected_chromedriver(url, params)
        else:
            raise ValueError(f"Неизвестный метод: {method}")
    except Exception as e:
        log_event({
            "event": "strategy_failed",
            "method": method,
            "error": str(e)
        })
        return None

def _use_selenium(url: str, params: Dict[str, Any]) -> Optional[str]:
    """Использует Selenium для получения страницы"""
    options = webdriver.ChromeOptions()
    if not params.get("js_enabled", True):
        options.add_argument("--disable-javascript")
    
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        if params.get("wait_time", 0) > 0:
            driver.implicitly_wait(params["wait_time"])
        return driver.page_source
    finally:
        driver.quit()

def _use_playwright(url: str, params: Dict[str, Any]) -> Optional[str]:
    """Использует Playwright для получения страницы"""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=not params.get("stealth_mode", False)
        )
        context = browser.new_context()
        page = context.new_page()
        
        try:
            page.goto(url)
            if params.get("wait_time", 0) > 0:
                page.wait_for_timeout(params["wait_time"] * 1000)
            return page.content()
        finally:
            browser.close()

def _use_cloudscraper(url: str, params: Dict[str, Any]) -> Optional[str]:
    """Использует CloudScraper для получения страницы"""
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': params.get('browser_type', 'chrome'),
        }
    )
    
    for _ in range(params.get("retry_count", 1)):
        try:
            response = scraper.get(url)
            if response.status_code == 200:
                return response.text
        except Exception:
            continue
    return None

def _use_rotating_proxy(url: str, params: Dict[str, Any]) -> Optional[str]:
    """Использует ротацию прокси для получения страницы"""
    ua = UserAgent()
    headers = {'User-Agent': ua.random}
    
    for _ in range(params.get("retry_count", 1)):
        try:
            # Обновляем IP через Tor
            with Controller.from_port(port=9051) as controller:
                controller.authenticate()
                controller.signal(Signal.NEWNYM)
            
            proxies = {
                'http': 'socks5h://localhost:9050',
                'https': 'socks5h://localhost:9050'
            }
            
            response = requests.get(
                url,
                headers=headers,
                proxies=proxies,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.text
                
        except Exception:
            continue
    return None

def _use_undetected_chromedriver(url: str, params: Dict[str, Any]) -> Optional[str]:
    """Использует undetected_chromedriver для получения страницы"""
    options = uc.ChromeOptions()
    options.headless = params.get("headless", False)
    
    driver = uc.Chrome(options=options)
    try:
        driver.get(url)
        if params.get("wait_time", 0) > 0:
            driver.implicitly_wait(params["wait_time"])
        return driver.page_source
    finally:
        driver.quit()

def create_new_strategy(protection_type: str, method: str, params: Dict[str, Any]) -> None:
    """
    Создает новую стратегию обхода защиты.
    
    Args:
        protection_type: Тип защиты
        method: Метод обхода
        params: Параметры метода
    """
    strategy = {
        "protection_type": protection_type,
        "strategy": {
            "method": method,
            "params": params
        },
        "created_at": datetime.now().isoformat()
    }
    
    save_strategy(strategy)
    
    log_event({
        "event": "new_strategy_created",
        "protection_type": protection_type,
        "method": method
    })
