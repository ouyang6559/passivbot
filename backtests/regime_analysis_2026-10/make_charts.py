"""Per-coin regime timeline charts (log price colored by regime + realized vol)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import font_manager

for _cand in ["Hiragino Sans GB", "PingFang SC", "Arial Unicode MS", "STHeiti"]:
    if any(f.name == _cand for f in font_manager.fontManager.ttflist):
        plt.rcParams["font.family"] = _cand
        print("using CJK font:", _cand)
        break
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).parent
DATA = ROOT / "data"
CHARTS = ROOT / "charts"
CHARTS.mkdir(exist_ok=True)

COINS = ["BTC", "ETH", "XRP", "SOL", "ADA"]
REGIMES = ["normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"]
COLORS = {
    "normal_osc": "#9ecae1",
    "low_vol_osc": "#c7e9c0",
    "strong_trend": "#fdae6b",
    "bear": "#fb6a4a",
    "extreme_vol": "#cb181d",
}
CN = {
    "normal_osc": "正常震荡",
    "low_vol_osc": "低波动震荡",
    "strong_trend": "强趋势(上行)",
    "bear": "熊市下跌",
    "extreme_vol": "极端波动",
}

for coin in COINS:
    d = pd.read_csv(DATA / f"regimes_{coin}.csv", parse_dates=["date"], index_col="date")
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(13, 7), sharex=True, gridspec_kw={"height_ratios": [3, 1]}
    )
    for regime in REGIMES:
        seg = d[d["regime"] == regime]
        ax1.scatter(seg.index, seg["close"], s=1.2, color=COLORS[regime], label=CN[regime])
    ax1.set_yscale("log")
    ax1.set_ylabel(f"{coin} price (log)")
    ax1.legend(loc="upper left", markerscale=8, framealpha=0.6, fontsize=8)
    ax1.set_title(f"{coin} 行情状态划分 (2021-01 ~ 2026-10, Binance 1h 数据)")
    ax2.fill_between(d.index, d["rv_1d"], color="#807dba", alpha=0.6, linewidth=0)
    ax2.axhline(d["rv_1d"].quantile(0.98), color="#cb181d", linewidth=0.8, linestyle="--")
    ax2.axhline(d["rv_1d"].quantile(0.30), color="#238b45", linewidth=0.8, linestyle="--")
    ax2.set_ylabel("日实现波动率")
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    fig.tight_layout()
    fig.savefig(CHARTS / f"regimes_{coin}.png", dpi=110)
    plt.close(fig)
    print(f"chart written: charts/regimes_{coin}.png")
