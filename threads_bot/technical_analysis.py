"""
H1 (1-hour) technical analysis for Bitcoin and Gold.
Calculates support/resistance levels using pivot points and price action.
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional


def fetch_h1_ohlcv_binance(symbol: str = "BTCUSDT", limit: int = 100) -> pd.DataFrame:
    """Fetch H1 candle data from Binance public API."""
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": "1h",
        "limit": limit,
    }
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore"
        ])
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        df["datetime"] = pd.to_datetime(df["open_time"], unit="ms")
        return df[["datetime", "open", "high", "low", "close", "volume"]]
    except Exception as e:
        print(f"[technical_analysis] Failed to fetch {symbol}: {e}")
        return pd.DataFrame()


def fetch_h1_ohlcv_gold() -> pd.DataFrame:
    """
    Fetch H1 candle data for Gold (XAU/USD).
    Uses Binance PAX Gold (PAXGUSDT) as a proxy.
    """
    return fetch_h1_ohlcv_binance("PAXGUSDT", limit=100)


def find_support_resistance(df: pd.DataFrame, window: int = 5) -> Dict:
    """
    Find support and resistance levels using local min/max method.

    Returns dict with 'support' and 'resistance' lists of price levels.
    """
    if df.empty or len(df) < window * 2:
        return {"support": [], "resistance": []}

    highs = df["high"].values
    lows = df["low"].values

    resistance_levels = []
    support_levels = []

    for i in range(window, len(df) - window):
        # Local maximum -> resistance
        if highs[i] == max(highs[i - window:i + window + 1]):
            resistance_levels.append(round(float(highs[i]), 2))

        # Local minimum -> support
        if lows[i] == min(lows[i - window:i + window + 1]):
            support_levels.append(round(float(lows[i]), 2))

    # Cluster nearby levels (within 0.5% of each other)
    support_levels = _cluster_levels(support_levels)
    resistance_levels = _cluster_levels(resistance_levels)

    return {
        "support": sorted(support_levels)[-3:],       # Top 3 nearest supports
        "resistance": sorted(resistance_levels)[:3],   # Top 3 nearest resistances
    }


def _cluster_levels(levels: List[float], threshold: float = 0.005) -> List[float]:
    """Merge price levels that are within threshold% of each other."""
    if not levels:
        return []

    levels = sorted(levels)
    clustered = []
    cluster = [levels[0]]

    for i in range(1, len(levels)):
        if (levels[i] - cluster[0]) / cluster[0] <= threshold:
            cluster.append(levels[i])
        else:
            clustered.append(round(np.mean(cluster), 2))
            cluster = [levels[i]]

    clustered.append(round(np.mean(cluster), 2))
    return clustered


def calculate_trend(df: pd.DataFrame) -> str:
    """Determine the current trend using EMA crossover on H1 data."""
    if df.empty or len(df) < 50:
        return "neutral"

    close = df["close"]
    ema_20 = close.ewm(span=20).mean()
    ema_50 = close.ewm(span=50).mean()

    current_price = close.iloc[-1]
    ema20_val = ema_20.iloc[-1]
    ema50_val = ema_50.iloc[-1]

    if ema20_val > ema50_val and current_price > ema20_val:
        return "bullish"
    elif ema20_val < ema50_val and current_price < ema20_val:
        return "bearish"
    else:
        return "neutral"


def calculate_rsi(df: pd.DataFrame, period: int = 14) -> Optional[float]:
    """Calculate RSI for the latest candle."""
    if df.empty or len(df) < period + 1:
        return None

    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(float(rsi.iloc[-1]), 1)


def analyze_asset(symbol: str, name: str) -> Dict:
    """
    Full H1 analysis for a single asset.
    Returns support/resistance, trend, RSI, and current price.
    """
    if symbol == "GOLD":
        df = fetch_h1_ohlcv_gold()
    else:
        df = fetch_h1_ohlcv_binance(symbol)

    if df.empty:
        return {"asset": name, "error": "Failed to fetch data"}

    sr_levels = find_support_resistance(df)
    trend = calculate_trend(df)
    rsi = calculate_rsi(df)
    current_price = round(float(df["close"].iloc[-1]), 2)
    high_24h = round(float(df["high"].tail(24).max()), 2)
    low_24h = round(float(df["low"].tail(24).min()), 2)

    return {
        "asset": name,
        "current_price": current_price,
        "high_24h": high_24h,
        "low_24h": low_24h,
        "support": sr_levels["support"],
        "resistance": sr_levels["resistance"],
        "trend": trend,
        "rsi": rsi,
    }


def analyze_all() -> Dict:
    """Run H1 analysis for both BTC and Gold."""
    btc = analyze_asset("BTCUSDT", "Bitcoin (BTC)")
    gold = analyze_asset("GOLD", "Gold (XAU)")
    return {"bitcoin": btc, "gold": gold}


if __name__ == "__main__":
    import json
    result = analyze_all()
    print(json.dumps(result, indent=2, ensure_ascii=False))
