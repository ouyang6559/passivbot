"""Annual stats for the HSL-10% rerun (episode-aware).

Reads hsl10_results.json; for every config chains its episodes into
per-calendar-year statistics. Episode boundaries (fresh 100k sequel after a
liquidation) are handled the same way as eth_v2h_episodes: a year return is
the product of within-episode calendar-year segment ratios; drawdown and
Sharpe are computed within episodes only (a sequel deposit is new capital,
not a gain). 期末资金 is the synthetic compounded wallet 100k * prod(1+r_year).

Also counts HSL red events per year: panic fills that flatten the position.
Saves hsl10_annual_stats.json and prints a digest.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

R1X = Path(__file__).parent
START_BALANCE = 100_000.0


def load_eq(run_dir: str) -> pd.Series:
    df = pd.read_csv(Path(run_dir) / "balance_and_equity.csv.gz")
    df["dt"] = pd.to_datetime(df["Unnamed: 0"])
    return df.set_index("dt")["usd_total_equity"]


def red_events_per_year(run_dir: str) -> dict:
    f = pd.read_csv(Path(run_dir) / "fills.csv",
                    usecols=["timestamp", "type", "psize"], parse_dates=["timestamp"])
    panic = f[f["type"].str.startswith("close_panic")]
    flat = panic[panic["psize"] == 0.0]  # panic fill that fully closed the side
    return flat["timestamp"].dt.year.value_counts().to_dict()


def main():
    results = json.loads((R1X / "hsl10_results.json").read_text())
    out = {}
    for key, v in sorted(results.items()):
        if "episodes" not in v:
            continue
        coin, regime, side = key.split("/")
        year_ratio: dict[int, float] = {}
        year_rets: dict[int, list] = {}
        year_dd: dict[int, float] = {}
        year_fills: dict[int, int] = {}
        year_reds: dict[int, int] = {}
        for ep in v["episodes"]:
            eq = load_eq(ep["run_dir"])
            rets = eq.pct_change().clip(-0.5, 0.5)
            fills = pd.read_csv(Path(ep["run_dir"]) / "fills.csv",
                                usecols=["timestamp"], parse_dates=["timestamp"])
            fill_years = fills["timestamp"].dt.year.value_counts().to_dict()
            for y, cnt in red_events_per_year(ep["run_dir"]).items():
                year_reds[int(y)] = year_reds.get(int(y), 0) + int(cnt)
            for year, seg in eq.groupby(eq.index.year):
                y = int(year)
                year_ratio[y] = year_ratio.get(y, 1.0) * (seg.iloc[-1] / seg.iloc[0])
                year_rets.setdefault(y, []).extend(rets.loc[seg.index].tolist())
                dd = float((seg / seg.cummax() - 1.0).min())
                year_dd[y] = min(year_dd.get(y, 0.0), dd)
                year_fills[y] = year_fills.get(y, 0) + int(fill_years.get(year, 0))
        wallet = START_BALANCE
        years = {}
        for y in sorted(year_ratio):
            r = year_ratio[y] - 1.0
            wallet *= year_ratio[y]
            arr = np.array(year_rets[y])
            sharpe = float(arr.mean() / arr.std() * (24 * 365) ** 0.5) if arr.std() > 0 else 0.0
            years[str(y)] = {
                "return": round(r, 4),
                "end_equity": round(wallet, 0),
                "worst_dd": round(year_dd[y], 4),
                "sharpe": round(sharpe, 2),
                "n_fills": year_fills.get(y, 0),
                "hsl_red_events": year_reds.get(y, 0),
            }
        out[key] = {
            "n_episodes": v["n_episodes"],
            "n_liquidations": v["n_liquidations"],
            "liquidation_dates": [e["end"] for e in v["episodes"] if e["liquidated"]],
            "final_equity_multiple": round(wallet / START_BALANCE, 4),
            "start_year": min(int(y) for y in year_ratio),
            "end": max(e["end"] for e in v["episodes"]),
            "years": years,
        }
    (R1X / "hsl10_annual_stats.json").write_text(json.dumps(out, indent=2))
    print(f"saved hsl10_annual_stats.json ({len(out)} configs)")
    for coin in ("BTC", "ETH", "SOL"):
        for side in ("long", "short", "both"):
            for regime in ("normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"):
                k = f"{coin}/{regime}/{side}"
                if k not in out:
                    continue
                ys = out[k]["years"]
                s = " ".join(f"{y}:{d['return']:+.1%}" for y, d in sorted(ys.items()))
                reds = sum(d["hsl_red_events"] for d in ys.values())
                print(f"{coin:4s} {side:5s} {regime:12s} liq={out[k]['n_liquidations']} "
                      f"reds={reds:3d} final={out[k]['final_equity_multiple']:.2f}x {s}")


if __name__ == "__main__":
    main()
