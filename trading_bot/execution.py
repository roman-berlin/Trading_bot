"""
Order execution and trade management.

This module wraps the MetaTrader 5 order_send API to place and
manage trades.  It provides methods for opening buy and sell
positions with stop-loss and take-profit settings and for updating
trailing stops.
"""

from typing import Optional

import MetaTrader5 as mt5

from .config import BotConfig
from .risk_manager import RiskManager
from .utils import debug


class OrderExecutor:
    """Places and modifies orders via MetaTrader 5."""

    def __init__(self, config: BotConfig, risk_manager: RiskManager) -> None:
        self.config = config
        self.risk_manager = risk_manager

    def _build_request(self, action: int, volume: float, price: float,
                       sl: float, tp: float) -> dict:
        """Construct the order request dictionary used by mt5.order_send."""
        return {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": self.config.symbol,
            "volume": volume,
            "type": action,
            "price": price,
            "sl": sl,
            "tp": tp,
            "deviation": 10,  # maximum acceptable price slippage in points
            "magic": self.config.magic_number,
            "comment": "PythonBot",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_RETURN,
        }

    def open_buy(self, bid: float, ask: float, pip: float) -> bool:
        """Open a buy position at the current ask price."""
        lot = self.risk_manager.calculate_lot()
        stop_level = mt5.symbol_info(self.config.symbol).trade_stops_level * mt5.symbol_info(self.config.symbol).point
        sl_price = (ask - self.config.stop_loss_pips * pip) if self.config.stop_loss_pips > 0 else 0.0
        tp_price = (ask + self.config.take_profit_pips * pip) if self.config.take_profit_pips > 0 else 0.0
        # enforce minimum stop distance
        if self.config.stop_loss_pips > 0 and stop_level > 0 and (ask - sl_price) < stop_level:
            sl_price = ask - stop_level
        if self.config.take_profit_pips > 0 and stop_level > 0 and (tp_price - ask) < stop_level:
            tp_price = ask + stop_level
        sl_price = round(sl_price, mt5.symbol_info(self.config.symbol).digits) if sl_price > 0 else 0.0
        tp_price = round(tp_price, mt5.symbol_info(self.config.symbol).digits) if tp_price > 0 else 0.0
        request = self._build_request(mt5.ORDER_TYPE_BUY, lot, ask, sl_price, tp_price)
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            debug(f"Buy opened: order #{result.order}", self.config.symbol, self.config.enable_debug)
            return True
        debug(f"Buy failed: retcode {result.retcode} - {result.comment}", self.config.symbol, self.config.enable_debug)
        return False

    def open_sell(self, bid: float, ask: float, pip: float) -> bool:
        """Open a sell position at the current bid price."""
        lot = self.risk_manager.calculate_lot()
        stop_level = mt5.symbol_info(self.config.symbol).trade_stops_level * mt5.symbol_info(self.config.symbol).point
        sl_price = (bid + self.config.stop_loss_pips * pip) if self.config.stop_loss_pips > 0 else 0.0
        tp_price = (bid - self.config.take_profit_pips * pip) if self.config.take_profit_pips > 0 else 0.0
        # enforce minimum stop distance
        if self.config.stop_loss_pips > 0 and stop_level > 0 and (sl_price - bid) < stop_level:
            sl_price = bid + stop_level
        if self.config.take_profit_pips > 0 and stop_level > 0 and (bid - tp_price) < stop_level:
            tp_price = bid - stop_level
        sl_price = round(sl_price, mt5.symbol_info(self.config.symbol).digits) if sl_price > 0 else 0.0
        tp_price = round(tp_price, mt5.symbol_info(self.config.symbol).digits) if tp_price > 0 else 0.0
        request = self._build_request(mt5.ORDER_TYPE_SELL, lot, bid, sl_price, tp_price)
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            debug(f"Sell opened: order #{result.order}", self.config.symbol, self.config.enable_debug)
            return True
        debug(f"Sell failed: retcode {result.retcode} - {result.comment}", self.config.symbol, self.config.enable_debug)
        return False

    def modify_trailing_stops(self, pip: float) -> None:
        """Iterate over open positions and adjust stop-loss according to trailing stop settings."""
        if self.config.trailing_stop <= 0:
            return
        total = mt5.positions_total()
        for i in range(total):
            ticket = mt5.positions_get()[i].ticket
            pos = mt5.positions_get(ticket=ticket)[0]
            if pos.magic != self.config.magic_number or pos.symbol != self.config.symbol:
                continue
            open_price = pos.price_open
            current_sl = pos.sl
            current_tp = pos.tp
            need_modify = False
            new_sl = current_sl
            stop_level = mt5.symbol_info(self.config.symbol).trade_stops_level * mt5.symbol_info(self.config.symbol).point
            if pos.type == mt5.POSITION_TYPE_BUY:
                current_price = mt5.symbol_info_tick(self.config.symbol).bid
                candidate_sl = current_price - self.config.trailing_stop * pip
                if current_sl == 0 or candidate_sl > current_sl:
                    if (current_price - candidate_sl) >= stop_level:
                        need_modify = True
                        new_sl = candidate_sl
            elif pos.type == mt5.POSITION_TYPE_SELL:
                current_price = mt5.symbol_info_tick(self.config.symbol).ask
                candidate_sl = current_price + self.config.trailing_stop * pip
                if current_sl == 0 or candidate_sl < current_sl:
                    if (candidate_sl - current_price) >= stop_level:
                        need_modify = True
                        new_sl = candidate_sl
            if need_modify:
                new_sl = round(new_sl, mt5.symbol_info(self.config.symbol).digits)
                # modify the position
                result = mt5.order_send({
                    "action": mt5.TRADE_ACTION_SLTP,
                    "symbol": pos.symbol,
                    "position": ticket,
                    "sl": new_sl,
                    "tp": current_tp,
                    "deviation": 0,
                    "magic": pos.magic,
                    "comment": "TrailingStopUpdate",
                })
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    pos_type = "Buy" if pos.type == mt5.POSITION_TYPE_BUY else "Sell"
                    debug(f"Trailing stop updated for {pos_type} #{ticket}: new SL={new_sl}",
                          self.config.symbol, self.config.enable_debug)
                else:
                    debug(f"Trailing stop update failed for #{ticket}: retcode {result.retcode} - {result.comment}",
                          self.config.symbol, self.config.enable_debug)
