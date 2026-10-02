"""ETH short-side windowed backtests: baseline vs v2 params, per regime.

Windows are the representative contiguous windows from regime_windows.json.
v2 applies the long-side findings mirrored to short: earlier/larger unstuck,
lighter initial qty, wider DCA spacing in dense regimes.
Writes eth_short_windows.json + prints a digest.
"""
import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pandas as pd

R1X = Path(__file__).parent
LOCAL = Path("configs/local/regime_1x_bt/ETH")
OUT = R1X / "eth_short_window_runs"
OUT.mkdir(exist_ok=True)

WINDOWS = {  # longest representative window per regime (regime_windows.json)
    "normal_osc": ("2023-10-13", "2024-05-15"),
    "low_vol_osc": ("2023-07-05", "2023-11-01"),
    "strong_trend": ("2025-07-16", "2025-09-08"),
    "bear": ("2025-10-17", "2026-04-20"),
    "extreme_vol": ("2021-05-03", "2021-05-25"),
}
EXTRA = {  # second-longest windows for robustness
    "bear": ("2022-08-27", "2023-01-24"),
    "normal_osc": ("2023-02-09", "2023-07-21"),
}

# v2 overrides on bot.short (mirrors long-side section-8 findings)
V2 = {
    "normal_osc": {
        "risk.total_wallet_exposure_limit": None,  # unchanged
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
        "strategy.trailing_martingale.close.threshold_base_pct": 0.006,
        "unstuck.threshold": 0.72,
    },
    "bear": {
        "unstuck.threshold": 0.75,
        "unstuck.close_pct": 0.013,
    },
    "extreme_vol": {},  # keep (only surviving full-history config)
}


def set_path(cfg, dotted, value):
    node = cfg
    parts = dotted.split(".")
    for p in parts[:-1]:
        node = node[p]
    node[parts[-1]] = value


def make_cfg(regime, start, end, variant):
    cfg = json.loads((LOCAL / regime / "short.json").read_text())
    cfg["backtest"]["start_date"] = start
    cfg["backtest"]["end_date"] = end
    if variant == "v2":
        for dotted, value in V2[regime].items():
            if value is not None:
                set_path(cfg, "bot.short." + dotted, value)
    path = OUT / f"{regime}_{variant}_{start}_{end}.json"
    path.write_text(json.dumps(cfg, indent=4))
    return path


def fill_stats(run_dir):
    f = pd.read_csv(Path(run_dir) / "fills.csv", parse_dates=["timestamp"])
    f = f[f["type"].str.endswith("_short")]
    if f.empty:
        return {}
    days = max((f["timestamp"].iloc[-1] - f["timestamp"].iloc[0]).total_seconds() / 86400, 1e-9)
    close = f[f["type"].str.startswith("close")]
    unst = close[close["type"].str.contains("unstuck")]
    return {
        "fills_per_day": round(len(f) / days, 2),
        "frac_close_unstuck": round(len(unst) / len(f), 3) if len(f) else 0.0,
        "unstuck_pnl": round(unst["pnl"].sum(), 1) if len(unst) else 0.0,
        "loss_sum": round(close["pnl"][close["pnl"] < 0].sum(), 1),
        "win_sum": round(close["pnl"][close["pnl"] > 0].sum(), 1),
        "twe_max": round(f["twe_short"].abs().max(), 3),
    }


def run(cfg_path):
    proc = subprocess.run(
        ["./venv/bin/passivbot", "backtest", str(cfg_path)],
        capture_output=True, text=True, timeout=3600,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-400:])
    # newest run dir in backtests/binance
    dirs = sorted(p for p in Path("backtests/binance").iterdir() if p.is_dir())
    run_dir = dirs[-1]
    a = json.loads((run_dir / "analysis.json").read_text())
    out = {
        "adg_pnl": a.get("adg_pnl"), "drawdown_worst_usd": a.get("drawdown_worst_usd"),
        "loss_profit_ratio": a.get("loss_profit_ratio"),
        "backtest_completion_ratio": a.get("backtest_completion_ratio"),
        "liquidated": a.get("liquidated"),
        "run_dir": str(run_dir), "fills": fill_stats(run_dir),
    }
    return out


def main():
    results = {}
    for regime, (start, end) in WINDOWS.items():
        for variant in ("baseline", "v2"):
            key = f"{regime}/{variant}"
            try:
                cfg = make_cfg(regime, start, end, variant)
                results[key] = {"window": [start, end], **run(cfg)}
                f = results[key]["fills"]
                print(f"{key:26s} adg={results[key]['adg_pnl']:.5f} "
                      f"dd={results[key]['drawdown_worst_usd']:.3f} "
                      f"liq={results[key]['liquidated']} "
                      f"unstuck%={f.get('frac_close_unstuck', 0):.2f} "
                      f"fpd={f.get('fills_per_day', 0):.1f}", flush=True)
            except Exception as e:  # noqa: BLE001
                results[key] = {"error": str(e)[:300]}
                print(f"{key:26s} FAILED {str(e)[:120]}", flush=True)
    for regime, (start, end) in EXTRA.items():
        for variant in ("baseline", "v2"):
            key = f"{regime}_{start}/{variant}"
            try:
                cfg = make_cfg(regime, start, end, variant)
                results[key] = {"window": [start, end], **run(cfg)}
                print(f"{key:26s} adg={results[key]['adg_pnl']:.5f} "
                      f"dd={results[key]['drawdown_worst_usd']:.3f} "
                      f"liq={results[key]['liquidated']}", flush=True)
            except Exception as e:  # noqa: BLE001
                results[key] = {"error": str(e)[:300]}
                print(f"{key:26s} FAILED {str(e)[:120]}", flush=True)
    (R1X / "eth_short_windows.json").write_text(json.dumps(results, indent=2))
    print("saved eth_short_windows.json")


if __name__ == "__main__":
    main()
