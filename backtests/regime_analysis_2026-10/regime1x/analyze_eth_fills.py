"""ETH fills-process analysis across the 15 regime_1x ETH backtests.

For each run: extract entry/close structure, exposure path, DCA chains,
unstuck cost, enforcer interventions, and pnl decomposition from fills.csv,
plus the configured bot.long/short params from config.json.
Outputs regime1x/eth_fills_stats.json and a printed digest.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

R1X = Path(__file__).parent
results = json.loads((R1X / "results.json").read_text())
REGIMES = ["normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"]
SIDES = ["long", "short", "both"]


def load(run):
    fills = pd.read_csv(Path(run) / "fills.csv", parse_dates=["timestamp"])
    cfg = json.loads((Path(run) / "config.json").read_text())
    fills = fills.sort_values("timestamp").reset_index(drop=True)
    return fills, cfg


def side_params(cfg, pside):
    b = cfg["bot"][pside]
    return {
        "twel": b["risk"]["total_wallet_exposure_limit"],
        "we_excess": b["risk"]["we_excess_allowance_pct"],
        "n_pos": b["risk"]["n_positions"],
        "initial_qty_pct": b["strategy"]["trailing_martingale"]["entry"]["initial_qty_pct"],
        "ddf": b["strategy"]["trailing_martingale"]["entry"]["double_down_factor"],
        "entry_thr": b["strategy"]["trailing_martingale"]["entry"]["threshold_base_pct"],
        "entry_we_w": b["strategy"]["trailing_martingale"]["entry"]["threshold_we_weight"],
        "entry_vol_w_1h": b["strategy"]["trailing_martingale"]["entry"]["threshold_volatility_1h_weight"],
        "initial_ema_dist": b["strategy"]["trailing_martingale"]["entry"]["initial_ema_dist"],
        "close_thr": b["strategy"]["trailing_martingale"]["close"]["threshold_base_pct"],
        "close_we_w": b["strategy"]["trailing_martingale"]["close"]["threshold_we_weight"],
        "close_vol_w_1h": b["strategy"]["trailing_martingale"]["close"]["threshold_volatility_1h_weight"],
        "close_qty_pct": b["strategy"]["trailing_martingale"]["close"]["qty_pct"],
        "unstuck_thr": b["unstuck"]["threshold"],
        "unstuck_close_pct": b["unstuck"]["close_pct"],
        "unstuck_ema_dist": b["unstuck"]["ema_dist"],
        "unstuck_loss_allow": b["unstuck"]["loss_allowance_pct"],
    }


def analyze_side(fills, pside):
    f = fills[fills["type"].str.endswith("_" + pside)].copy()
    if f.empty:
        return None
    days = (f["timestamp"].iloc[-1] - f["timestamp"].iloc[0]).total_seconds() / 86400
    entry = f[f["type"].str.startswith("entry")]
    close = f[f["type"].str.startswith("close")]

    def frac(pattern):
        sel = f[f["type"].str.contains(pattern)]
        return round(len(sel) / len(f), 4) if len(f) else 0.0

    # DCA chains: a cycle starts at an initial entry (previous fill of ANY type
    # left psize ~ 0) and ends when the position is fully closed.
    f["prev_psize"] = f["psize"].shift(1).abs().fillna(0.0)
    f["prev_pprice"] = f["pprice"].shift(1)
    e = f[f["type"].str.startswith("entry")]
    new_cycle = e["prev_psize"] < 1e-9
    cycle_id = new_cycle.cumsum()
    entries_per_cycle = e.groupby(cycle_id).size()
    # initial qty per cycle = qty of first (initial) entry
    first_qty = e["qty"].abs().groupby(cycle_id).first()
    chain_growth = e["psize"].abs() / first_qty
    # realized DCA spacing: grid entry while the position was already open,
    # price vs the position's pprice before this fill
    is_grid = e["type"].str.contains("grid")
    same_cycle = ~new_cycle
    spacing = (e["price"] / e["prev_pprice"] - 1.0).abs()[is_grid & same_cycle]
    spacing = spacing.dropna()
    spacing = spacing[spacing > 1e-6]

    # close profit distances: grid close price vs pprice
    cg = close[close["type"].str.contains("close_grid")]
    close_dist = (cg["price"] / cg["pprice"] - 1.0).abs()
    close_dist = close_dist[close_dist > 1e-6]

    unst = close[close["type"].str.contains("unstuck")]
    auto_twel = close[close["type"].str.contains("auto_reduce_twel")]

    pnl_close = close["pnl"]
    win = pnl_close[pnl_close > 0]
    loss = pnl_close[pnl_close < 0]
    twe_col = "twe_" + pside
    we_max = f[twe_col].abs().max() if f[twe_col].abs().max() > 0 else f["wallet_exposure"].max()
    return {
        "days": round(days, 1),
        "fills_per_day": round(len(f) / days, 2),
        "frac_entry_grid_cropped": frac("entry_grid_cropped"),
        "frac_entry_trailing": frac("entry_trailing"),
        "frac_close_unstuck": frac("close_unstuck"),
        "frac_close_auto_reduce_twel": frac("close_auto_reduce_twel"),
        "n_entries": len(entry), "n_closes": len(close),
        "entries_per_cycle_mean": round(entries_per_cycle.mean(), 2),
        "entries_per_cycle_p95": round(entries_per_cycle.quantile(0.95), 1),
        "chain_growth_max_p99": round(chain_growth.quantile(0.99), 2),
        "we_max": round(we_max, 3),
        "we_at_entry_p95": round(entry["wallet_exposure"].quantile(0.95), 3),
        "dca_spacing_pct_median": round(spacing.median() * 100, 3) if len(spacing) else None,
        "dca_spacing_pct_p95": round(spacing.quantile(0.95) * 100, 3) if len(spacing) else None,
        "close_dist_pct_median": round(close_dist.median() * 100, 3) if len(close_dist) else None,
        "close_dist_pct_p05": round(close_dist.quantile(0.05) * 100, 3) if len(close_dist) else None,
        "close_dist_pct_p95": round(close_dist.quantile(0.95) * 100, 3) if len(close_dist) else None,
        "unstuck_n": len(unst),
        "unstuck_pnl_total": round(unst["pnl"].sum(), 1) if len(unst) else 0.0,
        "unstuck_we_median": round(unst["wallet_exposure"].median(), 3) if len(unst) else None,
        "auto_twel_n": len(auto_twel),
        "auto_twel_pnl_total": round(auto_twel["pnl"].sum(), 1) if len(auto_twel) else 0.0,
        "win_sum": round(win.sum(), 1), "loss_sum": round(loss.sum(), 1),
        "n_win": len(win), "n_loss": len(loss),
        "fees_total": round(f["fee_paid"].sum(), 1),
        "pnl_total": round(f["pnl"].sum() + f["fee_paid"].sum(), 1),
    }


def main():
    out = {}
    for key, v in sorted(results.items()):
        if not v.get("analysis_metrics_done") or not key.startswith("ETH"):
            continue
        coin, regime, side_file = key.split("/")
        side = side_file.removesuffix(".json")
        fills, cfg = load(v["run_dir"])
        rec = {"metrics": {k: v[k] for k in
                           ("adg_pnl", "drawdown_worst_usd", "loss_profit_ratio",
                            "backtest_completion_ratio", "liquidated")},
               "params": {}}
        for pside in ("long", "short"):
            enabled = (pside == "long") == (side in ("long", "both"))
            sp = side_params(cfg, pside)
            if enabled:
                rec["params"][pside] = sp
                rec["params"][pside]["fills_stats"] = analyze_side(fills, pside)
            else:
                rec["params"][pside] = {"twel": sp["twel"]}
        out[f"{coin}/{regime}/{side}"] = rec

    (R1X / "eth_fills_stats.json").write_text(json.dumps(out, indent=2))

    # digest
    for regime in REGIMES:
        for side in SIDES:
            rec = out.get(f"ETH/{regime}/{side}")
            if not rec:
                continue
            print(f"== ETH {regime} {side}  adg={rec['metrics']['adg_pnl']:.4f} "
                  f"dd={rec['metrics']['drawdown_worst_usd']:.3f} "
                  f"lpr={rec['metrics']['loss_profit_ratio']:.3f} "
                  f"liq={rec['metrics']['liquidated']}")
            for pside in ("long", "short"):
                p = rec["params"][pside]
                if "fills_stats" not in p or p["fills_stats"] is None:
                    continue
                s = p["fills_stats"]
                print(f"  [{pside}] twel={p['twel']} iq={p['initial_qty_pct']} ddf={p['ddf']} "
                      f"ethr={p['entry_thr']} cthr={p['close_thr']} "
                      f"excess={p['we_excess']} usthr={p['unstuck_thr']}")
                print(f"     fpd={s['fills_per_day']} crop={s['frac_entry_grid_cropped']} "
                      f"unstuck%={s['frac_close_unstuck']} e/c={s['entries_per_cycle_cycle'] if False else s['entries_per_cycle_mean']} "
                      f"wemax={s['we_max']} spacemed={s['dca_spacing_pct_median']}% "
                      f"closedist={s['close_dist_pct_median']}% "
                      f"unstuck_pnl={s['unstuck_pnl_total']} twelcut_pnl={s['auto_twel_pnl_total']} "
                      f"win={s['win_sum']} loss={s['loss_sum']}")


if __name__ == "__main__":
    main()
