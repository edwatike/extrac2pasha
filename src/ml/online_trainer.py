"""
Модуль для online learning ML-модели предсказания стратегий.
"""

import os
import json
import hashlib
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional
from sklearn.linear_model import SGDClassifier
from src.protections.strategy_predictor import StrategyPredictor
from src.logger import logger
import numpy as np


class OnlineTrainer:
    """Класс для online learning ML-модели."""

    def __init__(
        self,
        log_path: str = "data/strategy_logs.csv",
        meta_path: str = "models/model_meta.json",
        update_threshold: int = 100,
        update_interval_hours: int = 24,
    ):
        """
        Инициализация online trainer.

        Args:
            log_path: Путь к файлу с логами
            meta_path: Путь к файлу с метаданными модели
            update_threshold: Порог количества новых записей для обновления
            update_interval_hours: Интервал обновления в часах
        """
        self.log_path = log_path
        self.meta_path = meta_path
        self.update_threshold = update_threshold
        self.update_interval_hours = update_interval_hours
        self.predictor = StrategyPredictor()

        # Создаем необходимые директории
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        os.makedirs(os.path.dirname(meta_path), exist_ok=True)

        # Инициализируем метаданные, если файл не существует
        if not os.path.exists(meta_path):
            self._init_meta()

    def _init_meta(self) -> None:
        """Инициализирует метаданные модели."""
        meta = {
            "last_update": datetime.now().isoformat(),
            "last_hash": "",
            "total_records": 0,
            "update_count": 0,
        }
        self._save_meta(meta)

    def _load_meta(self) -> Dict:
        """Загружает метаданные модели."""
        try:
            with open(self.meta_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки метаданных: {e}")
            return {}

    def _save_meta(self, meta: Dict) -> None:
        """Сохраняет метаданные модели."""
        try:
            with open(self.meta_path, "w") as f:
                json.dump(meta, f, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения метаданных: {e}")

    def _get_file_hash(self) -> str:
        """Вычисляет хэш файла с логами."""
        try:
            with open(self.log_path, "rb") as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return ""

    def append_to_log(self, record: Dict) -> None:
        """
        Добавляет запись в лог-файл.

        Args:
            record: Словарь с данными о применении стратегии
        """
        try:
            # Преобразуем запись в DataFrame
            df = pd.DataFrame([record])

            # Добавляем запись в файл
            if os.path.exists(self.log_path):
                df.to_csv(self.log_path, mode="a", header=False, index=False)
            else:
                df.to_csv(self.log_path, index=False)

            logger.info(f"Добавлена запись в лог: {record['strategy_name']}")

        except Exception as e:
            logger.error(f"Ошибка добавления записи в лог: {e}")

    def should_update_model(self) -> bool:
        """
        Проверяет, нужно ли обновлять модель.

        Returns:
            bool: True, если модель нужно обновить
        """
        if not os.path.exists(self.log_path):
            return False

        meta = self._load_meta()
        if not meta:
            return True

        # Проверяем количество новых записей
        current_records = sum(1 for _ in open(self.log_path)) - 1  # -1 для заголовка
        new_records = current_records - meta.get("total_records", 0)

        if new_records >= self.update_threshold:
            return True

        # Проверяем время с последнего обновления
        last_update = datetime.fromisoformat(meta.get("last_update", ""))
        hours_since_update = (datetime.now() - last_update).total_seconds() / 3600

        if hours_since_update >= self.update_interval_hours:
            return True

        return False

    def update_model(self) -> None:
        """Обновляет модель на новых данных."""
        try:
            # Загружаем данные
            df = pd.read_csv(self.log_path)

            # Подготавливаем признаки
            X = df[self.predictor.feature_names]
            y = df["strategy_name"]

            # Создаем или загружаем модель
            if self.predictor.model is None:
                self.predictor.model = SGDClassifier(
                    loss="log_loss", learning_rate="adaptive", eta0=0.01, max_iter=1000
                )

            # Обновляем модель
            self.predictor.model.partial_fit(X, y, classes=np.unique(y))

            # Сохраняем модель
            self.predictor.save_model()

            # Обновляем метаданные
            meta = self._load_meta()
            meta.update(
                {
                    "last_update": datetime.now().isoformat(),
                    "last_hash": self._get_file_hash(),
                    "total_records": len(df),
                    "update_count": meta.get("update_count", 0) + 1,
                }
            )
            self._save_meta(meta)

            logger.info("Модель успешно обновлена")

        except Exception as e:
            logger.error(f"Ошибка обновления модели: {e}")

    def track_strategy_result(
        self, strategy_name: str, features_dict: Dict, success: bool, duration: float
    ) -> None:
        """
        Отслеживает результат применения стратегии.

        Args:
            strategy_name: Название стратегии
            features_dict: Словарь с признаками
            success: Успешность применения
            duration: Время выполнения в секундах
        """
        try:
            # Формируем запись
            record = {
                "strategy_name": strategy_name,
                "success": success,
                "duration": duration,
                **features_dict,
            }

            # Добавляем в лог
            self.append_to_log(record)

            # Проверяем необходимость обновления
            if self.should_update_model():
                logger.info("Запуск обновления модели")
                self.update_model()

        except Exception as e:
            logger.error(f"Ошибка отслеживания результата: {e}")
