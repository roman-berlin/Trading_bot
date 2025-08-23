"""
Type definitions for core trading entities.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Candle:
    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

@dataclass
class Signal:
    side: str
    sl_price: float
    tp_price: float

@dataclass
class Trade:
    entry_time: datetime
    exit_time: Optional[datetime]
    side: str
    entry_price: float
    exit_price: Optional[float]
    volume: float
    sl_price: float
    tp_price: float

@dataclass
class Stats:
    n_trades: int
    win_rate: float
    pnl: float
    max_dd: float
    expectancy: float
