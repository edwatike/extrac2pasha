Модуль logger
=============

Модуль для логирования событий в JSON-формате.

Формат лога:
- timestamp: время события в ISO формате
- event: тип события
- дополнительные поля в зависимости от события

Основные типы событий:
- protection_detection: обнаружение защиты
- strategies_loaded: загрузка стратегий
- strategy_saved: сохранение стратегии
- strategy_failed: ошибка применения стратегии
- inn_extraction_started: начало извлечения ИНН
- inn_extracted: успешное извлечение ИНН
- inn_not_found: ИНН не найден

Пример записи в логе:
::

    {
        "timestamp": "2024-02-20T15:30:00",
        "event": "inn_extracted",
        "inn": "7707083893",
        "pattern_used": "ИНН\\s*[:：]?\\s*(\\d{10,12})"
    }

.. automodule:: src.logger
   :members:
   :undoc-members:
   :show-inheritance: 