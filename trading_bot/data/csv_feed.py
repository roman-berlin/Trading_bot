"""
CSV data feed for the trading bot.
"""
import pandas as pd
from trading_bot.types import Candle

class CsvFeed:
    def __init__(self, path: str):
        self.df = pd.read_csv(path, parse_dates=["time"]).sort_values("time").reset_index(drop=True)
        # Normalize columns to lower-case
        self.df.columns = self.df.columns.str.lower()

    def iter(self):
        cols = set(self.df.columns)
        use_ohlc = {"open","high","low","close"}.issubset(cols)
        for r in self.df.itertuples(index=False):
            if use_ohlc:
                yield Candle(r.time, r.open, r.high, r.low, r.close, getattr(r, "volume", 0.0))
            else:
                # Fallback if only bid/ask present
                close = getattr(r, "bid", None)
                if close is None:  # try ask
                    close = getattr(r, "ask", None)
                o = h = l = c = float(close)
                yield Candle(r.time, o, h, l, c, getattr(r, "volume", 0.0))
