"""2022-01-01 -> 2026-10-01 windowed short/both backtests for BTC/ETH/SOL.

The 2019/2020 starts liquidated every short/both config during the 2020-2021
bull; this rerun starts after that era. Configs derive from
configs/local/regime_1x_bt (local ohlcv source) with shifted dates.
Resumable: results in regime1x/results_2022_sb.json, completed keys skipped.
"""
import json
import subprocess
import time
from pathlib import Path

R1X = Path(__file__).parent
LOCAL = Path("configs/local/regime_1x_bt")
OUT = Path("configs/local/regime_1x_bt_2022")
BT = Path("backtests/binance")
COINS = ["BTC", "ETH", "SOL"]
REGIMES = ["normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"]
SIDES = ["long", "short", "both"]
START, END = "2022-01-01", "2026-10-01"
METRICS = [
    "adg_pnl", "mdg_pnl", "drawdown_worst_usd", "loss_profit_ratio",
    "peak_recovery_hours_pnl", "position_held_hours_max",
    "position_unchanged_hours_max", "volume_pct_per_day_avg_w",
]
GUARDS = ["backtest_completion_ratio", "liquidated"]


def make_cfg(coin, regime, side) -> Path:
    dst = OUT / coin / regime
    dst.mkdir(parents=True, exist_ok=True)
    path = dst / f"{side}.json"
    if path.exists():
        return path
    cfg = json.loads((LOCAL / coin / regime / f"{side}.json").read_text())
    cfg["backtest"]["start_date"] = START
    cfg["backtest"]["end_date"] = END
    path.write_text(json.dumps(cfg, indent=4))
    return path


def pick_run_dir(before: set, coin: str) -> Path:
    new = sorted({p for p in BT.iterdir() if p.is_dir()} - before)
    for d in reversed(new):
        try:
            ds = json.loads((d / "dataset.json").read_text())
            (d / "analysis.json").read_text()
            if set(ds.get("coins", [])) == {coin}:
                return d
        except Exception:  # noqa: BLE001
            continue
    raise RuntimeError(f"no new run dir for {coin} among {new}")


def run_one(coin, regime, side) -> dict:
    cfg = make_cfg(coin, regime, side)
    before = {p for p in BT.iterdir() if p.is_dir()}
    t0 = time.time()
    proc = subprocess.run(
        ["./venv/bin/passivbot", "backtest", str(cfg)],
        capture_output=True, text=True, timeout=7200,
    )
    if proc.returncode != 0:
        (R1X / "logs").mkdir(exist_ok=True)
        (R1X / "logs" / f"2022_{coin}_{regime}_{side}.log").write_text(
            proc.stdout + "\n=== STDERR ===\n" + proc.stderr)
        raise RuntimeError(f"exit {proc.returncode}")
    run_dir = pick_run_dir(before, coin)
    a = json.loads((run_dir / "analysis.json").read_text())
    out = {"run_dir": str(run_dir), "seconds": round(time.time() - t0, 1)}
    out.update({m: a.get(m) for m in METRICS})
    out.update({g: a.get(g) for g in GUARDS})
    out["n_fills"] = a.get("fills_count")
    return out


def main():
    results_path = R1X / "results_2022_sb.json"
    results = json.loads(results_path.read_text()) if results_path.exists() else {}
    jobs = [(c, r, s) for c in COINS for r in REGIMES for s in SIDES]
    for i, (coin, regime, side) in enumerate(jobs):
        key = f"{coin}/{regime}/{side}.json"
        if results.get(key, {}).get("analysis_metrics_done"):
            continue
        try:
            res = run_one(coin, regime, side)
            res["analysis_metrics_done"] = True
            results[key] = res
            print(f"[{i + 1}/{len(jobs)}] {key} OK {res['seconds']}s "
                  f"adg={res['adg_pnl']:+.5f} dd={res['drawdown_worst_usd']:.3f} "
                  f"liq={res['liquidated']}", flush=True)
        except Exception as e:  # noqa: BLE001
            results[key] = {"error": str(e)[:200]}
            print(f"[{i + 1}/{len(jobs)}] {key} FAILED: {str(e)[:120]}", flush=True)
        results_path.write_text(json.dumps(results, indent=2))
    done = [k for k, v in results.items() if v.get("analysis_metrics_done")]
    print(f"batch finished: {len(done)}/{len(jobs)} complete", flush=True)


if __name__ == "__main__":
    main()
