"""Incremental freqtrade-feather -> passivbot daily npy cache for the 13 coins.

Writes caches/ft_source/binance/1m/<COIN>/YYYY-MM-DD.npy (ts,open,high,low,close,volume,
float64, ms epoch). Skips day files that already exist except the newest day
(partial). New coins carry data from 2021-09-01; BTC/ETH/SOL extend the
existing cache.
"""
import os
from pathlib import Path

import numpy as np
import pandas as pd

SRC = Path("/Users/liu/Documents/go/gopath/src/rust-pro/freqtrade-wc/user_data/data/binance/futures")
DST = Path("caches/ft_source/binance/1m")
COINS = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "LINK", "DOT", "UNI", "LTC", "XMR"]


def convert(coin: str) -> None:
    outdir = DST / coin
    outdir.mkdir(parents=True, exist_ok=True)
    df = pd.read_feather(SRC / f"{coin}_USDT_USDT-1m-futures.feather")
    if coin not in ("BTC", "ETH", "SOL"):
        df = df[df["date"] >= pd.Timestamp("2021-09-01", tz="UTC")]
    ts = (df["date"].values.astype("datetime64[ns]").astype("int64") // 10**6).astype(np.int64)
    arr = np.stack(
        [ts, df["open"].values, df["high"].values, df["low"].values, df["close"].values, df["volume"].values],
        axis=1,
    ).astype(float)
    days = (ts // 86_400_000).astype(np.int64)
    order = np.argsort(days, kind="stable")
    days_sorted = days[order]
    arr_sorted = arr[order]
    boundaries = np.flatnonzero(np.diff(days_sorted)) + 1
    max_day = int(days_sorted[-1])
    n_new, n_skip = 0, 0
    for spl in np.split(np.arange(len(days_sorted)), boundaries):
        day = int(days_sorted[spl[0]])
        date = pd.Timestamp(day * 86_400_000, unit="ms").strftime("%Y-%m-%d")
        path = outdir / f"{date}.npy"
        if path.exists() and day < max_day - 1:
            n_skip += 1
            continue
        np.save(path, arr_sorted[spl])
        n_new += 1
    print(f"{coin}: {n_new} written, {n_skip} skipped, {len(arr)} rows "
          f"{pd.Timestamp(int(ts[0]), unit='ms')} -> {pd.Timestamp(int(ts[-1]), unit='ms')}", flush=True)


if __name__ == "__main__":
    for coin in COINS:
        convert(coin)
