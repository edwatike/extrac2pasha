import re
from typing import Optional
from bs4 import BeautifulSoup
from logger import log_event

def extract_inn_from_html(html: str) -> Optional[str]:
    """
    Извлекает ИНН из HTML-кода страницы.
    
    Args:
        html: HTML-код страницы
        
    Returns:
        Optional[str]: Найденный ИНН или None, если ИНН не найден
    """
    # Логируем начало извлечения
    log_event({
        "event": "inn_extraction_started",
        "html_length": len(html)
    })
    
    # Парсим HTML
    soup = BeautifulSoup(html, 'html.parser')
    
    # Удаляем скрипты и стили
    for script in soup(["script", "style"]):
        script.decompose()
    
    # Получаем чистый текст
    text = soup.get_text()
    
    # Паттерны для поиска ИНН
    patterns = [
        # Стандартные форматы
        r'ИНН\s*[:：]?\s*(\d{10,12})',
        r'ИНН&nbsp;(\d{10,12})',
        r'ИНН\s+(\d{10,12})',
        r'ИНН\s*=\s*(\d{10,12})',
        r'ИНН/КПП\s*[:：]?\s*(\d{10,12})',
        r'Идентификационный номер\s*[:：]?\s*(\d{10,12})',
        r'ИНН организации\s*[:：]?\s*(\d{10,12})',
        r'ИНН компании\s*[:：]?\s*(\d{10,12})',
        r'ИНН\s*\((\d{10,12})\)',
        r'ИНН\s*№\s*(\d{10,12})',
        
        # Дополнительные форматы
        r'ИНН.*?(\d{10})',
        r'ИНН.*?(\d{12})',
        r'инн.*?(\d{10})',
        r'инн.*?(\d{12})',
        r'ИНН\s*[^0-9]{0,20}(\d{10})',
        r'ИНН\s*[^0-9]{0,20}(\d{12})',
        
        # Поиск в реквизитах
        r'реквизиты.*?ИНН.*?(\d{10,12})',
        r'реквизиты.*?инн.*?(\d{10,12})',
        r'огрн.*?инн.*?(\d{10,12})',
        r'ОГРН.*?ИНН.*?(\d{10,12})',
        
        # Поиск в контактах
        r'контакты.*?ИНН.*?(\d{10,12})',
        r'контакты.*?инн.*?(\d{10,12})',
        
        # Поиск в JSON-данных
        r'"inn"\s*:\s*"(\d{10,12})"',
        r'"ИНН"\s*:\s*"(\d{10,12})"',
        r'"inn"\s*:\s*(\d{10,12})',
        r'"ИНН"\s*:\s*(\d{10,12})'
    ]
    
    # Ищем ИНН в тексте
    for pattern in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
        for match in matches:
            inn = match.group(1)
            
            # Проверяем валидность ИНН
            if len(inn) in [10, 12] and is_valid_inn(inn):
                # Логируем успешное извлечение
                log_event({
                    "event": "inn_extracted",
                    "inn": inn,
                    "pattern_used": pattern
                })
                
                return inn
    
    # Ищем ИНН в атрибутах HTML
    for tag in soup.find_all(['div', 'span', 'p', 'td']):
        for attr in ['data-inn', 'data-tax-id', 'data-company-inn', 'inn']:
            if attr in tag.attrs:
                inn = tag[attr]
                if re.match(r'^\d{10,12}$', inn) and is_valid_inn(inn):
                    log_event({
                        "event": "inn_extracted",
                        "inn": inn,
                        "source": f"HTML attribute: {attr}"
                    })
                    return inn
    
    # Логируем неудачное извлечение
    log_event({
        "event": "inn_not_found",
        "error": "ИНН не найден в HTML"
    })
    
    return None

def is_valid_inn(inn: str) -> bool:
    """
    Проверяет валидность ИНН по контрольным суммам.
    
    Args:
        inn: ИНН для проверки
        
    Returns:
        bool: True если ИНН валиден, False если нет
    """
    if not inn.isdigit():
        return False
        
    if len(inn) == 10:  # ИНН юридического лица
        weights = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        control_sum = sum(int(inn[i]) * weights[i] for i in range(9))
        control_digit = control_sum % 11 % 10
        return int(inn[9]) == control_digit
        
    elif len(inn) == 12:  # ИНН физического лица
        weights1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        weights2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        
        control_sum1 = sum(int(inn[i]) * weights1[i] for i in range(10))
        control_sum2 = sum(int(inn[i]) * weights2[i] for i in range(11))
        
        control_digit1 = control_sum1 % 11 % 10
        control_digit2 = control_sum2 % 11 % 10
        
        return int(inn[10]) == control_digit1 and int(inn[11]) == control_digit2
        
    return False
