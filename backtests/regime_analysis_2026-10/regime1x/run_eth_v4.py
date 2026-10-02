"""ETH v4 final calibration round (freeze-point candidates).

- low_vol_osc: last middle point between v1 (adg 0.403%/d, chain 8.1) and v3
  (0.338%/d, chain 5.3): keep early size, widen spacing less, slower mid-chain.
- extreme_vol: last twel step down (0.52) to fit the dd <= v1*1.05 gate.
- normal_osc: v1-long + short-off windowed allocation runs (pure allocation
  baseline; final normal_osc long params stay v1, so the window evidence must
  use v1 long too).

Outputs under regime1x/eth_v4/.  Resumable.
"""
import json
import time
from pathlib import Path

import analyze_eth_fills as aef
from run_eth_v2 import LOCAL, WINDOWS, apply_deltas, pick_run_dir
from run_eth_v3 import save_run_artifacts

R1X = Path(__file__).parent
V4 = R1X / "eth_v4"
(V4 / "runs").mkdir(parents=True, exist_ok=True)
FULL_START, FULL_END = "2019-11-28", "2026-10-01"

LONG_V4 = {
    "low_vol_osc": {
        "strategy.trailing_martingale.entry.initial_qty_pct": 0.040,
        "strategy.trailing_martingale.entry.threshold_base_pct": 0.0150,
        "strategy.trailing_martingale.entry.double_down_factor": 0.72,
        "unstuck.threshold": 0.78,
        "unstuck.close_pct": 0.012,
    },
    "extreme_vol": {
        "risk.total_wallet_exposure_limit": 0.52,
        "strategy.trailing_martingale.entry.initial_qty_pct": 0.0098,
    },
}
SHORT_LOWVOL_V2 = {  # adopted short-side v2 for low_vol_osc (§6.3)
    "strategy.trailing_martingale.entry.initial_qty_pct": 0.030,
    "strategy.trailing_martingale.entry.threshold_base_pct": 0.017,
    "strategy.trailing_martingale.entry.double_down_factor": 0.72,
    "unstuck.threshold": 0.75,
    "unstuck.close_pct": 0.012,
}


def build_v4_cfg(regime, kind, start, end, long_deltas, short_deltas=None,
                 long_twel=None, short_twel=None):
    src = LOCAL / regime / ("long.json" if kind == "long" else "both.json")
    cfg = json.loads(src.read_text())
    cfg["backtest"]["start_date"] = start
    cfg["backtest"]["end_date"] = end
    if long_deltas:
        apply_deltas(cfg["bot"]["long"], long_deltas)
    if short_deltas:
        apply_deltas(cfg["bot"]["short"], short_deltas)
    if long_twel is not None:
        cfg["bot"]["long"]["risk"]["total_wallet_exposure_limit"] = long_twel
    if short_twel is not None:
        cfg["bot"]["short"]["risk"]["total_wallet_exposure_limit"] = short_twel
    name = f"{regime}_{kind}_v4_{start}_{end}"
    path = V4 / f"{name}.json"
    path.write_text(json.dumps(cfg, indent=4))
    return path


def run_one(job):
    cfg_path = build_v4_cfg(job["regime"], job["kind"], job["start"], job["end"],
                            job.get("long_deltas"), job.get("short_deltas"),
                            job.get("long_twel"), job.get("short_twel"))
    t0 = time.time()
    proc = __import__("subprocess").run(["./venv/bin/passivbot", "backtest", str(cfg_path)],
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
        {"regime": "low_vol_osc", "kind": "long", "start": FULL_START, "end": FULL_END,
         "long_deltas": LONG_V4["low_vol_osc"], "label": "longfull_v4/low_vol_osc"},
        {"regime": "extreme_vol", "kind": "long", "start": FULL_START, "end": FULL_END,
         "long_deltas": LONG_V4["extreme_vol"], "label": "longfull_v4/extreme_vol"},
        {"regime": "normal_osc", "kind": "both", "start": nw1[0], "end": nw1[1],
         "long_deltas": None, "short_twel": 0.0, "label": "normal_osc/w1/Lonly_v1"},
        {"regime": "normal_osc", "kind": "both", "start": nw2[0], "end": nw2[1],
         "long_deltas": None, "short_twel": 0.0, "label": "normal_osc/w2/Lonly_v1"},
        {"regime": "low_vol_osc", "kind": "both", "start": lw1[0], "end": lw1[1],
         "long_deltas": LONG_V4["low_vol_osc"], "short_deltas": SHORT_LOWVOL_V2,
         "long_twel": 1.0, "short_twel": 0.5, "label": "low_vol_osc/w1/L1_S0.5_v4"},
        {"regime": "extreme_vol", "kind": "both", "start": ew1[0], "end": ew1[1],
         "long_deltas": LONG_V4["extreme_vol"], "long_twel": 0.52, "short_twel": 0.5,
         "label": "extreme_vol/w1/L0.52_S0.5_v4"},
    ]


def main():
    results_path = V4 / "results_v4.json"
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
    print("v4 batch finished", flush=True)


if __name__ == "__main__":
    main()
