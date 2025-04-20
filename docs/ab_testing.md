# A/B Тестирование стратегий

## Обзор

Модуль A/B тестирования позволяет сравнивать эффективность ML и Rule-Based подходов к выбору стратегий обхода защиты.

## Как работает выбор стратегий

### Распределение трафика

- С вероятностью 50% выбирается ML-стратегия
- С вероятностью 50% выбирается Rule-Based стратегия

### Процесс выбора

1. **ML-стратегия**
   - Использует `StrategyPredictor`
   - Учитывает контекст запроса
   - Предсказывает оптимальную стратегию

2. **Rule-Based стратегия**
   - Использует `StrategySelector`
   - Основан на статистике успешности
   - Выбирает наиболее эффективную стратегию

## Логирование результатов

### Формат данных

Результаты сохраняются в `data/ab_test_results.csv`:

```csv
timestamp,strategy_name,method,success,duration,protection_type,url,ip_region,user_agent,has_captcha
2024-01-01T12:00:00,playwright_interactive,ML,true,3.21,cloudflare,https://example.com,RU,chrome_91,false
```

### Поля лога

- `timestamp`: Время применения стратегии
- `strategy_name`: Название выбранной стратегии
- `method`: Метод выбора ("ML" или "RuleBased")
- `success`: Успешность применения
- `duration`: Время выполнения в секундах
- `protection_type`: Тип защиты
- `url`: URL запроса
- `ip_region`: Регион IP
- `user_agent`: User-Agent
- `has_captcha`: Наличие капчи

## Анализ результатов

### Метрики

Для каждого метода вычисляются:
- Общее количество применений
- Процент успешных обходов
- Среднее время выполнения

### Пример анализа

```python
import pandas as pd

# Загрузка данных
df = pd.read_csv('data/ab_test_results.csv')

# Статистика по методам
ml_stats = df[df['method'] == 'ML']
rule_stats = df[df['method'] == 'RuleBased']

print(f"ML успешность: {ml_stats['success'].mean():.2%}")
print(f"RuleBased успешность: {rule_stats['success'].mean():.2%}")
```

### Визуализация

```python
import matplotlib.pyplot as plt

# График успешности по времени
df.groupby(['timestamp', 'method'])['success'].mean().unstack().plot()
plt.title('Успешность стратегий по времени')
plt.show()
```

## Рекомендации по анализу

1. **Достаточность данных**
   - Минимум 1000 применений каждого метода
   - Равномерное распределение по типам защиты

2. **Статистическая значимость**
   - Используйте t-тест для сравнения успешности
   - Учитывайте доверительные интервалы

3. **Анализ по подгруппам**
   - Разделяйте данные по типам защиты
   - Анализируйте эффективность в разных регионах

## Интеграция

### Использование в коде

```python
from src.evaluation.ab_tester import ABTester

tester = ABTester()

# Выбор стратегии
strategy, method = tester.select_strategy(
    protection_type="cloudflare",
    context={"url": "https://example.com"}
)

# Логирование результата
tester.log_result(
    strategy_name=strategy,
    method=method,
    success=True,
    duration=3.21,
    metadata={
        "protection_type": "cloudflare",
        "url": "https://example.com",
        "ip_region": "RU"
    }
)
```

### Мониторинг

- Регулярно проверяйте статистику
- Следите за изменением эффективности
- Анализируйте причины неудач 