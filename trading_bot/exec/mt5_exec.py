"""
MetaTrader 5 live execution engine (skeleton).
"""
import time
import MetaTrader5 as mt5
import pandas as pd
from trading_bot.types import Candle

class MT5Exec:
    def __init__(self, cfg, dry_run=True):
        self.cfg = cfg
        self.dry = dry_run

    def run_loop(self, strat):
        assert mt5.initialize(), "MT5 init failed"
        try:
            assert mt5.symbol_select(self.cfg.symbol, True)
            info = mt5.symbol_info(self.cfg.symbol)
            digits = info.digits
            while True:
                rates = mt5.copy_rates_from_pos(self.cfg.symbol, getattr(mt5, self.cfg.timeframe), 0, 1)
                if rates is None or len(rates) == 0:
                    time.sleep(1); continue
                r = rates[-1]
                bar = Candle(pd.to_datetime(r['time'], unit='s'), r['open'], r['high'], r['low'], r['close'], r['tick_volume'])
                sig = strat.on_bar(bar, digits)
                if sig:
                    if self.dry:
                        print(f"signal: {sig}")
                    else:
                        print("TODO: send order")  # placeholder
                time.sleep(1)
        finally:
            mt5.shutdown()
