"""Resumable batch runner for the 105 regime_1x backtests (2019 -> now).

Resume contract:
- progress lives in regime1x/results.json; entries with a valid 'analysis' are skipped,
  entries with 'error' are retried on the next launch, partially-written entries are
  overwritten. Relaunching this script always continues where the previous run stopped.
- runs are ordered coin-first so each coin's 1m history is downloaded once and reused
  by its 15 configs (same data window/exchange/coin -> same prepared cache).
- after each run, dataset.json must contain exactly the config's coin; otherwise the
  run is retried once with --force-refetch-gaps (guards the hash-suffix cache bug).
"""
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent  # regime_analysis_2026-10
R1X = ROOT / "regime1x"  # this script's directory
CFG_ROOT = Path.cwd() / "configs" / "regime_1x"
BT = Path.cwd() / "backtests" / "binance"

MANIFEST = json.loads((R1X / "manifest.json").read_text())
COINS_ORDER = ["BTC", "ETH", "XRP", "SOL", "ADA", "DOGE", "LINK"]
# Local freqtrade-derived candles cover these coins only; their run configs live
# under configs/local/regime_1x_bt with ohlcv_source_dir set. Coins without a
# local run config are skipped (recorded as pending) instead of hitting the
# public API for 7 years of 1m data.
LOCAL_CFG_ROOT = Path.cwd() / "configs" / "local" / "regime_1x_bt"


def resolve_cfg_path(item) -> Path | None:
    local = LOCAL_CFG_ROOT / item["config"]
    return local if local.exists() else None
METRICS = [
    "adg_pnl", "mdg_pnl", "drawdown_worst_usd", "loss_profit_ratio",
    "peak_recovery_hours_pnl", "position_held_hours_max",
    "position_unchanged_hours_max", "volume_pct_per_day_avg_w",
]
GUARDS = ["backtest_completion_ratio", "liquidated"]


def coin_runs():
    by_coin = {c: [] for c in COINS_ORDER}
    for item in MANIFEST:
        by_coin.setdefault(item["coin"], []).append(item)
    for c in COINS_ORDER:
        yield from by_coin.get(c, [])


def invoke(cfg_path: str, force: bool) -> subprocess.CompletedProcess:
    cmd = ["./venv/bin/passivbot", "backtest", cfg_path, "-dp"]
    if force:
        cmd.append("--force-refetch-gaps")
    return subprocess.run(cmd, capture_output=True, text=True, timeout=14400)


def pick_run_dir(before: set, coin: str) -> Path:
    new = sorted({p for p in BT.iterdir() if p.is_dir()} - before)
    for d in reversed(new):
        try:
            ds = json.loads((d / "dataset.json").read_text())
            (d / "analysis.json").read_text()
            if set(ds.get("coins", [])) == {coin}:
                return d
        except Exception:  # noqa: BLE001 - try next dir
            continue
    raise RuntimeError(f"no new run dir for {coin} among {new}")


def run_one(item) -> dict:
    coin = item["coin"]
    cfg_path = str(resolve_cfg_path(item))
    before = {p for p in BT.iterdir() if p.is_dir()}
    t0 = time.time()
    proc = invoke(cfg_path, force=False)
    log = proc.stdout + "\n=== STDERR ===\n" + proc.stderr
    if proc.returncode != 0:
        (R1X / "logs" ).mkdir(exist_ok=True)
        (R1X / "logs" / f"{coin}_{item['regime']}_{item['direction']}.log").write_text(log)
        raise RuntimeError(f"exit {proc.returncode}")
    try:
        run_dir = pick_run_dir(before, coin)
    except RuntimeError:
        proc = invoke(cfg_path, force=True)
        log += "\n=== FORCED RETRY ===\n" + proc.stdout + proc.stderr
        if proc.returncode != 0:
            raise RuntimeError(f"forced exit {proc.returncode}")
        run_dir = pick_run_dir(before, coin)
    analysis = json.loads((run_dir / "analysis.json").read_text())
    (R1X / "logs").mkdir(exist_ok=True)
    (R1X / "logs" / f"{coin}_{item['regime']}_{item['direction']}.log").write_text(log[-8000:])
    out = {"run_dir": str(run_dir), "seconds": round(time.time() - t0, 1)}
    out.update({m: analysis.get(m) for m in METRICS})
    out.update({g: analysis.get(g) for g in GUARDS})
    out["n_fills"] = analysis.get("fills_count")
    return out


def main():
    results_path = R1X / "results.json"
    results = json.loads(results_path.read_text()) if results_path.exists() else {}
    pending = [it for it in coin_runs()
               if resolve_cfg_path(it) is not None
               and not results.get(it["config"], {}).get("analysis_metrics_done")]
    skipped = sorted({it["coin"] for it in coin_runs() if resolve_cfg_path(it) is None})
    if skipped:
        print(f"skipping coins without local data/configs: {', '.join(skipped)}", flush=True)
    done = len([k for k, v in results.items() if v.get("analysis_metrics_done")])
    print(f"{done} done, {len(pending)} pending", flush=True)
    for i, item in enumerate(pending):
        key = item["config"]
        try:
            res = run_one(item)
            res["analysis_metrics_done"] = True
            results[key] = res
            print(f"[{i+1}/{len(pending)}] {key} OK {res['seconds']}s "
                  f"adg={res['adg_pnl']:.4f} dd={res['drawdown_worst_usd']:.3f} "
                  f"lpr={res['loss_profit_ratio']:.3f}", flush=True)
        except Exception as e:  # noqa: BLE001 - record, retry next launch
            results[key] = {"error": str(e)[:200], "attempts": results.get(key, {}).get("attempts", 0) + 1}
            print(f"[{i+1}/{len(pending)}] {key} FAILED: {e}", flush=True)
        results_path.write_text(json.dumps(results, indent=2))
    done = [k for k, v in results.items() if v.get("analysis_metrics_done")]
    print(f"batch finished: {len(done)}/{len(MANIFEST)} complete", flush=True)


if __name__ == "__main__":
    main()
