import asyncio
from protections import detect_protection, apply_strategy, get_strategy
from extractor import extract_inn_from_html
from logger import log_event

TEST_SITES = [
    "https://cvetmetall.ru",
    "https://www.kirelis.ru",
    "https://medexe.ru",
    "https://mc.ru",
    "https://www.metallotorg.ru"
]

async def test_site(url: str):
    """Тестирует обход защиты на конкретном сайте"""
    log_event({
        "event": "site_test_started",
        "url": url
    })
    
    # Пробуем получить страницу без защиты
    strategy = get_strategy("none")
    html = apply_strategy(url, strategy)
    
    if html:
        # Определяем тип защиты
        protection_type = detect_protection(html)
        log_event({
            "event": "protection_detected",
            "url": url,
            "protection_type": protection_type
        })
        
        # Если есть защита, пробуем обойти её
        if protection_type != "none":
            strategy = get_strategy(protection_type)
            if strategy:
                html = apply_strategy(url, strategy)
        
        # Если получили HTML, пробуем извлечь ИНН
        if html:
            inn = extract_inn_from_html(html)
            log_event({
                "event": "inn_extraction_result",
                "url": url,
                "inn": inn,
                "success": inn is not None
            })
            return inn
    
    log_event({
        "event": "site_test_failed",
        "url": url
    })
    return None

async def main():
    """Тестирует все сайты"""
    results = {}
    for url in TEST_SITES:
        inn = await test_site(url)
        results[url] = inn
    
    # Выводим результаты
    print("\nРезультаты тестирования:")
    for url, inn in results.items():
        status = "УСПЕХ" if inn else "НЕУДАЧА"
        print(f"{url}: {status}")
        if inn:
            print(f"Найден ИНН: {inn}")
        print()

if __name__ == "__main__":
    asyncio.run(main()) 