import os
import asyncio
from protections import apply_strategy, get_strategy
from logger import log_event

TEST_SITES = [
    "https://cvetmetall.ru",
    "https://www.kirelis.ru",
    "https://medexe.ru",
    "https://mc.ru",
    "https://www.metallotorg.ru"
]

async def save_page(url: str):
    """Сохраняет HTML-страницу в файл"""
    # Создаем имя файла из URL
    filename = url.replace("https://", "").replace("http://", "").replace("/", "_")
    filepath = os.path.join("src/test_html", f"{filename}.html")
    
    # Пробуем разные стратегии
    strategies = [
        get_strategy("none"),
        get_strategy("cloudflare"),
        get_strategy("js_challenge")
    ]
    
    for strategy in strategies:
        if not strategy:
            continue
            
        log_event({
            "event": "saving_page_attempt",
            "url": url,
            "strategy": strategy["method"]
        })
        
        html = apply_strategy(url, strategy)
        if html:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
            
            log_event({
                "event": "page_saved",
                "url": url,
                "file": filepath,
                "strategy": strategy["method"]
            })
            return True
    
    log_event({
        "event": "page_save_failed",
        "url": url
    })
    return False

async def main():
    """Сохраняет страницы со всех тестовых сайтов"""
    for url in TEST_SITES:
        await save_page(url)

if __name__ == "__main__":
    asyncio.run(main()) 