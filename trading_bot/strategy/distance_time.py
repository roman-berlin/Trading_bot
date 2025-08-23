"""
Distance/Time breakout strategy.
"""
import collections
from trading_bot.types import Signal, Candle

class DistanceTime:
    def __init__(self, cfg) -> None:
        s = cfg.strategy
        self.win = s["window_minutes"]
        self.dist = s["distance_pips"]
        self.sl_pips = s["sl_pips"]
        self.tp_rr = s["tp_rr"]
        self.window = collections.deque(maxlen=max(1, self.win))

    @staticmethod
    def _pip(digits: int) -> float:
        return 0.01 if digits in (1,2,3) else 0.0001

    def on_bar(self, bar: Candle, digits: int = 5):
        self.window.append(bar)
        if len(self.window) < self.window.maxlen:
            return None
        hi = max(c.high for c in self.window)
        lo = min(c.low for c in self.window)
        dist_pips = (hi - lo) / self._pip(digits)
        if dist_pips < self.dist:
            return None
        last = self.window[-1].close
        pip = self._pip(digits)
        if last >= hi:
            return Signal("long", last - self.sl_pips*pip, last + self.sl_pips*self.tp_rr*pip)
        if last <= lo:
            return Signal("short", last + self.sl_pips*pip, last - self.sl_pips*self.tp_rr*pip)
        return None
