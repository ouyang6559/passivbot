"""Death anatomy for liquidated short/both runs in the 2022 window.

For each liquidated run, extract from fills.csv + equity curve:
- survival days, death date
- exposure path: peak TWE, share of life spent above 90% TWEL cap
- entry cropping (WEL binding) share
- realized vs unrealized loss split at death
- unstuck: count, realized loss, loss-allowance consumption
- final chain: position size vs initial entry, adverse excursion of price
  vs position pprice at death
- fees
Outputs regime1x/death_anatomy.json and prints a digest.
"""
import json
from pathlib import Path

import pandas as pd

R1X = Path(__file__).parent
results = json.loads((R1X / "results_2022_sb.json").read_text())
START_BAL = 100_000.0


def anatomy(key: str, v: dict) -> dict | None:
    coin, regime, side = key.split("/")
    side = side.removesuffix(".json")
    fills = pd.read_csv(Path(v["run_dir"]) / "fills.csv", parse_dates=["timestamp"])
    eq = pd.read_csv(Path(v["run_dir"]) / "balance_and_equity.csv.gz")
    eq["dt"] = pd.to_datetime(eq["Unnamed: 0"])
    eq = eq.set_index("dt")
    cfg = json.loads((Path(v["run_dir"]) / "config.json").read_text())
    sfx = "_short"
    f = fills[fills["type"].str.endswith(sfx)].copy()
    if f.empty:
        return None
    bot = cfg["bot"]["short"]
    twel = bot["risk"]["total_wallet_exposure_limit"]
    excess = bot["risk"]["we_excess_allowance_pct"]
    loss_allow = bot["unstuck"]["loss_allowance_pct"]

    t0, t1 = f["timestamp"].iloc[0], f["timestamp"].iloc[-1]
    days = (t1 - t0).total_seconds() / 86400
    # death equity/balance
    eq_die = eq["usd_total_equity"].iloc[-1]
    bal_die = eq["usd_total_balance"].iloc[-1]
    unrealized = eq_die - bal_die
    # exposure path from fills
    twe = f["twe_short"].abs()
    peak_twe = twe.max()
    # time above 90% of effective cap: approximate via twe at fills (proxy)
    cap = twel * 0.99
    frac_near_cap = float((twe >= 0.9 * cap).mean())
    entry = f[f["type"].str.startswith("entry")]
    crop = float(entry["type"].str.contains("cropped").mean()) if len(entry) else 0.0
    close = f[f["type"].str.startswith("close")]
    unst = close[close["type"].str.contains("unstuck")]
    realized = float(f["pnl"].sum())
    unst_pnl = float(unst["pnl"].sum()) if len(unst) else 0.0
    # final chain state (last open position before death)
    last_entry = entry.iloc[-1]
    # adverse excursion: max price after last entry vs entry pprice
    tail = f[f["timestamp"] >= last_entry["timestamp"]]
    px_max = float(tail["price"].max())
    pprice = float(last_entry["pprice"])
    adverse = px_max / pprice - 1.0  # short loses when price rises
    # last position size vs its initial entry
    # find the initial entry that opened the final cycle
    f["prev_psize"] = f["psize"].shift(1).abs().fillna(0.0)
    entries_all = f[f["type"].str.startswith("entry")]
    new_cycle = entries_all["prev_psize"] < 1e-9
    if new_cycle.any():
        last_cycle_start = entries_all[new_cycle].index[-1]
    else:
        last_cycle_start = entries_all.index[0]
    final_entries = entries_all.loc[last_cycle_start:]
    init_qty = float(final_entries["qty"].abs().iloc[0])
    final_psize = float(final_entries["psize"].abs().iloc[-1])
    return {
        "coin": coin, "regime": regime, "side": side,
        "twel": twel, "we_excess": excess,
        "initial_qty_pct": bot["strategy"]["trailing_martingale"]["entry"]["initial_qty_pct"],
        "ddf": bot["strategy"]["trailing_martingale"]["entry"]["double_down_factor"],
        "entry_thr": bot["strategy"]["trailing_martingale"]["entry"]["threshold_base_pct"],
        "close_thr": bot["strategy"]["trailing_martingale"]["close"]["threshold_base_pct"],
        "unstuck_thr": bot["unstuck"]["threshold"],
        "unstuck_close_pct": bot["unstuck"]["close_pct"],
        "loss_allowance_pct": loss_allow,
        "days_survived": round(days, 1),
        "death_date": str(t1.date()),
        "equity_at_death": round(eq_die, 0),
        "balance_at_death": round(bal_die, 0),
        "unrealized_at_death": round(unrealized, 0),
        "realized_pnl_total": round(realized, 0),
        "unstuck_n": int(len(unst)),
        "unstuck_pnl": round(unst_pnl, 0),
        "fees": round(float(f["fee_paid"].sum()), 0),
        "peak_twe": round(peak_twe, 3),
        "frac_fills_near_cap": round(frac_near_cap, 3),
        "entry_crop_share": round(crop, 3),
        "n_entries": int(len(entry)),
        "final_chain_size_vs_init": round(final_psize / init_qty, 2) if init_qty else None,
        "final_chain_entries": int(len(final_entries)),
        "adverse_excursion_vs_pprice": round(adverse, 4),
    }


def main():
    out = {}
    for key, v in sorted(results.items()):
        if not v.get("analysis_metrics_done") or not v.get("liquidated"):
            continue
        try:
            out[key] = anatomy(key, v)
        except Exception as e:  # noqa: BLE001
            out[key] = {"error": str(e)[:200]}
    (R1X / "death_anatomy.json").write_text(json.dumps(out, indent=2))
    for key, a in out.items():
        if "error" in a:
            print(f"{key}: ERROR {a['error']}")
            continue
        print(f"{key:34s} survived={a['days_survived']:6.1f}d die={a['death_date']} "
              f"peakTWE={a['peak_twe']:.2f} nearCap={a['frac_fills_near_cap']:.0%} "
              f"crop={a['entry_crop_share']:.0%} "
              f"realized={a['realized_pnl_total']:+,.0f} unreal={a['unrealized_at_death']:+,.0f} "
              f"unstuck={a['unstuck_n']}({a['unstuck_pnl']:+,.0f}) "
              f"chain={a['final_chain_size_vs_init']}x adv={a['adverse_excursion_vs_pprice']:+.1%}")


if __name__ == "__main__":
    main()
