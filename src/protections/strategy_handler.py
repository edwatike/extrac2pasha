"""
Модуль для управления стратегиями обхода защит.
"""

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine, Column, String, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from src.logger import logger
from src.protections.strategy_discovery import StrategyDiscovery
from src.protections.strategy_selector import StrategySelector

Base = declarative_base()


class ProtectionStrategy(Base):
    """Модель для хранения стратегий обхода защит."""

    __tablename__ = "protection_strategies"

    id = Column(String, primary_key=True)
    protection_type = Column(String)
    strategy_name = Column(String)
    strategy_params = Column(JSON)
    success_count = Column(JSON, default=0)
    last_used = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)


class StrategyHandler:
    """Класс для управления стратегиями обхода защит."""

    def __init__(self, db_path: str = "data/strategies.db"):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.discovery = StrategyDiscovery(self)
        self.selector = StrategySelector(db_path)

        # Стандартные стратегии для известных типов защит
        self.default_strategies = {
            "cloudflare": {
                "name": "solve_with_playwright",
                "params": {"wait_until": "networkidle"},
            },
            "ddos_guard": {
                "name": "solve_with_headers_tweaking",
                "params": {
                    "headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    }
                },
            },
        }

    def find_strategy(self, protection_type: str, url: str) -> Optional[Dict[str, Any]]:
        """
        Ищет подходящую стратегию для типа защиты.

        Args:
            protection_type: Тип защиты
            url: URL для проверки

        Returns:
            Optional[Dict[str, Any]]: Найденная стратегия или None
        """
        session = self.Session()
        try:
            # Пробуем найти лучшую стратегию через селектор
            best_strategy_name = self.selector.get_best_strategy(protection_type)
            if best_strategy_name:
                strategy = (
                    session.query(ProtectionStrategy)
                    .filter_by(strategy_name=best_strategy_name)
                    .first()
                )

                if strategy:
                    logger.log_event(
                        "strategy",
                        "found",
                        {"type": protection_type, "strategy": strategy.strategy_name},
                    )
                    return {"name": strategy.strategy_name, "params": strategy.strategy_params}

            # Ищем сохраненную стратегию
            strategy = (
                session.query(ProtectionStrategy).filter_by(protection_type=protection_type).first()
            )

            if strategy:
                logger.log_event(
                    "strategy",
                    "found",
                    {"type": protection_type, "strategy": strategy.strategy_name},
                )
                return {"name": strategy.strategy_name, "params": strategy.strategy_params}

            # Пробуем стандартную стратегию
            if protection_type in self.default_strategies:
                logger.log_event(
                    "strategy",
                    "default",
                    {
                        "type": protection_type,
                        "strategy": self.default_strategies[protection_type]["name"],
                    },
                )
                return self.default_strategies[protection_type]

            # Если ничего не найдено, пробуем открыть новую стратегию
            logger.log_event("strategy", "not_found", {"type": protection_type, "url": url})

            new_strategy = self.discovery.discover_new_strategy(
                url, {"protection_type": protection_type}
            )
            if new_strategy:
                logger.log_event(
                    "strategy", "discovered", {"type": protection_type, "strategy": new_strategy}
                )
                return self.find_strategy(
                    protection_type, url
                )  # Повторно ищем сохраненную стратегию

            return None
        finally:
            session.close()

    def save_strategy(
        self, strategy_name: str, strategy_params: Dict[str, Any], protection_type: str
    ) -> None:
        """
        Сохраняет новую стратегию.

        Args:
            strategy_name: Название стратегии
            strategy_params: Параметры стратегии
            protection_type: Тип защиты
        """
        session = self.Session()
        try:
            strategy = ProtectionStrategy(
                id=f"{protection_type}_{strategy_name}",
                protection_type=protection_type,
                strategy_name=strategy_name,
                strategy_params=strategy_params,
                last_used=datetime.now(),
            )
            session.add(strategy)
            session.commit()

            logger.log_event(
                "strategy", "saved", {"type": protection_type, "strategy": strategy_name}
            )
        finally:
            session.close()

    def update_strategy_stats(self, strategy_id: str, success: bool, time_taken: float) -> None:
        """
        Обновляет статистику использования стратегии.

        Args:
            strategy_id: ID стратегии
            success: Успешность применения
            time_taken: Время выполнения в секундах
        """
        session = self.Session()
        try:
            strategy = session.query(ProtectionStrategy).filter_by(id=strategy_id).first()
            if strategy:
                # Обновляем статистику в базе стратегий
                strategy.success_count = strategy.success_count or 0
                strategy.success_count += 1 if success else 0
                strategy.last_used = datetime.now()
                session.commit()

                # Обновляем статистику в селекторе
                self.selector.evaluate_strategy_result(
                    strategy.strategy_name, success, time_taken, strategy.protection_type
                )
        finally:
            session.close()
