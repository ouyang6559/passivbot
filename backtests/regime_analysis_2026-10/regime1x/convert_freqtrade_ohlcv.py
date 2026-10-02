import os
import numpy as np
import pandas as pd

SRC = "/Users/liu/Documents/go/gopath/src/rust-pro/freqtrade-wc/user_data/data/binance/futures"
DST = "caches/ft_source/binance/1m"

for coin in ["BTC", "ETH", "SOL"]:
    outdir = os.path.join(DST, coin)
    os.makedirs(outdir, exist_ok=True)
    df = pd.read_feather(f"{SRC}/{coin}_USDT_USDT-1m-futures.feather")
    ts = (df["date"].values.astype("datetime64[ns]").astype("int64") // 10**6).astype(np.int64)
    arr = np.stack(
        [
            ts,
            df["open"].values,
            df["high"].values,
            df["low"].values,
            df["close"].values,
            df["volume"].values,
        ],
        axis=1,
    ).astype(float)
    days = (ts // 86_400_000).astype(np.int64)
    n = 0
    # group by day
    order = np.argsort(days, kind="stable")
    days_sorted = days[order]
    arr_sorted = arr[order]
    boundaries = np.flatnonzero(np.diff(days_sorted)) + 1
    splits = np.split(np.arange(len(days_sorted)), boundaries)
    for spl in splits:
        day = days_sorted[spl[0]]
        date = pd.Timestamp(day * 86_400_000, unit="ms").strftime("%Y-%m-%d")
        path = os.path.join(outdir, f"{date}.npy")
        np.save(path, arr_sorted[spl])
        n += 1
    print(f"{coin}: {n} daily files, {len(arr)} rows, {pd.Timestamp(ts[0], unit='ms')} -> {pd.Timestamp(ts[-1], unit='ms')}")
