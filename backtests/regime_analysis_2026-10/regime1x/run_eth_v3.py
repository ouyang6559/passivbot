"""ETH v3 iteration round: softened long-side v2 where round-1 acceptance failed.

Round-1 findings (results_v2.json vs eth_fills_stats.json baselines):
- normal_osc: iq cut 3.13%->2.6% cut wins more than unstuck fixes saved  -> adg -11%
- low_vol_osc: chain fix worked (unstuck loss -43%, e/cycle 8.1->5.0) but
  entry_thr 1.7% + iq 3.0% overcorrected                                   -> adg -35%
- extreme_vol: twel 0.65 + iq 1.2% raised adg +44% but dd 0.246->0.413     -> dd fail
- strong_trend passed all criteria (kept); bear we_excess change was a no-op (kept v1).

v3 = single-knob softening of exactly those three regimes; short sides unchanged.
Outputs under regime1x/eth_v3/ (same structure as eth_v2).  Resumable.
"""
import gzip
import json
import shutil
import subprocess
import time
from pathlib import Path

import analyze_eth_fills as aef
from run_eth_v2 import (LOCAL, WINDOWS, apply_deltas, build_cfg as build_cfg_v2,
                        pick_run_dir)

R1X = Path(__file__).parent
V3 = R1X / "eth_v3"
(V3 / "configs").mkdir(parents=True, exist_ok=True)
(V3 / "runs").mkdir(parents=True, exist_ok=True)
BT = Path("backtests/binance")
FULL_START, FULL_END = "2019-11-28", "2026-10-01"

LONG_V3 = {
    "normal_osc": {
        "strategy.trailing_martingale.entry.initial_qty_pct": 0.0313,  # reverted to v1
        "unstuck.threshold": 0.75,
        "unstuck.close_pct": 0.014,
    },
    "low_vol_osc": {
        "strategy.trailing_martingale.entry.initial_qty_pct": 0.036,
        "strategy.trailing_martingale.entry.threshold_base_pct": 0.0155,
        "strategy.trailing_martingale.entry.double_down_factor": 0.75,
        "unstuck.threshold": 0.75,
        "unstuck.close_pct": 0.012,
    },
    "extreme_vol": {
        "risk.total_wallet_exposure_limit": 0.55,
        "strategy.trailing_martingale.entry.initial_qty_pct": 0.010,
    },
}
SHORT_LOWVOL_V2 = {  # adopted short-side v2 for low_vol_osc (§6.3)
    "strategy.trailing_martingale.entry.initial_qty_pct": 0.030,
    "strategy.trailing_martingale.entry.threshold_base_pct": 0.017,
    "strategy.trailing_martingale.entry.double_down_factor": 0.72,
    "unstuck.threshold": 0.75,
    "unstuck.close_pct": 0.012,
}

ALLOC_V3 = {
    "Lonly": (None, 0.0),
    "L1_S0.5": (1.0, 0.5),
    "L0.55_S0.5": (0.55, 0.5),
}


def build_v3_cfg(regime, kind, start, end, alloc, short_deltas=None):
    src = LOCAL / regime / ("long.json" if kind == "long" else "both.json")
    cfg = json.loads(src.read_text())
    cfg["backtest"]["start_date"] = start
    cfg["backtest"]["end_date"] = end
    apply_deltas(cfg["bot"]["long"], LONG_V3[regime])
    if short_deltas:
        apply_deltas(cfg["bot"]["short"], short_deltas)
    if alloc:
        lt, st = ALLOC_V3[alloc]
        if lt is not None:
            cfg["bot"]["long"]["risk"]["total_wallet_exposure_limit"] = lt
        if st is not None:
            cfg["bot"]["short"]["risk"]["total_wallet_exposure_limit"] = st
    name = f"{regime}_{kind}_v3_{alloc or 'asis'}_{start}_{end}"
    path = V3 / "configs" / f"{name}.json"
    path.write_text(json.dumps(cfg, indent=4))
    return path, name


def save_run_artifacts(label, run_dir):
    out = V3 / "runs" / label.replace("/", "__")
    out.mkdir(parents=True, exist_ok=True)
    with open(run_dir / "fills.csv", "rb") as f_in, gzip.open(out / "fills.csv.gz", "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    shutil.copy(run_dir / "analysis.json", out / "analysis.json")
    shutil.copy(run_dir / "config.json", out / "config.json")
    return out


def run_one(job):
    cfg_path, name = build_v3_cfg(job["regime"], job["kind"], job["start"], job["end"],
                                  job["alloc"], job.get("short_deltas"))
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
    for pside, enabled in (("long", True), ("short", job["kind"] == "both")):
        twel = cfg["bot"][pside]["risk"]["total_wallet_exposure_limit"]
        if enabled and twel > 0:
            fstats[pside] = aef.analyze_side(fills, pside)
    return {
        "config": str(cfg_path), "run_dir": str(run_dir), "artifacts": str(artifacts),
        "seconds": round(time.time() - t0, 1), "window": [job["start"], job["end"]],
        "adg_pnl": analysis.get("adg_pnl"), "mdg_pnl": analysis.get("mdg_pnl"),
        "drawdown_worst_usd": analysis.get("drawdown_worst_usd"),
        "loss_profit_ratio": analysis.get("loss_profit_ratio"),
        "peak_recovery_hours_pnl": analysis.get("peak_recovery_hours_pnl"),
        "backtest_completion_ratio": analysis.get("backtest_completion_ratio"),
        "liquidated": analysis.get("liquidated"), "n_fills": analysis.get("fills_count"),
        "twel": {"long": cfg["bot"]["long"]["risk"]["total_wallet_exposure_limit"],
                 "short": cfg["bot"]["short"]["risk"]["total_wallet_exposure_limit"]},
        "fills_stats": fstats,
    }


def job_list():
    nw1, nw2 = WINDOWS["normal_osc"]
    lw1 = WINDOWS["low_vol_osc"][0]
    ew1 = WINDOWS["extreme_vol"][0]
    return [
        {"regime": "normal_osc", "kind": "long", "alloc": None,
         "start": FULL_START, "end": FULL_END, "label": "longfull_v3/normal_osc"},
        {"regime": "low_vol_osc", "kind": "long", "alloc": None,
         "start": FULL_START, "end": FULL_END, "label": "longfull_v3/low_vol_osc"},
        {"regime": "extreme_vol", "kind": "long", "alloc": None,
         "start": FULL_START, "end": FULL_END, "label": "longfull_v3/extreme_vol"},
        {"regime": "normal_osc", "kind": "both", "alloc": "Lonly",
         "start": nw1[0], "end": nw1[1], "label": "normal_osc/w1/Lonly_v3"},
        {"regime": "normal_osc", "kind": "both", "alloc": "Lonly",
         "start": nw2[0], "end": nw2[1], "label": "normal_osc/w2/Lonly_v3"},
        {"regime": "low_vol_osc", "kind": "both", "alloc": "Lonly",
         "start": lw1[0], "end": lw1[1], "label": "low_vol_osc/w1/Lonly_v3"},
        {"regime": "low_vol_osc", "kind": "both", "alloc": "L1_S0.5",
         "start": lw1[0], "end": lw1[1], "short_deltas": SHORT_LOWVOL_V2,
         "label": "low_vol_osc/w1/L1_S0.5_v3"},
        {"regime": "extreme_vol", "kind": "both", "alloc": "L0.55_S0.5",
         "start": ew1[0], "end": ew1[1], "label": "extreme_vol/w1/L0.55_S0.5_v3"},
        {"regime": "extreme_vol", "kind": "both", "alloc": "L0.55_S0.5",
         "start": FULL_START, "end": FULL_END, "label": "extreme_vol/full/L0.55_S0.5_v3"},
    ]


def main():
    results_path = V3 / "results_v3.json"
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
        except Exception as e:  # noqa: BLE001
            results[job["label"]] = {"error": str(e)[:300]}
            print(f"[{i+1}/{len(pending)}] {job['label']:38s} FAILED: {str(e)[:120]}", flush=True)
        results_path.write_text(json.dumps(results, indent=2))
    print("v3 batch finished", flush=True)


if __name__ == "__main__":
    main()
