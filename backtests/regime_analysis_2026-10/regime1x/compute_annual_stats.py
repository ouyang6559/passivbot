"""Annual (per-calendar-year) equity performance for the 45 regime_1x runs.

Reads each run's balance_and_equity.csv.gz (hourly usd_total_equity) and
computes per-year return and worst intra-year drawdown. Saves
regime1x/annual_stats.json and prints a digest.
"""
import json
from pathlib import Path

import pandas as pd

R1X = Path(__file__).parent
results = json.loads((R1X / "results.json").read_text())

out = {}
for key, v in sorted(results.items()):
    if not v.get("analysis_metrics_done"):
        continue
    coin, regime, side = key.split("/")
    side = side.removesuffix(".json")
    df = pd.read_csv(Path(v["run_dir"]) / "balance_and_equity.csv.gz")
    df["dt"] = pd.to_datetime(df["Unnamed: 0"])
    eq = df.set_index("dt")["usd_total_equity"]
    ret_h = eq.pct_change().clip(-0.5, 0.5)
    fills = pd.read_csv(Path(v["run_dir"]) / "fills.csv", parse_dates=["timestamp"])
    fill_years = fills["timestamp"].dt.year.value_counts().to_dict()
    years = {}
    for year, seg in eq.groupby(eq.index.year):
        run_max = seg.cummax()
        dd = (seg / run_max - 1.0).min()
        r = ret_h.loc[seg.index]
        sharpe = float(r.mean() / r.std() * (24 * 365) ** 0.5) if r.std() > 0 else 0.0
        years[str(int(year))] = {
            "return": round(seg.iloc[-1] / seg.iloc[0] - 1.0, 4),
            "worst_dd": round(dd, 4),
            "end_equity": round(float(seg.iloc[-1]), 0),
            "sharpe": round(sharpe, 2),
            "n_fills": int(fill_years.get(year, 0)),
        }
    out[f"{coin}/{regime}/{side}"] = {
        "liquidated": bool(v.get("liquidated")),
        "start_year": int(eq.index[0].year),
        "end": str(eq.index[-1].date()),
        "years": years,
    }

(R1X / "annual_stats.json").write_text(json.dumps(out, indent=2))
print(f"saved annual_stats.json ({len(out)} runs)")
for coin in ("BTC", "ETH", "SOL"):
    for side in ("long", "short", "both"):
        for regime in ("normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"):
            k = f"{coin}/{regime}/{side}"
            if k not in out:
                continue
            ys = out[k]["years"]
            s = " ".join(f"{y}:{d['return']:+.2f}" for y, d in sorted(ys.items()))
            print(f"{coin:4s} {side:5s} {regime:12s} liq={int(out[k]['liquidated'])} {s}")
