"""
Risk manager functions.
"""
from decimal import Decimal, ROUND_DOWN

def step_round(x: float, step: float) -> float:
    q = Decimal(str(step))
    return float((Decimal(x) / q).to_integral_value(rounding=ROUND_DOWN) * q)

def compute_volume(equity: float, entry: float, sl: float,
                   risk_pct: float, vol_min: float, vol_step: float, vol_max: float) -> float:
    risk_amt = equity * (risk_pct/100.0)
    stop = abs(entry - sl)
    if stop == 0:
        return vol_min
    raw = risk_amt / stop
    adj = max(vol_min, min(vol_max, step_round(raw, vol_step)))
    return adj
