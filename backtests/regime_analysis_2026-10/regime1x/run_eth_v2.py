"""ETH v2 verification backtests (official CLI: ./venv/bin/passivbot backtest).

Implements the verification path from docs/针对性配置文件调参数.md §4 and REPORT.md §8.4:

1. long-side v2 configs (5 regimes) on full history  -> acceptance criteria:
   unstuck loss share < 80%, entry crop < 8%, adg_pnl >= baseline, dd <= baseline * 1.05
2. per-regime windowed backtests comparing long/short allocations (多空调配):
   v1 both baseline vs v2 allocation (long-only / long+small-short) on the same
   regime-representative windows.

v2 deltas are exactly the ones proposed in docs/针对性配置文件调参数.md §2 (long)
and §6.3 (short).  Nothing else is touched.

Outputs (all under regime1x/eth_v2/):
- results_v2.json       headline metrics per run label
- fills_stats_v2.json   fill-level stats per run label (analyze_eth_fills functions)
- runs/<label>/         copied fills.csv.gz + analysis.json + config.json per run
Resumable: labels with results already present are skipped.
"""
import gzip
import json
import shutil
import subprocess
import time
from copy import deepcopy
from pathlib import Path

import analyze_eth_fills as aef

R1X = Path(__file__).parent
V2 = R1X / "eth_v2"
V2.mkdir(exist_ok=True)
(V2 / "configs").mkdir(exist_ok=True)
(V2 / "runs").mkdir(exist_ok=True)
LOCAL = Path("configs/local/regime_1x_bt/ETH")
LOCAL_V2 = Path("configs/local/eth_v2_bt/ETH")
LOCAL_V2.mkdir(parents=True, exist_ok=True)
BT = Path("backtests/binance")

REGIMES = ["normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"]
FULL_START, FULL_END = "2019-11-28", "2026-10-01"

# ---- v2 deltas (bot.<pside> dotted paths), verbatim from the §2 / §6.3 tables ----
LONG_V2 = {
    "normal_osc": {
        "strategy.trailing_martingale.entry.initial_qty_pct": 0.026,
        "unstuck.threshold": 0.72,
        "unstuck.close_pct": 0.014,
    },
    "low_vol_osc": {
        "strategy.trailing_martingale.entry.initial_qty_pct": 0.030,
        "strategy.trailing_martingale.entry.threshold_base_pct": 0.017,
        "strategy.trailing_martingale.entry.double_down_factor": 0.72,
        "unstuck.threshold": 0.75,
        "unstuck.close_pct": 0.012,
    },
    "strong_trend": {
        "strategy.trailing_martingale.close.threshold_base_pct": 0.010,
        "unstuck.threshold": 0.75,
    },
    "bear": {
        "risk.we_excess_allowance_pct": 1.0,
    },
    "extreme_vol": {
        "risk.total_wallet_exposure_limit": 0.65,
        "strategy.trailing_martingale.entry.initial_qty_pct": 0.012,
    },
}
SHORT_V2 = {
    "normal_osc": {},  # §6.3: params cannot fix; exposure control only
    "low_vol_osc": {
        "strategy.trailing_martingale.entry.initial_qty_pct": 0.030,
        "strategy.trailing_martingale.entry.threshold_base_pct": 0.017,
        "strategy.trailing_martingale.entry.double_down_factor": 0.72,
        "unstuck.threshold": 0.75,
        "unstuck.close_pct": 0.012,
    },
    "strong_trend": {
        "strategy.trailing_martingale.close.threshold_base_pct": 0.006,
        "unstuck.threshold": 0.72,
    },
    "bear": {},        # §6.3: baseline already near-optimal
    "extreme_vol": {}, # §6.3: only full-history survivor, keep
}

WINDOWS = {  # representative windows from regime_windows.json
    "normal_osc": [("2023-10-13", "2024-05-15"), ("2023-02-09", "2023-07-21")],
    "low_vol_osc": [("2023-07-05", "2023-11-01")],
    "strong_trend": [("2025-07-16", "2025-09-08")],
    "bear": [("2025-10-17", "2026-04-20"), ("2022-08-27", "2023-01-24")],
    "extreme_vol": [("2021-05-03", "2021-05-25")],
}

# long TWEL / short TWEL per allocation label
ALLOC = {
    "Lonly": (None, 0.0),        # long TWEL from config (v1 or v2)
    "both_v1": (None, None),     # keep config as-is
    "L1_S0.5": (1.0, 0.5),
    "L0.7_S1": (0.7, 1.0),
    "L0.65_S0.5": (0.65, 0.5),
}


def set_path(node, dotted, value):
    parts = dotted.split(".")
    for p in parts[:-1]:
        node = node[p]
    node[parts[-1]] = value


def apply_deltas(bot_side, deltas):
    for dotted, value in deltas.items():
        set_path(bot_side, dotted, value)


def build_cfg(regime, kind, variant, start, end, alloc):
    """kind: long|both; variant: v1|v2. alloc: key into ALLOC or None."""
    src = LOCAL / regime / ("long.json" if kind == "long" else "both.json")
    cfg = json.loads(src.read_text())
    cfg["backtest"]["start_date"] = start
    cfg["backtest"]["end_date"] = end
    if variant == "v2":
        apply_deltas(cfg["bot"]["long"], LONG_V2[regime])
        if kind == "both":
            apply_deltas(cfg["bot"]["short"], SHORT_V2[regime])
    if alloc:
        lt, st = ALLOC[alloc]
        if lt is not None:
            cfg["bot"]["long"]["risk"]["total_wallet_exposure_limit"] = lt
        if st is not None:
            cfg["bot"]["short"]["risk"]["total_wallet_exposure_limit"] = st
    name = f"{regime}_{kind}_{variant}_{alloc or 'asis'}_{start}_{end}"
    path = LOCAL_V2 / f"{name}.json"
    path.write_text(json.dumps(cfg, indent=4))
    return path, name


def job_list():
    jobs = []
    # 1) full-history long-only v2 (acceptance criteria §4)
    for regime in REGIMES:
        jobs.append({"regime": regime, "kind": "long", "variant": "v2", "alloc": None,
                     "start": FULL_START, "end": FULL_END,
                     "label": f"longfull_v2/{regime}"})
    # 2) windowed allocation comparisons
    for regime, windows in WINDOWS.items():
        for w_i, (start, end) in enumerate(windows, 1):
            tag = f"w{w_i}"
            if regime == "extreme_vol":
                jobs.append({"regime": regime, "kind": "both", "variant": "v1", "alloc": None,
                             "start": start, "end": end, "label": f"{regime}/{tag}/both_v1"})
                jobs.append({"regime": regime, "kind": "both", "variant": "v2",
                             "alloc": "L0.65_S0.5", "start": start, "end": end,
                             "label": f"{regime}/{tag}/L0.65_S0.5_v2"})
                continue
            jobs.append({"regime": regime, "kind": "both", "variant": "v1", "alloc": None,
                         "start": start, "end": end, "label": f"{regime}/{tag}/both_v1"})
            jobs.append({"regime": regime, "kind": "both", "variant": "v2", "alloc": "Lonly",
                         "start": start, "end": end, "label": f"{regime}/{tag}/Lonly_v2"})
            alloc = {"normal_osc": "L1_S0.5", "low_vol_osc": "L1_S0.5",
                     "strong_trend": "L1_S0.5", "bear": "L0.7_S1"}[regime]
            variant = "v2"
            jobs.append({"regime": regime, "kind": "both", "variant": variant, "alloc": alloc,
                         "start": start, "end": end, "label": f"{regime}/{tag}/{alloc}_v2"})
    # 3) full-history both for the only surviving both family (extreme_vol)
    jobs.append({"regime": "extreme_vol", "kind": "both", "variant": "v2",
                 "alloc": "L0.65_S0.5", "start": FULL_START, "end": FULL_END,
                 "label": "extreme_vol/full/L0.65_S0.5_v2"})
    return jobs


def pick_run_dir() -> Path:
    dirs = sorted(p for p in BT.iterdir() if p.is_dir())
    for d in reversed(dirs):
        try:
            ds = json.loads((d / "dataset.json").read_text())
            (d / "analysis.json").read_text()
            if set(ds.get("coins", [])) == {"ETH"}:
                return d
        except Exception:  # noqa: BLE001
            continue
    raise RuntimeError("no ETH run dir found")


def save_run_artifacts(label: str, run_dir: Path):
    out = V2 / "runs" / label.replace("/", "__")
    out.mkdir(parents=True, exist_ok=True)
    with open(run_dir / "fills.csv", "rb") as f_in, gzip.open(out / "fills.csv.gz", "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    shutil.copy(run_dir / "analysis.json", out / "analysis.json")
    shutil.copy(run_dir / "config.json", out / "config.json")
    return out


def run_one(job) -> dict:
    cfg_path, name = build_cfg(job["regime"], job["kind"], job["variant"],
                               job["start"], job["end"], job["alloc"])
    t0 = time.time()
    proc = subprocess.run(["./venv/bin/passivbot", "backtest", str(cfg_path)],
                          capture_output=True, text=True, timeout=3600)
    if proc.returncode != 0:
        raise RuntimeError(f"exit {proc.returncode}: {proc.stderr[-300:]}")
    run_dir = pick_run_dir()
    analysis = json.loads((run_dir / "analysis.json").read_text())
    artifacts = save_run_artifacts(job["label"], run_dir)
    fills = aef.load(str(run_dir))[0]
    cfg = json.loads((run_dir / "config.json").read_text())
    fstats = {}
    for pside, enabled in (("long", job["kind"] in ("long", "both")),
                           ("short", job["kind"] == "both")):
        twel = cfg["bot"][pside]["risk"]["total_wallet_exposure_limit"]
        if enabled and twel > 0:
            fstats[pside] = aef.analyze_side(fills, pside)
    out = {
        "config": str(cfg_path), "run_dir": str(run_dir), "artifacts": str(artifacts),
        "seconds": round(time.time() - t0, 1),
        "window": [job["start"], job["end"]],
        "adg_pnl": analysis.get("adg_pnl"), "mdg_pnl": analysis.get("mdg_pnl"),
        "drawdown_worst_usd": analysis.get("drawdown_worst_usd"),
        "loss_profit_ratio": analysis.get("loss_profit_ratio"),
        "peak_recovery_hours_pnl": analysis.get("peak_recovery_hours_pnl"),
        "backtest_completion_ratio": analysis.get("backtest_completion_ratio"),
        "liquidated": analysis.get("liquidated"),
        "n_fills": analysis.get("fills_count"),
        "twel": {"long": cfg["bot"]["long"]["risk"]["total_wallet_exposure_limit"],
                 "short": cfg["bot"]["short"]["risk"]["total_wallet_exposure_limit"]},
        "fills_stats": fstats,
    }
    return out


def main():
    results_path = V2 / "results_v2.json"
    results = json.loads(results_path.read_text()) if results_path.exists() else {}
    jobs = job_list()
    pending = [j for j in jobs if j["label"] not in results]
    print(f"{len(results)} done, {len(pending)} pending", flush=True)
    for i, job in enumerate(pending):
        try:
            res = run_one(job)
            results[job["label"]] = res
            liq = "LIQ" if res["liquidated"] else "ok "
            print(f"[{i+1}/{len(pending)}] {job['label']:38s} {res['seconds']:6.1f}s {liq} "
                  f"adg={res['adg_pnl']:+.5f} dd={res['drawdown_worst_usd']:.3f} "
                  f"lpr={res['loss_profit_ratio']:.3f}", flush=True)
        except Exception as e:  # noqa: BLE001 - record, keep going
            results[job["label"]] = {"error": str(e)[:300]}
            print(f"[{i+1}/{len(pending)}] {job['label']:38s} FAILED: {str(e)[:120]}", flush=True)
        results_path.write_text(json.dumps(results, indent=2))
    print("batch finished", flush=True)


if __name__ == "__main__":
    main()
