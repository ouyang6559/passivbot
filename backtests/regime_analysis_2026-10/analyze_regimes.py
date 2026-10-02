"""Regime classification + per-coin statistics for parameter calibration.

Regimes (per day, per coin, thresholds calibrated from each coin's own history):
  extreme_vol  - realized daily vol >= P98 or |daily move| >= P98 of |moves|
  bear         - sustained downtrend: below EMA90, 30d return in worst P15 and negative
  strong_trend - sustained uptrend: 30d return in best P15 and > +8%, above EMA90
  low_vol_osc  - quiet sideways: realized vol <= P30 and small 14d drift
  normal_osc   - everything else

Outputs (under this directory):
  data/regimes_<COIN>.csv      per-day metrics + regime label
  regime_stats.csv             per coin x regime summary stats
  regime_windows.json          representative contiguous windows per coin x regime
  regime_share_by_year.csv     sanity table: regime share per coin per calendar year
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent
DATA = ROOT / "data"
COINS = ["BTC", "ETH", "XRP", "SOL", "ADA", "DOGE", "LINK"]
REGIMES = ["normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"]
CN = {
    "normal_osc": "正常震荡",
    "low_vol_osc": "低波动震荡",
    "strong_trend": "强趋势(上行)",
    "bear": "熊市下跌",
    "extreme_vol": "极端波动",
}


def load_coin(coin: str) -> pd.DataFrame:
    rows = json.loads((DATA / f"{coin}_1h.json").read_text())
    df = pd.DataFrame(
        rows,
        columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "qvol", "n", "taker_base", "taker_quote", "ignore",
        ],
    )
    df = df[["open_time", "high", "low", "close"]].astype(float)
    df["dt"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df = df.set_index("dt").sort_index()
    return df


def daily_metrics(df: pd.DataFrame) -> pd.DataFrame:
    h1r = np.log(df["close"] / df["close"].shift(1))
    day = df.index.floor("D")
    g = h1r.groupby(day)
    d = pd.DataFrame({
        "rv_1d": g.std(ddof=1) * np.sqrt(24),        # daily-scale realized vol
        "n_hours": g.size(),
    })
    d["ret_1d"] = np.log(df["close"].resample("1D").last().shift(0)).pipe(
        lambda s: np.log(df["close"].resample("1D").last())
    ).diff()
    oc = df["close"].resample("1D").last()
    hi = df["high"].resample("1D").max()
    lo = df["low"].resample("1D").min()
    d = d.reindex(oc.index)
    d["close"] = oc
    d["range_1d"] = np.log(hi / lo)
    d["ret_1d"] = np.log(oc / oc.shift(1))
    d["ema30"] = oc.ewm(span=30, adjust=False).mean()
    d["ema90"] = oc.ewm(span=90, adjust=False).mean()
    d["trend_14d"] = np.log(oc / oc.shift(14))
    d["trend_30d"] = np.log(oc / oc.shift(30))
    d["dd_90"] = oc / oc.rolling(90).max() - 1.0
    # hourly log range for grid calibration
    hr = np.log(df["high"] / df["low"])
    d["range_1h_med"] = hr.groupby(day).median()
    return d.dropna(subset=["rv_1d", "range_1d", "trend_30d"])


def classify(d: pd.DataFrame) -> pd.Series:
    p = {
        "rv98": d["rv_1d"].quantile(0.98),
        "ret98": d["ret_1d"].abs().quantile(0.98),
        "t15": d["trend_30d"].quantile(0.15),
        "t85": d["trend_30d"].quantile(0.85),
        "rv30": d["rv_1d"].quantile(0.30),
        "t14_40": d["trend_14d"].abs().quantile(0.40),
    }
    cond = {}
    cond["extreme_vol"] = (d["rv_1d"] >= p["rv98"]) | (d["ret_1d"].abs() >= p["ret98"])
    cond["bear"] = (
        (d["close"] < d["ema90"])
        & (d["trend_30d"] < 0)
        & ((d["trend_30d"] <= min(p["t15"], -0.08)) | (d["dd_90"] <= -0.20))
        & ~cond["extreme_vol"]
    )
    cond["strong_trend"] = (
        (d["trend_30d"] >= max(p["t85"], 0.08))
        & (d["close"] >= d["ema90"])
        & ~cond["extreme_vol"]
        & ~cond["bear"]
    )
    cond["low_vol_osc"] = (
        (d["rv_1d"] <= p["rv30"])
        & (d["trend_14d"].abs() <= p["t14_40"])
        & ~cond["extreme_vol"] & ~cond["bear"] & ~cond["strong_trend"]
    )
    labels = pd.Series("normal_osc", index=d.index)
    for name in ["low_vol_osc", "strong_trend", "bear", "extreme_vol"]:
        labels[cond[name]] = name
    return labels, p


def windows_of(labels: pd.Series, regime: str, min_len=21, min_share=0.6):
    """Return contiguous windows where regime share >= min_share over >= min_len days."""
    idx = labels.index
    arr = (labels == regime).astype(int).values
    out = []
    i = 0
    n = len(arr)
    while i < n:
        if arr[i] == 0:
            i += 1
            continue
        j = i
        while j < n:
            seg = arr[i:j + 1]
            if seg.mean() >= min_share or (j - i) < min_len:
                j += 1
                if j < n and arr[i:j + 1].mean() < min_share and (j - i) >= min_len:
                    break
            else:
                break
        # fall back: simple scan for runs with >=60% share using expanding window
        best_end = None
        for end in range(i + min_len - 1, n):
            share = arr[i:end + 1].mean()
            if share >= min_share:
                best_end = end
            elif end - i + 1 >= min_len and share < min_share and arr[end] == 0:
                break
        if best_end is not None and (best_end - i + 1) >= min_len:
            out.append((str(idx[i].date()), str(idx[best_end].date()), int(best_end - i + 1)))
            i = best_end + 1
        else:
            i += 1
    return out


def longest_windows(ws, k=2):
    return sorted(ws, key=lambda w: -w[2])[:k]


def main():
    all_stats = []
    windows = {}
    for coin in COINS:
        df = load_coin(coin)
        d = daily_metrics(df)
        labels, p = classify(d)
        d["regime"] = labels
        d.to_csv(DATA / f"regimes_{coin}.csv", index_label="date")
        med_rng_all = d["range_1d"].median()
        for regime in REGIMES:
            seg = d[labels == regime]
            all_stats.append({
                "coin": coin,
                "regime": regime,
                "days": len(seg),
                "share_pct": round(100 * len(seg) / len(d), 1),
                "range_1d_med": round(seg["range_1d"].median(), 4),
                "rv_1d_med": round(seg["rv_1d"].median(), 4),
                "absret_1d_med": round(seg["ret_1d"].abs().median(), 4),
                "range_1h_med": round(seg["range_1h_med"].median(), 5),
                "mult_vs_own_avg": round(seg["range_1d"].median() / med_rng_all, 2),
            })
            ws = longest_windows(windows_of(labels, regime))
            if ws:
                windows.setdefault(coin, {})[regime] = ws
        # yearly sanity table
        yr = labels.groupby(labels.index.year).value_counts().unstack(fill_value=0)
        yr = (yr.T / yr.sum(axis=1)).T * 100
        yr = yr.reindex(columns=REGIMES)
        yr.round(1).to_csv(DATA / f"regime_share_{coin}.csv")
        print(f"== {coin} thresholds: " + json.dumps({k: round(v, 4) for k, v in p.items()}))
        print(yr.round(0).astype(int).to_string())
        print()

    stats = pd.DataFrame(all_stats)
    stats.to_csv(ROOT / "regime_stats.csv", index=False)
    (ROOT / "regime_windows.json").write_text(json.dumps(windows, indent=2))
    print(stats.to_string(index=False))


if __name__ == "__main__":
    main()
