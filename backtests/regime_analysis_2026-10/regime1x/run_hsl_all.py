"""HSL-enabled re-run of the 45 regime_1x backtests with liquidation-episode protocol.

Protocol (user-specified, follows run_eth_v2h_episodes.py):
- same 45-config grid as the baseline full-history runs (BTC/ETH/SOL x 5 regimes x
  long/short/both), same start dates and local 1m data (configs/local/regime_1x_bt),
- only change vs baseline: bot.{pside}.hsl.enabled = true on the active side(s);
  every other HSL parameter keeps the config's own value,
- each config runs continuously; if liquidated (equity -> 5% of starting balance),
  record the date and start a fresh episode (starting balance reset to 100k) the next
  day, until the window end (2026-10-01),
- annual stats (return / worst drawdown / Sharpe / fills) computed on the stitched
  normalized equity curve, following compute_annual_stats.py.

Resumable: regime1x/hsl_episodes.json (per-config), written after every episode.
Usage:
  python run_hsl_all.py                # all pending configs, 3 coins in parallel
  python run_hsl_all.py --only BTC/normal_osc/short
  python run_hsl_all.py --stats-only   # recompute hsl_annual_stats.json from run dirs
"""
import argparse
import json
import subprocess
import threading
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

R1X = Path(__file__).parent
BASE = Path("configs/local/regime_1x_bt")
OUT = Path("configs/local/regime_1x_hsl")
BT = Path("backtests/binance")
WINDOW_END = date(2026, 10, 1)
COINS = ["BTC", "ETH", "SOL"]
REGIMES = ["normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"]
SIDES = ["long", "short", "both"]
START_BALANCE = 100_000.0

_results_lock = threading.Lock()


def make_cfg(coin: str, regime: str, side: str) -> Path:
    dst = OUT / coin / regime
    dst.mkdir(parents=True, exist_ok=True)
    path = dst / f"{side}.json"
    if path.exists():
        return path
    cfg = json.loads((BASE / coin / regime / f"{side}.json").read_text())
    for pside in ("long", "short"):
        active = (pside == "long") == (side in ("long", "both"))
        cfg["bot"][pside]["hsl"]["enabled"] = bool(active)
    path.write_text(json.dumps(cfg, indent=4))
    return path


def episode_cfg(coin: str, regime: str, side: str, start: date, end: date) -> Path:
    cfg = json.loads(make_cfg(coin, regime, side).read_text())
    cfg["backtest"]["start_date"] = start.isoformat()
    cfg["backtest"]["end_date"] = end.isoformat()
    ep_dir = OUT / "_episodes"
    ep_dir.mkdir(parents=True, exist_ok=True)
    path = ep_dir / f"{coin}_{regime}_{side}_{start}_{end}.json"
    path.write_text(json.dumps(cfg, indent=4))
    return path


def run_backtest(cfg_path: Path) -> tuple[dict, Path]:
    before = {p for p in BT.iterdir() if p.is_dir()}
    ours = json.loads(cfg_path.read_text())
    proc = subprocess.run(
        ["./venv/bin/passivbot", "backtest", str(cfg_path), "-dp"],
        capture_output=True, text=True, timeout=14400,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-300:])
    # match on identical config contents (parallel runs share the timestamped dirs)
    want = json.dumps(ours, sort_keys=True)
    new = sorted(p for p in BT.iterdir() if p.is_dir() and p not in before)
    for d in reversed(new):
        try:
            dc = json.loads((d / "config.json").read_text())
            if json.dumps(dc, sort_keys=True) == want:
                return json.loads((d / "analysis.json").read_text()), d
        except Exception:  # noqa: BLE001 - try next dir
            continue
    raise RuntimeError(f"no matching new run dir among {len(new)}")


def run_series(coin: str, regime: str, side: str) -> dict:
    key = f"{coin}/{regime}/{side}"
    start = date.fromisoformat(
        json.loads((BASE / coin / regime / f"{side}.json").read_text())
        ["backtest"]["start_date"])
    episodes = []
    cursor = start
    while cursor <= WINDOW_END:
        cfg = episode_cfg(coin, regime, side, cursor, WINDOW_END)
        a, run_dir = run_backtest(cfg)
        eq = pd.read_csv(Path(run_dir) / "balance_and_equity.csv.gz")
        eq["dt"] = pd.to_datetime(eq["Unnamed: 0"])
        end_dt = eq["dt"].iloc[-1].date()
        end_equity = float(eq["usd_total_equity"].iloc[-1])
        liq = bool(a.get("liquidated"))
        s = eq.set_index("dt")["usd_total_equity"]
        yr = {}
        for y, seg in s.groupby(s.index.year):
            yr[str(int(y))] = round(float(seg.iloc[-1] / seg.iloc[0] - 1.0), 4)
        fills = pd.read_csv(Path(run_dir) / "fills.csv", parse_dates=["timestamp"])
        ep = {
            "start": cursor.isoformat(), "end": end_dt.isoformat(),
            "liquidated": liq, "end_equity": round(end_equity, 0),
            "run_dir": str(Path(run_dir).resolve()),
            "n_fills": int(len(fills)),
            "year_returns": yr,
        }
        episodes.append(ep)
        print(f"  [{key}] episode {cursor} -> {end_dt} liq={liq} eq={end_equity:,.0f}",
              flush=True)
        if liq:
            cursor = end_dt + timedelta(days=1)
        else:
            break
    return {
        "episodes": episodes,
        "n_liquidations": sum(1 for e in episodes if e["liquidated"]),
        "liquidation_dates": [e["end"] for e in episodes if e["liquidated"]],
    }


def coin_worker(coin: str, keys: list[str], results: dict, results_path: Path):
    for key in keys:
        c, regime, side = key.split("/")
        try:
            t0 = time.time()
            res = run_series(c, regime, side)
            res["seconds"] = round(time.time() - t0, 1)
            with _results_lock:
                results[key] = res
                results_path.write_text(json.dumps(results, indent=2))
            yr = res["episodes"][-1]["year_returns"]
            print(f"[{key}] OK {res['seconds']}s liq={res['n_liquidations']} "
                  f"episodes={len(res['episodes'])}", flush=True)
        except Exception as e:  # noqa: BLE001 - record, retry on relaunch
            with _results_lock:
                results[key] = {"error": str(e)[:300],
                                "attempts": results.get(key, {}).get("attempts", 0) + 1}
                results_path.write_text(json.dumps(results, indent=2))
            print(f"[{key}] FAILED: {str(e)[:150]}", flush=True)


def compute_stats(results: dict) -> dict:
    """Annual stats on the stitched normalized equity curve (compute_annual_stats
    methodology; each episode normalized to its own start, liquidations count as
    the -95% they are)."""
    out = {}
    for key, v in sorted(results.items()):
        if not v.get("episodes"):
            continue
        coin, regime, side = key.split("/")
        frames, rets, fill_years, liq_years = [], [], {}, set()
        for ep in v["episodes"]:
            df = pd.read_csv(Path(ep["run_dir"]) / "balance_and_equity.csv.gz")
            df["dt"] = pd.to_datetime(df["Unnamed: 0"])
            s = df.set_index("dt")["usd_total_equity"]
            frames.append(s / s.iloc[0])
            rets.append(s.pct_change().clip(-0.5, 0.5).dropna())
            fills = pd.read_csv(Path(ep["run_dir"]) / "fills.csv",
                                parse_dates=["timestamp"])
            for y, n in fills["timestamp"].dt.year.value_counts().items():
                fill_years[int(y)] = fill_years.get(int(y), 0) + n
            if ep["liquidated"]:
                liq_years.add(int(ep["end"][:4]))
        eq = pd.concat(frames)
        eq = eq.groupby(eq.index).last()
        ret_h = pd.concat(rets).sort_index()
        years = {}
        for y, seg in eq.groupby(eq.index.year):
            r = ret_h.loc[ret_h.index.year == y]
            dd = float((seg / seg.cummax() - 1.0).min())
            if y in liq_years:
                dd = min(dd, -0.95)
            sharpe = (float(r.mean() / r.std() * (24 * 365) ** 0.5)
                      if len(r) > 1 and r.std() > 0 else 0.0)
            year_ret = 1.0
            for ep in v["episodes"]:
                if y in ep["year_returns"]:
                    year_ret *= 1.0 + ep["year_returns"][str(y)]
            years[str(y)] = {
                "return": round(year_ret - 1.0, 4),
                "worst_dd": round(dd, 4),
                "sharpe": round(sharpe, 2),
                "n_fills": int(fill_years.get(y, 0)),
            }
        out[key] = {
            "n_liquidations": v["n_liquidations"],
            "liquidation_dates": v["liquidation_dates"],
            "final_equity_multiple": round(float(eq.iloc[-1]), 4),
            "years": years,
        }
    (R1X / "hsl_annual_stats.json").write_text(json.dumps(out, indent=2))
    print(f"saved hsl_annual_stats.json ({len(out)} configs)", flush=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="restrict to one COIN/REGIME/SIDE key")
    ap.add_argument("--stats-only", action="store_true")
    args = ap.parse_args()
    results_path = R1X / "hsl_episodes.json"
    results = json.loads(results_path.read_text()) if results_path.exists() else {}
    if args.stats_only:
        compute_stats(results)
        return
    all_keys = [f"{c}/{r}/{s}" for c in COINS for r in REGIMES for s in SIDES]
    if args.only:
        all_keys = [args.only]
    pending = [k for k in all_keys if not results.get(k, {}).get("episodes")]
    print(f"{len(all_keys) - len(pending)} done, {len(pending)} pending", flush=True)
    threads = []
    for coin in COINS:
        keys = [k for k in pending if k.startswith(coin + "/")]
        if keys:
            t = threading.Thread(target=coin_worker, args=(coin, keys, results,
                                                           results_path))
            t.start()
            threads.append(t)
    for t in threads:
        t.join()
    done = [k for k, v in results.items() if v.get("episodes")]
    print(f"batch finished: {len(done)}/{len(all_keys)} complete", flush=True)
    compute_stats(results)


if __name__ == "__main__":
    main()
