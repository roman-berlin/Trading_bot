"""
Simple backtesting executor.
"""
from dataclasses import asdict
from trading_bot.types import Trade, Stats
from trading_bot.risk.risk_manager import compute_volume
import csv

VOL_MIN, VOL_STEP, VOL_MAX = 0.01, 0.01, 10.0  # conservative defaults

class BacktestExec:
    def __init__(self, cfg):
        self.cfg = cfg

    @staticmethod
    def _pip(digits: int) -> float:
        return 0.01 if digits in (1,2,3) else 0.0001

    def run(self, feed, strat):
        equity = 10000.0
        trades = []
        open_trade = None
        pip = self._pip(5)
        equity_curve = []

        for bar in feed:
            sig = strat.on_bar(bar, digits=5)
            if sig and not open_trade:
                entry = bar.open
                vol = compute_volume(equity, entry, sig.sl_price,
                                     self.cfg.risk_pct, VOL_MIN, VOL_STEP, VOL_MAX)
                open_trade = Trade(
                    entry_time=bar.time, exit_time=None, side=sig.side,
                    entry_price=entry, exit_price=None, volume=vol,
                    sl_price=sig.sl_price, tp_price=sig.tp_price
                )
                equity_curve.append((bar.time, equity))
                continue

            if open_trade:
                hit_sl = (bar.low <= open_trade.sl_price) if open_trade.side == "long" else (bar.high >= open_trade.sl_price)
                hit_tp = (bar.high >= open_trade.tp_price) if open_trade.side == "long" else (bar.low <= open_trade.tp_price)
                if hit_sl or hit_tp:
                    exit_price = open_trade.sl_price if hit_sl else open_trade.tp_price
                    open_trade.exit_time = bar.time
                    open_trade.exit_price = exit_price
                    sign = 1 if open_trade.side == "long" else -1
                    pnl_t = (open_trade.exit_price - open_trade.entry_price) * sign * open_trade.volume * 100000
                    equity += pnl_t
                    trades.append(open_trade)
                    open_trade = None
            equity_curve.append((bar.time, equity))

        # Stats
        pnl = 0.0
        wins = 0
        for t in trades:
            sign = 1 if t.side == "long" else -1
            pnl_t = (t.exit_price - t.entry_price) * sign * t.volume * 100000
            pnl += pnl_t
            if pnl_t > 0:
                wins += 1
        win_rate = (wins/len(trades)) if trades else 0.0

        # Max Drawdown
        peak = -1e18
        max_dd = 0.0
        for _, eq in equity_curve:
            if eq > peak:
                peak = eq
            dd = peak - eq
            if dd > max_dd:
                max_dd = dd

        # Expectancy
        expectancy = (pnl/len(trades)) if trades else 0.0

        # Write equity.csv next to working dir
        with open("equity.csv", "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["time","equity"])
            for t, eq in equity_curve:
                w.writerow([t, eq])

        return Stats(len(trades), win_rate, pnl, max_dd, expectancy)
