import json
import datetime
from typing import Dict, Any

def log_event(data: Dict[str, Any]) -> None:
    """
    Записывает событие в лог-файл в формате JSON.
    
    Args:
        data: Словарь с данными события. Должен содержать обязательные поля:
            - timestamp: время события
            - url: URL страницы
            - protection_detected: тип обнаруженной защиты
            - strategy_used: использованная стратегия
            - inn_extracted: извлеченный ИНН
            - error: описание ошибки (если есть)
    """
    # Добавляем временную метку, если её нет
    if 'timestamp' not in data:
        data['timestamp'] = datetime.datetime.now().isoformat()
    
    # Записываем событие в лог-файл
    with open('log.txt', 'a', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)
        f.write('\n')
