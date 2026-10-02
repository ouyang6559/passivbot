import glob
import json
import logging
import os
import sys

sys.path.insert(0, "src")
logging.disable(logging.CRITICAL)
from config.load import load_input_config, prepare_config

SOURCE_ROOT = os.path.abspath("caches/ft_source")
START_DATES = {"BTC": "2019-09-09", "ETH": "2019-11-28", "SOL": "2020-09-15"}
END_DATE = "2026-10-01"
OUT_ROOT = "configs/local/regime_1x_bt"

count = 0
for f in sorted(glob.glob("configs/regime_1x/*/*/*.json")):
    coin, regime, side = f.split("/")[2], f.split("/")[3], f.split("/")[4][:-5]
    if coin not in START_DATES:
        continue
    source, _, _ = load_input_config(f, log_info=False)
    cfg = prepare_config(source, verbose=False)
    cfg["backtest"]["ohlcv_source_dir"] = SOURCE_ROOT
    cfg["backtest"]["exchanges"] = ["binance"]
    cfg["backtest"]["start_date"] = START_DATES[coin]
    cfg["backtest"]["end_date"] = END_DATE
    outdir = os.path.join(OUT_ROOT, coin, regime)
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, f"{side}.json")
    with open(out, "w") as fh:
        json.dump(cfg, fh, indent=4)
    count += 1
print(f"wrote {count} run configs under {OUT_ROOT}")
