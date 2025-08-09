"""
Risk management module.

Implements simple fixed fractional money management akin to the MQL5
expert advisor.  If the `mm` parameter is greater than zero, the lot
size is proportional to the account equity; otherwise the fixed lot
size from the configuration is used.
"""

import MetaTrader5 as mt5

from .config import BotConfig
from .utils import debug


class RiskManager:
    """Determines position size based on account equity and config."""

    def __init__(self, config: BotConfig, enable_debug: bool = False) -> None:
        self.config = config
        self.enable_debug = enable_debug

    def calculate_lot(self) -> float:
        """Compute the trade lot size according to money management rules."""
        # Use fixed lot if MM disabled
        if self.config.mm <= 0:
            return self.config.lot_size

        equity = mt5.account_info().equity
        calculated_lot = (equity / 10000.0) * self.config.mm

        # Retrieve symbol limits
        sym_info = mt5.symbol_info(self.config.symbol)
        min_lot = sym_info.volume_min
        max_lot = sym_info.volume_max
        step_lot = sym_info.volume_step

        # Apply MM maximum limit if set
        if self.config.mm_max_lot > 0:
            max_lot = min(max_lot, self.config.mm_max_lot)

        # Clamp between min and max
        if calculated_lot < min_lot:
            calculated_lot = min_lot
        if calculated_lot > max_lot:
            calculated_lot = max_lot

        # Normalize to step size (floor)
        normalized = (calculated_lot // step_lot) * step_lot
        if normalized < min_lot:
            normalized = min_lot

        # Round to two decimal places for readability
        return round(normalized, 2)
