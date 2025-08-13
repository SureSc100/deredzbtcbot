import numpy as np, pandas as pd
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

class SignalResult:
    def __init__(self, side=None, confidence=0.0, reason=""):
        self.side = side
        self.confidence = confidence
        self.reason = reason

def compute_indicators(df: pd.DataFrame):
    ema50 = EMAIndicator(close=df["close"], window=50).ema_indicator()
    ema200 = EMAIndicator(close=df["close"], window=200).ema_indicator()
    rsi = RSIIndicator(close=df["close"], window=14).rsi()
    macd = MACD(close=df["close"], window_slow=26, window_fast=12, window_sign=9)
    macd_line = macd.macd()
    macd_signal = macd.macd_signal()
    atr = AverageTrueRange(high=df["high"], low=df["low"], close=df["close"], window=14).average_true_range()
    out = df.copy()
    out["ema50"] = ema50
    out["ema200"] = ema200
    out["rsi"] = rsi
    out["macd"] = macd_line
    out["macd_signal"] = macd_signal
    out["atr"] = atr
    return out

def _recent_breakout(series: pd.Series, lookback=20, breakout_pct=0.0):
    last = series.iloc[-1]
    prev_max = series.iloc[-lookback:-1].max()
    prev_min = series.iloc[-lookback:-1].min()
    up = last > prev_max * (1 + breakout_pct/100)
    down = last < prev_min * (1 - breakout_pct/100)
    return up, down, prev_max, prev_min

def htf_trend_align(htf_df: pd.DataFrame, side: str) -> bool:
    if htf_df is None or len(htf_df) < 210:
        return True
    d = compute_indicators(htf_df).dropna()
    if len(d) < 210:
        return True
    close = d["close"].iloc[-1]
    ema50 = d["ema50"].iloc[-1]
    ema200 = d["ema200"].iloc[-1]
    if side == "BUY":
        return ema50 > ema200 and close > ema200
    else:
        return ema50 < ema200 and close < ema200

def generate_signal(df: pd.DataFrame, htf_df: pd.DataFrame=None, min_conf=85, require_htf=True) -> SignalResult:
    d = compute_indicators(df).dropna().copy()
    if len(d) < 210:
        return SignalResult(None, 0.0, "Not enough data")
    close = d["close"].iloc[-1]
    ema50 = d["ema50"].iloc[-1]
    ema200 = d["ema200"].iloc[-1]
    rsi = d["rsi"].iloc[-1]
    macd = d["macd"].iloc[-1]
    macd_sig = d["macd_signal"].iloc[-1]
    atr = d["atr"].iloc[-1]

    up_break, down_break, hh, ll = _recent_breakout(d["close"], lookback=20, breakout_pct=0.0)
    uptrend = ema50 > ema200 and close > ema200
    downtrend = ema50 < ema200 and close < ema200
    bull_macd = macd > macd_sig
    bear_macd = macd < macd_sig
    rsi_ok_long = 45 <= rsi <= 65
    rsi_ok_short = 35 <= rsi <= 55

    atr_pct = (atr / max(1e-8, close)) * 100
    if atr_pct > 3.5:
        return SignalResult(None, 0.0, f"ATR too high ({atr_pct:.2f}%)")

    reasons = []
    score = 0

    if uptrend and bull_macd and rsi_ok_long and (up_break or close > hh):
        score += 1.0
        reasons += ["Uptrend (EMA50>EMA200)", "MACD bull", "RSI healthy", "Breakout/highs"]
        slope = (ema50 - ema200) / max(1e-8, ema200)
        score += min(1.0, max(0.0, slope * 50))
        conf = min(99.0, 65 + score * 22)
        if conf >= min_conf:
            if not require_htf or htf_trend_align(htf_df, "BUY"):
                return SignalResult("BUY", conf, "; ".join(reasons))

    if downtrend and bear_macd and rsi_ok_short and (down_break or close < ll):
        score += 1.0
        reasons += ["Downtrend (EMA50<EMA200)", "MACD bear", "RSI healthy", "Breakout/lows"]
        slope = (ema200 - ema50) / max(1e-8, ema200)
        score += min(1.0, max(0.0, slope * 50))
        conf = min(99.0, 65 + score * 22)
        if conf >= min_conf:
            if not require_htf or htf_trend_align(htf_df, "SELL"):
                return SignalResult("SELL", conf, "; ".join(reasons))

    return SignalResult(None, 0.0, "No clean setup")
