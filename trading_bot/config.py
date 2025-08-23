"""
Configuration loading and validation.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any
import yaml

@dataclass
class Config:
    symbol: str
    timeframe: str
    risk_pct: float
    max_open_trades: int
    spread_points: int
    commission_per_lot: float
    slippage_points: int
    strategy: Dict[str, Any]
    backtest: Dict[str, Any]

    @staticmethod
    def load(path: str) -> "Config":
        data = yaml.safe_load(Path(path).read_text())
        assert data.get("risk_pct", 0) > 0, "risk_pct must be positive"
        s = data.get("strategy", {})
        assert s.get("sl_pips", 0) > 0, "strategy.sl_pips must be positive"
        assert s.get("distance_pips", 0) > 0, "strategy.distance_pips must be positive"
        assert s.get("tp_rr", 0) > 0, "strategy.tp_rr must be positive"
        return Config(**data)
