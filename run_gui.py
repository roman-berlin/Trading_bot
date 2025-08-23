"""
Minimal GUI stub. Loads Config and shows main window.
"""
from PyQt5.QtWidgets import QApplication
from trading_bot.config import Config
# Placeholder GUI reference to keep file compiling if GUI not present
class MainWindow(object):
    def __init__(self, cfg): pass
    def show(self): pass

def main():
    app = QApplication([])
    try:
        cfg = Config.load("config.yaml")
    except Exception:
        cfg = Config(symbol="EURUSD", timeframe="M5", risk_pct=1.0,
                     max_open_trades=1, spread_points=10, commission_per_lot=0.0,
                     slippage_points=2,
                     strategy={"name":"distance_time","window_minutes":10,"distance_pips":5,"sl_pips":12,"tp_rr":1.5},
                     backtest={"csv_path":"data/sample_data.csv","tz":"UTC","start":None,"end":None})
    w = MainWindow(cfg)
    w.show()
    app.exec()

if __name__ == "__main__":
    main()
