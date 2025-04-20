"""
Утилита для обучения ML-модели предсказания стратегий.
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from src.protections.strategy_predictor import StrategyPredictor
from src.logger import logger


def load_training_data(log_path: str = "data/strategy_logs.csv") -> pd.DataFrame:
    """
    Загружает данные для обучения из CSV-файла.

    Args:
        log_path: Путь к файлу с логами

    Returns:
        pd.DataFrame: Загруженные данные
    """
    if not os.path.exists(log_path):
        logger.error(f"Файл с логами не найден: {log_path}")
        return pd.DataFrame()

    try:
        df = pd.read_csv(log_path)
        logger.info(f"Загружено {len(df)} записей из {log_path}")
        return df
    except Exception as e:
        logger.error(f"Ошибка загрузки данных: {e}")
        return pd.DataFrame()


def prepare_features(df: pd.DataFrame) -> tuple:
    """
    Подготавливает признаки и целевую переменную.

    Args:
        df: DataFrame с исходными данными

    Returns:
        tuple: (X, y) - матрица признаков и целевая переменная
    """
    # Создаем копию данных
    df = df.copy()

    # Создаем энкодеры для категориальных признаков
    encoders = {}
    categorical_features = ["protection_type", "user_agent_hash", "ip_region", "time_of_day"]

    for feature in categorical_features:
        if feature in df.columns:
            encoders[feature] = LabelEncoder()
            df[feature] = encoders[feature].fit_transform(df[feature])

    # Преобразуем html_title_keywords в бинарные признаки
    if "html_title_keywords" in df.columns:
        keywords = set()
        for keywords_str in df["html_title_keywords"].dropna():
            keywords.update(keywords_str.split(","))

        for keyword in keywords:
            df[f"has_{keyword}"] = (
                df["html_title_keywords"].str.contains(keyword, na=False).astype(int)
            )

        df = df.drop("html_title_keywords", axis=1)

    # Разделяем на признаки и целевую переменную
    X = df.drop("strategy_name", axis=1)
    y = df["strategy_name"]

    return X, y, encoders


def train_model(X: pd.DataFrame, y: pd.Series) -> RandomForestClassifier:
    """
    Обучает модель на подготовленных данных.

    Args:
        X: Матрица признаков
        y: Целевая переменная

    Returns:
        RandomForestClassifier: Обученная модель
    """
    # Разделяем данные на обучающую и тестовую выборки
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Создаем и обучаем модель
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)

    model.fit(X_train, y_train)

    # Оцениваем качество модели
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)

    logger.info(f"Точность на обучающей выборке: {train_score:.3f}")
    logger.info(f"Точность на тестовой выборке: {test_score:.3f}")

    return model


def main():
    """Основная функция обучения модели."""
    # Загружаем данные
    df = load_training_data()
    if df.empty:
        return

    # Подготавливаем признаки
    X, y, encoders = prepare_features(df)

    # Обучаем модель
    model = train_model(X, y)

    # Создаем и сохраняем предсказатель
    predictor = StrategyPredictor()
    predictor.model = model
    predictor.label_encoders = encoders
    predictor.save_model()

    logger.info("Обучение модели завершено успешно")


if __name__ == "__main__":
    main()
