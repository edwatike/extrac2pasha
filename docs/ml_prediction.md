# ML-прогнозирование стратегий

## Обзор

Модуль ML-прогнозирования стратегий использует машинное обучение для выбора оптимальных стратегий обхода защит на основе исторических данных и контекста запроса.

## Архитектура

### Признаки (Features)

Модель использует следующие признаки для предсказания:

1. `protection_type` (категориальный)
   - Тип защиты (cloudflare, ddos-guard, и т.д.)

2. `user_agent_hash` (категориальный)
   - Хэшированная строка user-agent

3. `has_captcha` (bool)
   - Наличие капчи на странице

4. `html_title_keywords` (массив)
   - Ключевые слова из заголовка страницы

5. `ip_region` (категориальный)
   - Регион IP-адреса (RU, US, CN, и т.д.)

6. `url_depth` (числовой)
   - Глубина вложенности URL

7. `time_of_day` (категориальный)
   - Время суток (утро, день, ночь)

### Модель

- Алгоритм: RandomForestClassifier
- Формат сохранения: pickle
- Путь к модели: `models/strategy_model.pkl`

## Обучение модели

### Подготовка данных

1. Соберите данные в CSV-файл `data/strategy_logs.csv`:
```csv
protection_type,user_agent_hash,has_captcha,html_title_keywords,ip_region,url_depth,time_of_day,strategy_name
cloudflare,hash1,true,"verify,security",RU,2,morning,strategy1
ddos-guard,hash2,false,"access,denied",US,1,evening,strategy2
```

2. Запустите обучение:
```bash
python src/train_predictor.py
```

### Анализ данных

Для анализа данных и важности признаков используйте Jupyter Notebook:
```bash
jupyter notebook notebooks/strategy_analysis.ipynb
```

## Использование

### В коде

```python
from src.protections.strategy_predictor import StrategyPredictor

# Создаем предсказатель
predictor = StrategyPredictor()

# Подготавливаем контекст
context = {
    'protection_type': 'cloudflare',
    'user_agent_hash': 'hash123',
    'has_captcha': True,
    'html_title_keywords': ['verify', 'security'],
    'ip_region': 'RU',
    'url_depth': 2,
    'time_of_day': 'morning'
}

# Получаем предсказание
strategy = predictor.predict_best_strategy(context)
```

### Интеграция с StrategySelector

StrategySelector автоматически использует ML-предсказание, если доступна обученная модель:

```python
from src.protections.strategy_selector import StrategySelector

selector = StrategySelector()
best_strategy = selector.get_best_strategy('cloudflare', context=context)
```

## Расширение

### Добавление новых признаков

1. Добавьте новый признак в `StrategyPredictor.feature_names`
2. Обновите логику подготовки данных в `train_predictor.py`
3. Переобучите модель

### Использование Deep Learning

Архитектура модуля позволяет легко заменить RandomForest на нейронную сеть:

1. Создайте новый класс модели
2. Реализуйте методы `predict` и `fit`
3. Обновите `StrategyPredictor` для работы с новой моделью

## Мониторинг

- Логи обучения сохраняются в `logs/training.log`
- Метрики модели доступны в Jupyter Notebook
- Статистика использования ML-предсказаний доступна через логгер

## Будущие улучшения

1. Online-learning для адаптации к новым данным
2. A/B тестирование разных моделей
3. Автоматический сбор фидбека для улучшения предсказаний
4. Интеграция с системой мониторинга производительности 