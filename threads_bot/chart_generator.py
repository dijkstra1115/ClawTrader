"""
Generate H1 candlestick charts with support/resistance zones.
Uses mplfinance for professional-looking charts.
"""
import os
import mplfinance as mpf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from typing import Dict, List, Optional

# Dark theme for social media readability
DARK_STYLE = {
    "base_mpl_style": "dark_background",
    "marketcolors": mpf.make_marketcolors(
        up="#26a69a", down="#ef5350",
        edge={"up": "#26a69a", "down": "#ef5350"},
        wick={"up": "#26a69a", "down": "#ef5350"},
        volume={"up": "#26a69a80", "down": "#ef535080"},
    ),
    "facecolor": "#1a1a2e",
    "figcolor": "#1a1a2e",
    "gridcolor": "#2d2d4a",
    "gridstyle": "--",
    "y_on_right": True,
    "rc": {
        "axes.labelcolor": "white",
        "xtick.color": "white",
        "ytick.color": "white",
    },
}

# Support/resistance zone thickness as percentage of price range
ZONE_PCT = 0.002  # 0.2% band around each level

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "..", "charts")


def _ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def generate_chart(
    df: pd.DataFrame,
    support_levels: List[float],
    resistance_levels: List[float],
    title: str,
    filename: str,
    ema_periods: tuple = (20, 50),
) -> Optional[str]:
    """
    Generate an H1 candlestick chart with support/resistance zones and EMAs.

    Returns the file path of the saved chart image, or None on failure.
    """
    if df.empty or len(df) < 20:
        print(f"[chart] Not enough data to generate chart for {title}")
        return None

    _ensure_output_dir()

    # Prepare dataframe for mplfinance (needs DatetimeIndex)
    plot_df = df.copy()
    plot_df.set_index("datetime", inplace=True)
    plot_df.index = pd.DatetimeIndex(plot_df.index)

    # Only show last 72 candles (3 days of H1)
    plot_df = plot_df.tail(72)

    style = mpf.make_mpf_style(**DARK_STYLE)

    # Build EMA overlay lines
    ema_colors = ["#FFD700", "#FF69B4"]  # Gold, Pink
    ema_plots = []
    for i, period in enumerate(ema_periods):
        ema = plot_df["close"].ewm(span=period).mean()
        ema_plots.append(mpf.make_addplot(
            ema, color=ema_colors[i], width=1.2,
            label=f"EMA {period}",
        ))

    # Generate the chart
    fig, axes = mpf.plot(
        plot_df,
        type="candle",
        style=style,
        volume=True,
        addplot=ema_plots if ema_plots else None,
        title="",
        figsize=(12, 7),
        returnfig=True,
        panel_ratios=(4, 1),
        scale_padding={"left": 0.5, "right": 1.0, "top": 0.6, "bottom": 0.75},
    )

    ax_price = axes[0]  # Price axis

    # Draw support zones (green)
    price_range = plot_df["high"].max() - plot_df["low"].min()
    zone_height = price_range * 0.008  # zone thickness

    for level in support_levels:
        ax_price.axhspan(
            level - zone_height / 2, level + zone_height / 2,
            color="#26a69a", alpha=0.25, zorder=0,
        )
        ax_price.axhline(
            y=level, color="#26a69a", linestyle="--",
            linewidth=1, alpha=0.7, zorder=1,
        )
        ax_price.text(
            plot_df.index[1], level,
            f"  S: ${level:,.0f}" if level > 100 else f"  S: ${level:,.2f}",
            color="#26a69a", fontsize=9, fontweight="bold",
            va="center", ha="left",
            bbox=dict(boxstyle="round,pad=0.2", fc="#1a1a2e", ec="#26a69a", alpha=0.8),
        )

    # Draw resistance zones (red)
    for level in resistance_levels:
        ax_price.axhspan(
            level - zone_height / 2, level + zone_height / 2,
            color="#ef5350", alpha=0.25, zorder=0,
        )
        ax_price.axhline(
            y=level, color="#ef5350", linestyle="--",
            linewidth=1, alpha=0.7, zorder=1,
        )
        ax_price.text(
            plot_df.index[1], level,
            f"  R: ${level:,.0f}" if level > 100 else f"  R: ${level:,.2f}",
            color="#ef5350", fontsize=9, fontweight="bold",
            va="center", ha="left",
            bbox=dict(boxstyle="round,pad=0.2", fc="#1a1a2e", ec="#ef5350", alpha=0.8),
        )

    # Title and branding
    ax_price.set_title(
        title,
        color="white", fontsize=16, fontweight="bold", loc="left", pad=12,
    )
    ax_price.text(
        0.99, 0.97, "ClawTrader",
        transform=ax_price.transAxes,
        color="#FFD700", fontsize=11, fontweight="bold",
        va="top", ha="right", alpha=0.7,
    )
    ax_price.text(
        0.99, 0.93, "H1 Support & Resistance",
        transform=ax_price.transAxes,
        color="#aaaaaa", fontsize=9,
        va="top", ha="right", alpha=0.7,
    )

    # EMA legend
    ax_price.text(
        0.01, 0.97, f"— EMA {ema_periods[0]}",
        transform=ax_price.transAxes,
        color=ema_colors[0], fontsize=9, va="top", ha="left",
    )
    ax_price.text(
        0.01, 0.93, f"— EMA {ema_periods[1]}",
        transform=ax_price.transAxes,
        color=ema_colors[1], fontsize=9, va="top", ha="left",
    )

    filepath = os.path.join(OUTPUT_DIR, filename)
    fig.savefig(filepath, dpi=100, facecolor="#1a1a2e")
    plt.close(fig)

    print(f"[chart] Saved: {filepath}")
    return filepath


def generate_analysis_charts(analysis_data: Dict, raw_data: Dict) -> Dict[str, str]:
    """
    Generate charts for all analyzed assets.

    Args:
        analysis_data: output from analyze_all()
        raw_data: dict with 'bitcoin' and 'gold' keys containing raw DataFrames

    Returns:
        dict mapping asset key to chart file path
    """
    charts = {}

    for key, name, symbol in [
        ("bitcoin", "Bitcoin (BTC/USDT)", "btc"),
        ("gold", "Gold (PAXG/USDT)", "gold"),
    ]:
        a = analysis_data.get(key, {})
        df = raw_data.get(key, pd.DataFrame())

        if "error" in a or df.empty:
            continue

        filepath = generate_chart(
            df=df,
            support_levels=a.get("support", []),
            resistance_levels=a.get("resistance", []),
            title=f"{name} — H1 Analysis",
            filename=f"{symbol}_h1_chart.png",
        )
        if filepath:
            charts[key] = filepath

    return charts


if __name__ == "__main__":
    from .technical_analysis import fetch_h1_ohlcv_binance, fetch_h1_ohlcv_gold, analyze_asset

    btc_df = fetch_h1_ohlcv_binance("BTCUSDT")
    btc_analysis = analyze_asset("BTCUSDT", "Bitcoin (BTC)")

    gold_df = fetch_h1_ohlcv_gold()
    gold_analysis = analyze_asset("GOLD", "Gold (XAU)")

    raw = {"bitcoin": btc_df, "gold": gold_df}
    analysis = {"bitcoin": btc_analysis, "gold": gold_analysis}

    charts = generate_analysis_charts(analysis, raw)
    print(f"Generated charts: {charts}")
