"""Sensitivity probes for FROZEN parameters (second-pass tuning candidates).

Question behind this script: the v2/v3/v4 rounds only opened 13-27 of ~88
bounds-exposed knobs per scenario.  Which of the frozen ones actually move
the needle?  Each probe changes ONE frozen knob on the normal_osc final
config (long side, full history) and compares against the v1 baseline
(adg 0.00250 / dd 0.671 / lpr 0.259 / unstuck-share 98% / crop 15.2%).

P7 is structural: can an HSL overlay rescue a small short allocation in the
normal_osc window where shorts got liquidated?

Outputs eth_final/probe_results.json.
"""
import json
import subprocess
import time
from pathlib import Path

import analyze_eth_fills as aef
from run_eth_v2 import pick_run_dir

BASE = json.loads(Path("configs/local/eth_final/ETH/normal_osc.json").read_text())
OUT = R1X_OUT = Path("backtests/regime_analysis_2026-10/regime1x/eth_final/probe_results.json")
PROBES = [
    {"label": "P1_entry_ema_x1.3", "window": None,
     "long": {"strategy.trailing_martingale.entry.ema_span_0": 1000,
              "strategy.trailing_martingale.entry.ema_span_1": 273}},
    {"label": "P2_entry_ema_x0.7", "window": None,
     "long": {"strategy.trailing_martingale.entry.ema_span_0": 540,
              "strategy.trailing_martingale.entry.ema_span_1": 147}},
    {"label": "P3_close_qty_0.2", "window": None,
     "long": {"strategy.trailing_martingale.close.qty_pct": 0.2}},
    {"label": "P4_vol_span_1m_300", "window": None,
     "long": {"strategy.trailing_martingale.volatility_ema_span_1m": 300}},
    {"label": "P5_we_weight_0.30", "window": None,
     "long": {"strategy.trailing_martingale.entry.threshold_we_weight": 0.30}},
    {"label": "P6_initial_dist_deep", "window": None,
     "long": {"strategy.trailing_martingale.entry.initial_ema_dist": -0.015}},
    {"label": "P7_hsl_short_rescue", "window": ("2023-10-13", "2024-05-15"),
     "short": {"risk.total_wallet_exposure_limit": 0.5,
               "hsl.enabled": True, "hsl.red_threshold": 0.15}},
]


def set_path(node, dotted, value):
    parts = dotted.split(".")
    for p in parts[:-1]:
        node = node[p]
    node[parts[-1]] = value


def run_probe(probe):
    cfg = json.loads(json.dumps(BASE))
    start, end = probe["window"] or ("2019-11-28", "2026-10-01")
    cfg["backtest"]["start_date"], cfg["backtest"]["end_date"] = start, end
    for side in ("long", "short"):
        for dotted, v in probe.get(side, {}).items():
            set_path(cfg["bot"][side], dotted, v)
    tmp = Path(f"/tmp/eth_probe_{probe['label']}.json")
    tmp.write_text(json.dumps(cfg, indent=4))
    t0 = time.time()
    proc = subprocess.run(["./venv/bin/passivbot", "backtest", str(tmp)],
                          capture_output=True, text=True, timeout=3600)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-300:])
    run_dir = pick_run_dir()
    a = json.loads((run_dir / "analysis.json").read_text())
    fills = aef.load(str(run_dir))[0]
    cfg_run = json.loads((run_dir / "config.json").read_text())
    stats = {}
    for pside in ("long", "short"):
        twel = cfg_run["bot"][pside]["risk"]["total_wallet_exposure_limit"]
        if twel > 0:
            s = aef.analyze_side(fills, pside) or {}
            if s:
                stats[pside] = {k: s[k] for k in
                                ("fills_per_day", "frac_close_unstuck", "frac_entry_grid_cropped",
                                 "entries_per_cycle_mean", "unstuck_pnl_total", "win_sum",
                                 "loss_sum", "close_dist_pct_median")}
    return {"window": [start, end], "seconds": round(time.time() - t0, 1),
            "adg_pnl": a.get("adg_pnl"), "drawdown_worst_usd": a.get("drawdown_worst_usd"),
            "loss_profit_ratio": a.get("loss_profit_ratio"),
            "backtest_completion_ratio": a.get("backtest_completion_ratio"),
            "liquidated": a.get("liquidated"), "n_fills": a.get("fills_count"),
            "run_dir": str(run_dir), "fills_stats": stats}


def main():
    results = json.loads(OUT.read_text()) if OUT.exists() else {}
    for probe in PROBES:
        if probe["label"] in results:
            continue
        try:
            r = run_probe(probe)
            results[probe["label"]] = r
            print(f"{probe['label']:24s} adg={r['adg_pnl']:+.5f} dd={r['drawdown_worst_usd']:.3f} "
                  f"lpr={r['loss_profit_ratio']:.3f} liq={r['liquidated']} "
                  f"fpd={list(r['fills_stats'].values())[0]['fills_per_day'] if r['fills_stats'] else '-'}",
                  flush=True)
        except Exception as e:  # noqa: BLE001
            results[probe["label"]] = {"error": str(e)[:300]}
            print(f"{probe['label']:24s} FAILED {str(e)[:150]}", flush=True)
        OUT.write_text(json.dumps(results, indent=2))
    print("probes finished", flush=True)


if __name__ == "__main__":
    main()
