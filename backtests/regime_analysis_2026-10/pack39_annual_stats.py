"""Annual (per-calendar-year) equity stats for the 39 pack39 runs.

Reads pack39/results.json, extracts hourly usd_total_equity from each run's
balance_and_equity.csv.gz, computes per-year return / worst drawdown / annualized
Sharpe / fill count. Saves pack39/annual_stats.json and prints a digest table.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
results = json.loads((ROOT / "pack39" / "results.json").read_text())

out = {}
for key, v in sorted(results.items()):
    if not v.get("analysis_metrics_done"):
        continue
    coin, mode = key.split("/")
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
    total_mult = float(eq.iloc[-1] / eq.iloc[0])
    out[key] = {
        "liquidated": bool(v.get("liquidated")),
        "adg_pnl": v.get("adg_pnl"),
        "drawdown_worst_usd": v.get("drawdown_worst_usd"),
        "completion": v.get("backtest_completion_ratio"),
        "n_fills_total": v.get("n_fills"),
        "total_return_mult": round(total_mult, 4),
        "start": str(eq.index[0].date()),
        "end": str(eq.index[-1].date()),
        "years": years,
    }

(ROOT / "pack39" / "annual_stats.json").write_text(json.dumps(out, indent=2))
print(f"saved annual_stats.json ({len(out)} runs)\n")
hdr = f"{'coin':5s} {'mode':6s} {'liq':3s} {'total_x':8s} " + " ".join(f"{y:>8s}" for y in ("2022", "2023", "2024", "2025", "2026"))
print(hdr)
for coin in ("BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "LINK", "DOT", "UNI", "LTC", "XMR"):
    for mode in ("long", "short", "both"):
        k = f"{coin}/{mode}"
        if k not in out:
            print(f"{coin:5s} {mode:6s} MISSING")
            continue
        d = out[k]
        ys = d["years"]
        cells = []
        for y in ("2022", "2023", "2024", "2025", "2026"):
            if y in ys:
                r = ys[y]["return"]
                cells.append(f"{r * 100:+7.1f}%")
            else:
                cells.append(f"{'—':>8s}")
        print(f"{coin:5s} {mode:6s} {int(d['liquidated']):3d} {d['total_return_mult']:8.3f} " + " ".join(cells))
