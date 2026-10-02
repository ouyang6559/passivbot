"""HSL-10% rerun of the 45 single-coin regime_1x backtests (full history).

Protocol (user-specified): identical to the original annual-comparison runs
(same configs, same windows, 100k starting balance) with one parameter delta:
- bot.{pside}.hsl.enabled = true (active psides only)
- bot.{pside}.hsl.red_threshold = 0.10  (equity hard stop at -10% drawdown)
- bot.{pside}.hsl.panic_close_order_type = "market"
- bot.{pside}.hsl.cooldown_minutes_after_red = 1440  (0 would halt the side
  forever; 1 day gives the requested "force-close, then start a sequel")

If an episode is still liquidated (equity -> 5% of starting balance; HSL can
be slipped by fast moves through the EMA smoothing), record the date and
resume a fresh episode (starting balance resets) the next day, until the
window end. Everything else is untouched relative to configs/local/regime_1x_bt.

Resumable: regime1x/hsl10_results.json.
"""
import json
import subprocess
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

R1X = Path(__file__).parent
BASE = Path("configs/local/regime_1x_bt")
OUT = Path("configs/local/regime_1x_hsl10")
BT = Path("backtests/binance")
END = date(2026, 10, 1)
COINS = ["BTC", "ETH", "SOL"]
REGIMES = ["normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"]
SIDES = ["long", "short", "both"]


def make_cfg(coin: str, regime: str, side: str) -> Path:
    dst = OUT / coin / regime
    dst.mkdir(parents=True, exist_ok=True)
    path = dst / f"{side}.json"
    if path.exists():
        return path
    cfg = json.loads((BASE / coin / regime / f"{side}.json").read_text())
    for pside in ("long", "short"):
        active = (pside == "long") == (side in ("long", "both"))
        hsl = cfg["bot"][pside]["hsl"]
        hsl["enabled"] = bool(active)
        if active:
            hsl["red_threshold"] = 0.10
            hsl["panic_close_order_type"] = "market"
            hsl["cooldown_minutes_after_red"] = 1440.0
    path.write_text(json.dumps(cfg, indent=4))
    return path


def episode_cfg(path: Path, start: date, end: date) -> Path:
    cfg = json.loads(path.read_text())
    cfg["backtest"]["start_date"] = start.isoformat()
    cfg["backtest"]["end_date"] = end.isoformat()
    ep_dir = OUT / "_episodes"
    ep_dir.mkdir(parents=True, exist_ok=True)
    ep_path = ep_dir / f"{path.parent.parent.name}_{path.parent.name}_{path.stem}_{start}_{end}.json"
    ep_path.write_text(json.dumps(cfg, indent=4))
    return ep_path


def run_backtest(cfg_path: Path) -> tuple[dict, Path]:
    before = {p for p in BT.iterdir() if p.is_dir()}
    proc = subprocess.run(
        ["./venv/bin/passivbot", "backtest", str(cfg_path)],
        capture_output=True, text=True, timeout=14400,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-300:])
    ours = json.loads(cfg_path.read_text())
    new = sorted(p for p in BT.iterdir() if p.is_dir() and p not in before)
    for d in reversed(new):
        try:
            dc = json.loads((d / "config.json").read_text())
            if (dc["backtest"]["start_date"] == ours["backtest"]["start_date"]
                    and dc["backtest"]["end_date"] == ours["backtest"]["end_date"]):
                return json.loads((d / "analysis.json").read_text()), d
        except Exception:  # noqa: BLE001
            continue
    raise RuntimeError(f"no matching new run dir among {len(new)}")


def run_series(coin: str, regime: str, side: str) -> dict:
    base = make_cfg(coin, regime, side)
    start0 = date.fromisoformat(json.loads(base.read_text())["backtest"]["start_date"])
    episodes = []
    cursor = start0
    while cursor <= END:
        cfg_path = episode_cfg(base, cursor, END)
        a, run_dir = run_backtest(cfg_path)
        eq = pd.read_csv(Path(run_dir) / "balance_and_equity.csv.gz")
        eq["dt"] = pd.to_datetime(eq["Unnamed: 0"])
        end_dt = eq["dt"].iloc[-1].date()
        end_equity = float(eq["usd_total_equity"].iloc[-1])
        liq = bool(a.get("liquidated"))
        episodes.append({
            "start": cursor.isoformat(), "end": end_dt.isoformat(),
            "run_dir": str(run_dir), "liquidated": liq,
            "end_equity": round(end_equity, 0),
        })
        print(f"    episode {cursor} -> {end_dt} liq={liq} eq={end_equity:,.0f}", flush=True)
        cursor = end_dt + timedelta(days=1) if liq else END + timedelta(days=1)
    return {"episodes": episodes, "n_liquidations": sum(1 for e in episodes if e["liquidated"]),
            "n_episodes": len(episodes)}


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else None  # e.g. "BTC/normal_osc/short"
    results_path = R1X / "hsl10_results.json"
    results = json.loads(results_path.read_text()) if results_path.exists() else {}
    jobs = [(c, r, s) for c in COINS for r in REGIMES for s in SIDES]
    if only:
        jobs = [j for j in jobs if "/".join(j) == only]
    for i, (coin, regime, side) in enumerate(jobs):
        key = f"{coin}/{regime}/{side}"
        if results.get(key, {}).get("episodes"):
            print(f"[{i+1}/{len(jobs)}] {key}: done, skip", flush=True)
            continue
        print(f"[{i+1}/{len(jobs)}] == {key}", flush=True)
        t0 = time.time()
        try:
            results[key] = run_series(coin, regime, side)
            results[key]["seconds"] = round(time.time() - t0, 1)
            print(f"    done in {results[key]['seconds']}s, "
                  f"{results[key]['n_episodes']} episode(s), "
                  f"{results[key]['n_liquidations']} liquidation(s)", flush=True)
        except Exception as e:  # noqa: BLE001 - record, retry next launch
            results[key] = {"error": str(e)[:300]}
            print(f"    FAILED {str(e)[:150]}", flush=True)
        results_path.write_text(json.dumps(results, indent=2))
    n_liq = sum(v.get("n_liquidations", 0) for v in results.values() if "episodes" in v)
    print(f"batch finished: {sum(1 for v in results.values() if 'episodes' in v)}/{len(jobs)} "
          f"configs, {n_liq} total liquidation(s)", flush=True)


if __name__ == "__main__":
    import sys
    main()
