"""Fetch public 1h klines (Binance USDT-M futures, unauthenticated public REST)
for the 5 config coins, for regime classification analysis.

No credentials, no account endpoints — market data only.
"""
import json
import time
from pathlib import Path

import requests

BASE = "https://fapi.binance.com/fapi/v1/klines"
OUT = Path(__file__).parent / "data"
OUT.mkdir(exist_ok=True)

SYMBOLS = {
    "BTC": "BTCUSDT",
    "ETH": "ETHUSDT",
    "XRP": "XRPUSDT",
    "SOL": "SOLUSDT",
    "ADA": "ADAUSDT",
    "DOGE": "DOGEUSDT",
    "LINK": "LINKUSDT",
}
START_MS = int(time.mktime(time.strptime("2021-01-01", "%Y-%m-%d"))) * 1000

session = requests.Session()


def fetch(symbol: str) -> list:
    rows = []
    start = START_MS
    while True:
        params = {"symbol": symbol, "interval": "1h", "startTime": start, "limit": 1000}
        for attempt in range(5):
            try:
                r = session.get(BASE, params=params, timeout=20)
                if r.status_code == 429 or r.status_code == 418:
                    wait = int(r.headers.get("retry-after", "30"))
                    print(f"  rate limited, waiting {wait}s")
                    time.sleep(wait)
                    continue
                r.raise_for_status()
                break
            except Exception as e:  # noqa: BLE001 - retry then raise
                if attempt == 4:
                    raise
                print(f"  retry {attempt + 1}: {e}")
                time.sleep(2 * (attempt + 1))
        batch = r.json()
        if not batch:
            break
        rows.extend(batch)
        last_open = batch[-1][0]
        start = last_open + 3_600_000
        if len(batch) < 1000:
            break
        time.sleep(0.15)
    return rows


def main():
    summary = {}
    for coin, symbol in SYMBOLS.items():
        t0 = time.time()
        rows = fetch(symbol)
        # columns: open_time, open, high, low, close, volume, close_time, qvol, n, taker_base, taker_quote, ignore
        out_path = OUT / f"{coin}_1h.json"
        out_path.write_text(json.dumps(rows))
        summary[coin] = {
            "symbol": symbol,
            "rows": len(rows),
            "first": rows[0][0],
            "last": rows[-1][0],
            "seconds": round(time.time() - t0, 1),
        }
        print(f"{coin}: {len(rows)} rows  {summary[coin]['seconds']}s")
    (OUT / "fetch_summary.json").write_text(json.dumps(summary, indent=2))
    print("done")


if __name__ == "__main__":
    main()
