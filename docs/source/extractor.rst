Модуль extractor
================

Модуль для извлечения ИНН из HTML-страниц.

Возможности:
- Поиск ИНН по различным шаблонам в тексте
- Поддержка ИНН юридических (10 цифр) и физических (12 цифр) лиц
- Проверка валидности ИНН по контрольным суммам
- Поиск в атрибутах HTML-тегов
- Поиск в JSON-данных

Пример использования:
::

    from src.extractor import extract_inn_from_html

    html = '<div>ИНН компании: 7707083893</div>'
    inn = extract_inn_from_html(html)
    print(inn)  # Выведет: 7707083893

.. automodule:: src.extractor
   :members:
   :undoc-members:
   :show-inheritance: 