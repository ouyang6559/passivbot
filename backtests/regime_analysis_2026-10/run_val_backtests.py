"""Run the 10 validation backtests sequentially and collect metrics.

Guards against the cache-hash-vs-coins mismatch bug (cache dirs match by hash
suffix only; a cache materialized with fewer coins than requested still loads):
- first run of each window uses --force-refetch-gaps to rebuild in place,
- after every run, dataset.json must contain all 5 coins, else the run is
  retried once with --force-refetch-gaps.
"""
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).parent
RUNS = ROOT / "backtest_runs"
BT = Path("backtests/binance")
MANIFEST = json.loads((RUNS / "manifest.json").read_text())
COINS = {"BTC", "ETH", "XRP", "SOL", "ADA"}


def newest_run_dir(before: set) -> Path:
    new = sorted({p for p in BT.iterdir() if p.is_dir()} - before)
    if not new:
        raise RuntimeError("no new backtest dir")
    # one invocation may emit more than one result dir (engine re-preparation);
    # prefer the newest whose dataset covers all coins and has analysis.json
    for d in reversed(new):
        try:
            ds = json.loads((d / "dataset.json").read_text())
            (d / "analysis.json").read_text()
            if COINS.issubset(set(ds.get("coins", []))):
                return d
        except Exception:  # noqa: BLE001 - try next dir
            continue
    raise RuntimeError(f"no new backtest dir with full coin coverage among {new}")


def invoke(cfg: str, force: bool) -> subprocess.CompletedProcess:
    cmd = ["./venv/bin/passivbot", "backtest", cfg, "-dp"]
    if force:
        cmd.append("--force-refetch-gaps")
    return subprocess.run(cmd, capture_output=True, text=True, timeout=14400)


def run_one(name: str) -> dict:
    cfg = str(RUNS / name)
    before = {p for p in BT.iterdir() if p.is_dir()}
    t0 = time.time()
    proc = invoke(cfg, force=False)
    log = proc.stdout + "\n=== STDERR ===\n" + proc.stderr
    if proc.returncode != 0:
        (RUNS / f"{name}.log").write_text(log)
        raise RuntimeError(f"backtest failed: {name}")
    run_dir = newest_run_dir(before)
    ds = json.loads((run_dir / "dataset.json").read_text())
    if not COINS.issubset(set(ds.get("coins", []))):
        log += f"\n=== coin coverage violated: {ds.get('coins')} — retrying with force ===\n"
        proc = invoke(cfg, force=True)
        log += proc.stdout + "\n=== STDERR ===\n" + proc.stderr
        if proc.returncode != 0:
            (RUNS / f"{name}.log").write_text(log)
            raise RuntimeError(f"backtest failed on forced retry: {name}")
        run_dir = newest_run_dir(before)
        ds = json.loads((run_dir / "dataset.json").read_text())
        if not COINS.issubset(set(ds.get("coins", []))):
            (RUNS / f"{name}.log").write_text(log)
            raise RuntimeError(f"coins still missing after force: {ds.get('coins')}")
    (RUNS / f"{name}.log").write_text(log)
    analysis = json.loads((run_dir / "analysis.json").read_text())
    print(f"    {name}: {time.time() - t0:.0f}s coins={ds.get('coins')} -> {run_dir}", flush=True)
    return {"run_dir": str(run_dir), "seconds": round(time.time() - t0, 1),
            "coins": ds.get("coins"), "analysis": analysis}


def main():
    results_path = RUNS / "validation_results.json"
    results = json.loads(results_path.read_text()) if results_path.exists() else {}
    for name in MANIFEST:
        if name in results and "error" not in results[name]:
            print(f"skip {name}")
            continue
        try:
            results[name] = run_one(name)
        except Exception as e:  # noqa: BLE001 - record and continue
            print(f"FAILED {name}: {e}", flush=True)
            results[name] = {"error": str(e)}
        results_path.write_text(json.dumps(results, indent=2))
    print("all done")


if __name__ == "__main__":
    main()
