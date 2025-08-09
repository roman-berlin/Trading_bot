"""
Trading bot package.

This package provides modules for connecting to MetaTrader 5, running
strategies, managing risk and executing trades.  It is a starting
point for building a modular algorithmic trading system in Python.

Trading Bot

A modular and extensible trading bot system with support for multiple brokers,
strategies, and risk management techniques.
"""
# Avoid importing heavy broker modules by default.  Optional components
# are imported lazily to prevent import errors when optional
# dependencies (such as MetaTrader5) are not installed.  Users can
# explicitly import these symbols from their respective modules.
try:
    from .app import TradingBot
    from .broker_factory import BrokerFactory
except Exception:
    TradingBot = None  # type: ignore
    BrokerFactory = None  # type: ignore

from .config import BotConfig
from .interfaces import IBroker, IDataFeed, IStrategy, IRiskManager, IOrderExecutor
from .risk_manager import (
    BaseRiskManager,
    FixedFractionalRiskManager,
    FixedLotSizeRiskManager,
    RiskManagerFactory,
    PositionSizeResult,
    RiskManager,
)

__version__ = "0.2.0"

__all__ = [
    # Core components
    'TradingBot',
    'BrokerFactory',
    'BotConfig',

    # Interfaces
    'IBroker',
    'IDataFeed',
    'IStrategy',
    'IRiskManager',
    'IOrderExecutor',

    # Money management
    'BaseRiskManager',
    'FixedFractionalRiskManager',
    'FixedLotSizeRiskManager',
    'RiskManagerFactory',
    'PositionSizeResult',
    'RiskManager'
]
