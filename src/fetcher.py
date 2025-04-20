import requests
import time
from typing import Optional
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from logger import log_event

def fetch_html(url: str) -> Optional[str]:
    """
    Загружает HTML с сайта, обходя различные типы защиты.
    
    Args:
        url: URL сайта
        
    Returns:
        Optional[str]: HTML-код страницы или None в случае ошибки
    """
    # Сразу используем Selenium для всех сайтов
    return fetch_with_selenium(url)

def fetch_with_selenium(url: str) -> Optional[str]:
    """
    Загружает HTML с сайта с использованием Selenium и undetected-chromedriver.
    
    Args:
        url: URL сайта
        
    Returns:
        Optional[str]: HTML-код страницы или None в случае ошибки
    """
    try:
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Добавляем дополнительные заголовки
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
        
        driver = uc.Chrome(options=options)
        
        # Устанавливаем таймауты
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(10)
        
        # Загружаем страницу
        driver.get(url)
        
        # Ждем загрузки страницы
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Даем время на выполнение JavaScript
        time.sleep(5)
        
        # Прокручиваем страницу для загрузки динамического контента
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Пытаемся найти ссылки на страницы с контактами
        contact_links = []
        try:
            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href")
                text = link.text.lower()
                if href and any(keyword in text for keyword in ["контакт", "о компании", "реквизит"]):
                    contact_links.append(href)
        except:
            pass
        
        # Собираем HTML со всех найденных страниц
        all_html = [driver.page_source]
        
        for link in contact_links[:3]:  # Ограничиваем количество дополнительных страниц
            try:
                driver.get(link)
                time.sleep(3)
                all_html.append(driver.page_source)
            except:
                continue
        
        driver.quit()
        
        log_event({
            "event": "html_fetched",
            "url": url,
            "method": "selenium",
            "additional_pages": len(all_html) - 1
        })
        
        return "\n".join(all_html)
        
    except Exception as e:
        log_event({
            "event": "selenium_error",
            "url": url,
            "error": str(e)
        })
        return None 