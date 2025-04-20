"""
FastAPI приложение для предоставления API к авто-экстрактору.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
import logging
from datetime import datetime
from src.agent.auto_extractor import AutoExtractor
from src.logger import setup_logger

# Настройка логгера
logger = setup_logger(__name__)

# Создание FastAPI приложения
app = FastAPI(
    title="Web Protection Bypass API",
    description="API для автоматического обхода защит веб-сайтов",
    version="1.0.0",
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Модели данных
class ExtractionRequest(BaseModel):
    """Модель запроса на извлечение."""

    url: HttpUrl
    options: Optional[Dict[str, Any]] = None


class ExtractionResponse(BaseModel):
    """Модель ответа на запрос извлечения."""

    status: str
    url: str
    strategy_used: Optional[str] = None
    html_snippet: Optional[str] = None
    has_protection: Optional[bool] = None
    protection_type: Optional[str] = None
    output_file: Optional[str] = None
    timestamp: str
    log: List[str] = []


class ErrorResponse(BaseModel):
    """Модель ответа с ошибкой."""

    status: str
    error: str
    timestamp: str


# Создаем экземпляр экстрактора
extractor = AutoExtractor()


@app.post("/extract", response_model=ExtractionResponse, responses={500: {"model": ErrorResponse}})
async def extract(request: ExtractionRequest, background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """
    Извлекает содержимое веб-страницы, обходя защиту при необходимости.

    Args:
        request: запрос на извлечение
        background_tasks: задачи для выполнения в фоне

    Returns:
        Dict: результат извлечения
    """
    try:
        logger.info(f"Получен запрос на извлечение: {request.url}")

        # Запускаем экстрактор
        result = extractor.run_agent(str(request.url), **(request.options or {}))

        # Формируем ответ
        response = {
            "status": "success",
            "url": str(request.url),
            "strategy_used": result.get("strategy"),
            "html_snippet": result.get("html", "")[:500] if result.get("html") else None,
            "has_protection": result.get("has_protection"),
            "protection_type": result.get("protection_type"),
            "output_file": result.get("output_file"),
            "timestamp": datetime.now().isoformat(),
            "log": [],  # Здесь можно добавить логи из экстрактора
        }

        logger.info(f"Успешно обработан запрос: {request.url}")
        return response

    except Exception as e:
        logger.error(f"Ошибка при обработке запроса {request.url}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "error": str(e), "timestamp": datetime.now().isoformat()},
        )


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Проверка работоспособности API.

    Returns:
        Dict: статус API
    """
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.get("/stats")
async def get_stats() -> Dict[str, Any]:
    """
    Получение статистики работы API.

    Returns:
        Dict: статистика
    """
    # Здесь можно добавить сбор статистики
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "total_requests": 0,  # TODO: добавить счетчик запросов
        "success_rate": 0.0,  # TODO: добавить расчет успешности
        "most_common_protection": None,  # TODO: добавить статистику по защитам
    }
