"""Run the 39 pack39 backtests sequentially. Resumable via results.json.

Each run is a single coin / single mode (long, short, both) over
2022-01-01 .. 2026-10-02 on local 1m data (caches/ft_source).
"""
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).parent
CONFIGS = ROOT / "pack39" / "configs"
BT = Path("backtests/binance")
COINS = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "LINK", "DOT", "UNI", "LTC", "XMR"]
MODES = ["long", "short", "both"]
METRICS = [
    "adg_pnl", "mdg_pnl", "drawdown_worst_usd", "loss_profit_ratio",
    "peak_recovery_hours_pnl", "position_held_hours_max",
    "position_unchanged_hours_max", "volume_pct_per_day_avg_w",
]
GUARDS = ["backtest_completion_ratio", "liquidated"]


def pick_run_dir(before: set, cfg_path: Path) -> Path:
    """Newest new run dir whose config's approved_coins match the intended config."""
    intended = json.loads(cfg_path.read_text())["live"]["approved_coins"]
    new = sorted({p for p in BT.iterdir() if p.is_dir()} - before)
    for d in reversed(new):
        try:
            run_cfg = json.loads((d / "config.json").read_text())
            if run_cfg["live"]["approved_coins"] != intended:
                continue
            ds = json.loads((d / "dataset.json").read_text())
            (d / "analysis.json").read_text()
            if set(ds.get("coins", [])) == set(intended.get("long", [])) | set(intended.get("short", [])):
                return d
        except Exception:  # noqa: BLE001
            continue
    raise RuntimeError(f"no new run dir matching {intended} among {new}")


def run_one(coin: str, mode: str) -> dict:
    cfg_path = CONFIGS / coin / f"{mode}.json"
    before = {p for p in BT.iterdir() if p.is_dir()}
    t0 = time.time()
    proc = subprocess.run(
        ["./venv/bin/passivbot", "backtest", str(cfg_path)],
        capture_output=True, text=True, timeout=7200,
    )
    if proc.returncode != 0:
        logdir = ROOT / "pack39" / "logs"
        logdir.mkdir(exist_ok=True)
        (logdir / f"{coin}_{mode}.log").write_text(proc.stdout + "\n=== STDERR ===\n" + proc.stderr)
        raise RuntimeError(f"exit {proc.returncode}")
    run_dir = pick_run_dir(before, cfg_path)
    a = json.loads((run_dir / "analysis.json").read_text())
    out = {"run_dir": str(run_dir), "seconds": round(time.time() - t0, 1)}
    out.update({m: a.get(m) for m in METRICS})
    out.update({g: a.get(g) for g in GUARDS})
    out["n_fills"] = a.get("fills_count")
    return out


def main():
    results_path = ROOT / "pack39" / "results.json"
    results = json.loads(results_path.read_text()) if results_path.exists() else {}
    jobs = [(c, m) for c in COINS for m in MODES]
    for i, (coin, mode) in enumerate(jobs):
        key = f"{coin}/{mode}"
        if results.get(key, {}).get("analysis_metrics_done"):
            continue
        try:
            res = run_one(coin, mode)
            res["analysis_metrics_done"] = True
            results[key] = res
            print(f"[{i + 1}/{len(jobs)}] {key} OK {res['seconds']}s "
                  f"adg={res['adg_pnl']:+.5f} dd={res['drawdown_worst_usd']:.3f} "
                  f"liq={res['liquidated']} completion={res['backtest_completion_ratio']}", flush=True)
        except Exception as e:  # noqa: BLE001
            results[key] = {"error": str(e)[:200]}
            print(f"[{i + 1}/{len(jobs)}] {key} FAILED: {str(e)[:150]}", flush=True)
        results_path.write_text(json.dumps(results, indent=2))
    done = [k for k, v in results.items() if v.get("analysis_metrics_done")]
    print(f"batch finished: {len(done)}/{len(jobs)} complete", flush=True)


if __name__ == "__main__":
    main()
