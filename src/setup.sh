#!/bin/bash

# Обновляем список пакетов
sudo apt-get update

# Устанавливаем системные зависимости
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    chromium-browser \
    chromium-chromedriver \
    xvfb \
    curl \
    wget \
    unzip \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev

# Создаем и активируем виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Обновляем pip
pip install --upgrade pip

# Устанавливаем Python-зависимости
pip install -r requirements.txt

# Устанавливаем дополнительные Python-пакеты для работы с прокси и другими инструментами
pip install \
    fake-useragent \
    python-dotenv \
    requests[socks] \
    stem \
    cloudscraper \
    playwright \
    pytest \
    pytest-asyncio

# Устанавливаем Playwright browsers
playwright install chromium

# Создаем директорию для логов
mkdir -p logs

echo "Установка завершена!" 