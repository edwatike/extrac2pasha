import os
from typing import Optional
from extractor import extract_inn_from_html
from protections import detect_protection, load_strategies, save_strategy
from logger import log_event
from fetcher import fetch_html

def process_url(url: str) -> Optional[str]:
    """
    Обрабатывает URL и извлекает ИНН.
    
    Args:
        url: URL сайта
        
    Returns:
        Optional[str]: Извлеченный ИНН или None
    """
    try:
        # Загружаем HTML
        html = fetch_html(url)
        if not html:
            return None
        
        # Определяем тип защиты
        protection_type = detect_protection(html)
        
        # Проверяем наличие стратегии для защиты
        strategies = load_strategies()
        strategy_used = None
        
        for strategy in strategies:
            if strategy["protection_type"] == protection_type:
                strategy_used = strategy["strategy"]
                break
        
        if strategy_used:
            log_event({
                "event": "strategy_applied",
                "url": url,
                "protection_type": protection_type,
                "strategy_used": strategy_used
            })
        else:
            log_event({
                "event": "no_strategy_found",
                "url": url,
                "protection_type": protection_type
            })
            
            # Создаем новую стратегию
            new_strategy = {
                "protection_type": protection_type,
                "strategy": "use_selenium",
                "created_at": "2024-04-20T21:00:00"
            }
            save_strategy(new_strategy)
        
        # Извлекаем ИНН
        inn = extract_inn_from_html(html)
        
        return inn
        
    except Exception as e:
        log_event({
            "event": "processing_error",
            "url": url,
            "error": str(e)
        })
        return None

if __name__ == "__main__":
    # Список URL для проверки
    urls = [
        "https://cvetmetall.ru",
        "https://www.kirelis.ru",
        "https://medexe.ru",
        "https://mc.ru/",
        "https://www.metallotorg.ru"
    ]
    
    print("Начинаем поиск ИНН на сайтах...")
    for url in urls:
        print(f"\nПроверяем {url}")
        inn = process_url(url)
        if inn:
            print(f"Найден ИНН: {inn}")
        else:
            print("ИНН не найден")
