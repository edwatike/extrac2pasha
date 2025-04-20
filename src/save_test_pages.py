import os
import asyncio
import traceback
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
    print(f"\nОбработка сайта: {url}")
    
    # Создаем имя файла из URL
    filename = url.replace("https://", "").replace("http://", "").replace("/", "_")
    filepath = os.path.join("src/test_html", f"{filename}.html")
    
    # Пробуем разные стратегии
    strategies = [
        ("none", get_strategy("none")),
        ("cloudflare", get_strategy("cloudflare")),
        ("js_challenge", get_strategy("js_challenge")),
        ("playwright", get_strategy("captcha"))  # Пробуем Playwright как запасной вариант
    ]
    
    for strategy_name, strategy in strategies:
        if not strategy:
            print(f"Стратегия {strategy_name} не найдена")
            continue
            
        print(f"Пробуем стратегию: {strategy_name}")
        log_event({
            "event": "saving_page_attempt",
            "url": url,
            "strategy": strategy["method"]
        })
        
        try:
            html = apply_strategy(url, strategy)
            if html:
                print(f"Получен HTML длиной {len(html)} байт")
                
                # Сохраняем HTML
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(html)
                
                print(f"Страница сохранена в {filepath}")
                log_event({
                    "event": "page_saved",
                    "url": url,
                    "file": filepath,
                    "strategy": strategy["method"],
                    "html_length": len(html)
                })
                return True
            else:
                print(f"Стратегия {strategy_name} не вернула HTML")
                
        except Exception as e:
            print(f"Ошибка при использовании стратегии {strategy_name}:")
            print(traceback.format_exc())
            log_event({
                "event": "strategy_error",
                "url": url,
                "strategy": strategy["method"],
                "error": str(e),
                "traceback": traceback.format_exc()
            })
    
    print(f"Не удалось сохранить страницу {url}")
    log_event({
        "event": "page_save_failed",
        "url": url
    })
    return False

async def main():
    """Сохраняет страницы со всех тестовых сайтов"""
    # Создаем директорию, если её нет
    os.makedirs("src/test_html", exist_ok=True)
    
    results = []
    for url in TEST_SITES:
        success = await save_page(url)
        results.append((url, success))
    
    # Выводим общий результат
    print("\nИтоговые результаты:")
    for url, success in results:
        status = "УСПЕХ" if success else "НЕУДАЧА"
        print(f"{url}: {status}")

if __name__ == "__main__":
    asyncio.run(main()) 