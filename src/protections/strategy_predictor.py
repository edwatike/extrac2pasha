"""
Модуль для ML-предсказания оптимальных стратегий обхода защиты.
"""

import os
import pickle
from typing import Dict, Optional
import numpy as np
from sklearn.preprocessing import LabelEncoder
from src.logger import logger


class StrategyPredictor:
    """Класс для ML-предсказания стратегий."""

    def __init__(self, model_path: str = "models/strategy_model.pkl"):
        """
        Инициализация предиктора.

        Args:
            model_path: Путь к сохраненной модели
        """
        self.model_path = model_path
        self.model = None
        self.feature_names = [
            "protection_type",
            "user_agent",
            "has_captcha",
            "html_title_keywords",
            "ip_region",
            "url_depth",
            "time_of_day",
        ]
        self.encoders = {}

        # Загружаем модель, если она существует
        if os.path.exists(model_path):
            self._load_model()

    def _load_model(self) -> None:
        """Загружает модель и энкодеры."""
        try:
            with open(self.model_path, "rb") as f:
                data = pickle.load(f)
                self.model = data["model"]
                self.encoders = data.get("encoders", {})

            logger.info("ML модель успешно загружена")

        except Exception as e:
            logger.error(f"Ошибка загрузки ML модели: {e}")
            self.model = None

    def predict_best_strategy(self, context: Dict) -> Optional[str]:
        """
        Предсказывает лучшую стратегию на основе контекста.

        Args:
            context: Словарь с признаками

        Returns:
            Optional[str]: Название стратегии или None
        """
        if not self.model:
            return None

        try:
            # Подготавливаем признаки
            features = []
            for feature in self.feature_names:
                value = context.get(feature, "")

                # Кодируем категориальные признаки
                if feature in self.encoders:
                    encoder = self.encoders[feature]
                    if value not in encoder.classes_:
                        value = encoder.classes_[0]  # Используем первый класс как дефолтный
                    value = encoder.transform([value])[0]

                features.append(value)

            # Делаем предсказание
            features = np.array(features).reshape(1, -1)
            strategy = self.model.predict(features)[0]

            logger.info(f"ML модель предсказала стратегию: {strategy}")
            return strategy

        except Exception as e:
            logger.error(f"Ошибка предсказания стратегии: {e}")
            return None

    def save_model(self) -> None:
        """Сохраняет модель и энкодеры."""
        try:
            # Создаем директорию, если её нет
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)

            # Сохраняем модель и энкодеры
            with open(self.model_path, "wb") as f:
                pickle.dump({"model": self.model, "encoders": self.encoders}, f)

            logger.info("ML модель успешно сохранена")

        except Exception as e:
            logger.error(f"Ошибка сохранения ML модели: {e}")
