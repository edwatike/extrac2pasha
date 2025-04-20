FROM python:3.11-slim

WORKDIR /app

# Установка зависимостей системы
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копирование файлов зависимостей
COPY requirements.txt .
COPY requirements-dev.txt .

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходного кода
COPY src/ src/
COPY tests/ tests/

# Установка браузеров для Playwright
RUN python -m playwright install

# Запуск тестов
CMD ["pytest", "tests/"] 