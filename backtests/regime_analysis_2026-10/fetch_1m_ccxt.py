"""Download/refresh Binance USDT-M 1m OHLCV into freqtrade-format feather files.

Public unauthenticated market data only (no credentials, no account calls).
New coins start 2021-09-01 (warmup before the 2022-01-01 backtest window);
existing coins are extended from their last candle to now. Idempotent.
"""
import time
from pathlib import Path

import ccxt
import pandas as pd

SRC = Path("/Users/liu/Documents/go/gopath/src/rust-pro/freqtrade-wc/user_data/data/binance/futures")
NEW_COIN_START = "2021-09-01"
COINS = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "LINK", "DOT", "UNI", "LTC", "XMR"]

ex = ccxt.binanceusdm({"enableRateLimit": True})
ex.proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}


def fetch_range(symbol: str, since_ms: int, until_ms: int) -> list:
    rows = []
    cursor = since_ms
    stalls = 0
    while cursor < until_ms:
        try:
            batch = ex.fetch_ohlcv(symbol, "1m", since=cursor, limit=1000)
        except (ccxt.RateLimitExceeded, ccxt.RequestTimeout, ccxt.ExchangeNotAvailable,
                ccxt.DDoSProtection) as e:
            stalls += 1
            if stalls > 20:
                raise
            wait = min(60 * stalls, 300)
            print(f"  {symbol}: rate-limited/{type(e).__name__}, backing off {wait}s", flush=True)
            time.sleep(wait)
            continue
        if not batch:
            break
        rows.extend(batch)
        last = batch[-1][0]
        if last <= cursor:
            break
        cursor = last + 60_000
        if len(batch) < 1000 and last >= until_ms - 120_000:
            break
    return rows


def to_df(rows: list) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
    df["date"] = pd.to_datetime(df["ts"], unit="ms", utc=True).astype("datetime64[ms, UTC]")
    return df[["date", "open", "high", "low", "close", "volume"]]


def main():
    now_ms = ex.milliseconds()
    for coin in COINS:
        path = SRC / f"{coin}_USDT_USDT-1m-futures.feather"
        symbol = f"{coin}/USDT:USDT"
        if path.exists():
            old = pd.read_feather(path)
            last_ms = int(old["date"].max().value // 10**6)
            start_ms = last_ms + 60_000
        else:
            old = None
            start_ms = int(pd.Timestamp(NEW_COIN_START, tz="UTC").value // 10**6)
        if start_ms >= now_ms - 120_000:
            print(f"{coin}: up to date", flush=True)
            continue
        t0 = time.time()
        try:
            rows = fetch_range(symbol, start_ms, now_ms)
        except Exception as e:  # noqa: BLE001
            print(f"{coin}: FETCH ERROR {e}", flush=True)
            continue
        if not rows:
            print(f"{coin}: no new rows", flush=True)
            continue
        new = to_df(rows)
        if old is not None:
            df = pd.concat([old, new], ignore_index=True)
            df = df.drop_duplicates(subset="date", keep="last").sort_values("date").reset_index(drop=True)
        else:
            df = new.sort_values("date").reset_index(drop=True)
        df.to_feather(path)
        print(f"{coin}: +{len(new)} rows in {time.time() - t0:.0f}s -> {df['date'].min()} .. {df['date'].max()} (total {len(df)})", flush=True)


if __name__ == "__main__":
    main()
