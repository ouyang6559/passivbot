"""ETH v2h (HSL + entry cooldown + doubled vol weights) episode backtests.

Protocol (user-specified): run one calendar year at a time from 2022-01-01;
if an episode is liquidated (equity -> 5% of starting balance), record the
liquidation date and resume a fresh episode (starting balance resets to
config's starting_balance) the next day, until 2026-10-01.

v2h parameter deltas vs the 2022 baseline configs (leverage cut deferred):
- bot.{pside}.hsl.enabled = true, red_threshold = 0.10,
  panic_close_order_type = market, cooldown_minutes_after_red = 1440
- bot.{pside}.risk.entry_cooldown_minutes = 10.0
- bot.{pside}.strategy.trailing_martingale.entry.threshold_volatility_1h_weight = 4.0

Resumable: regime1x/eth_v2h_episodes.json.
"""
import json
import subprocess
import time
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

R1X = Path(__file__).parent
BASE = Path("configs/local/regime_1x_bt/ETH")
OUT = Path("configs/local/regime_1x_eth_v2h")
BT = Path("backtests/binance")
WINDOW_START = date(2022, 1, 1)
WINDOW_END = date(2026, 10, 1)
REGIMES = ["normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"]
SIDES = ["long", "short", "both"]


def make_cfg(regime: str, side: str) -> Path:
    dst = OUT / regime
    dst.mkdir(parents=True, exist_ok=True)
    path = dst / f"{side}.json"
    if path.exists():
        return path
    cfg = json.loads((BASE / regime / f"{side}.json").read_text())
    for pside in ("long", "short"):
        enabled = (pside == "long") == (side in ("long", "both"))
        hsl = cfg["bot"][pside]["hsl"]
        hsl["enabled"] = bool(enabled)
        hsl["red_threshold"] = 0.10
        hsl["panic_close_order_type"] = "market"
        hsl["cooldown_minutes_after_red"] = 1440
        if enabled:
            cfg["bot"][pside]["risk"]["entry_cooldown_minutes"] = 10.0
            cfg["bot"][pside]["strategy"]["trailing_martingale"]["entry"][
                "threshold_volatility_1h_weight"] = 4.0
    path.write_text(json.dumps(cfg, indent=4))
    return path


def episode_cfg(regime: str, side: str, start: date, end: date) -> Path:
    cfg = json.loads(make_cfg(regime, side).read_text())
    cfg["backtest"]["start_date"] = start.isoformat()
    cfg["backtest"]["end_date"] = end.isoformat()
    ep_dir = OUT / "_episodes"
    ep_dir.mkdir(parents=True, exist_ok=True)
    path = ep_dir / f"{regime}_{side}_{start}_{end}.json"
    path.write_text(json.dumps(cfg, indent=4))
    return path


def run_backtest(cfg_path: Path) -> tuple[dict, Path]:
    before = {p for p in BT.iterdir() if p.is_dir()}
    proc = subprocess.run(
        ["./venv/bin/passivbot", "backtest", str(cfg_path)],
        capture_output=True, text=True, timeout=7200,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-300:])
    # only consider dirs created by this run; verify the dir's config matches ours
    ours = json.loads(cfg_path.read_text())
    new = sorted(p for p in BT.iterdir() if p.is_dir() and p not in before)
    for d in reversed(new):
        try:
            dc = json.loads((d / "config.json").read_text())
            if (dc["backtest"]["start_date"] == ours["backtest"]["start_date"]
                    and dc["backtest"]["end_date"] == ours["backtest"]["end_date"]):
                return json.loads((d / "analysis.json").read_text()), d
        except Exception:  # noqa: BLE001
            continue
    raise RuntimeError(f"no matching new run dir among {len(new)}")


def year_end(d: date) -> date:
    return date(d.year, 12, 31)


def run_series(regime: str, side: str) -> dict:
    episodes = []
    cursor = WINDOW_START
    while cursor <= WINDOW_END:
        seg_end = min(year_end(cursor), WINDOW_END)
        cfg = episode_cfg(regime, side, cursor, seg_end)
        a, run_dir = run_backtest(cfg)
        eq = pd.read_csv(Path(run_dir) / "balance_and_equity.csv.gz")
        eq["dt"] = pd.to_datetime(eq["Unnamed: 0"])
        end_dt = eq["dt"].iloc[-1].date()
        end_equity = float(eq["usd_total_equity"].iloc[-1])
        liq = bool(a.get("liquidated"))
        # per-year compounded return inside this episode
        s = eq.set_index("dt")["usd_total_equity"]
        yr = {}
        for y, seg in s.groupby(s.index.year):
            yr[int(y)] = seg.iloc[-1] / seg.iloc[0] - 1.0
        episodes.append({
            "start": cursor.isoformat(), "end": end_dt.isoformat(),
            "liquidated": liq, "end_equity": round(end_equity, 0),
            "year_returns": {str(k): round(v, 4) for k, v in yr.items()},
            "adg_pnl": a.get("adg_pnl"),
            "drawdown_worst_usd": a.get("drawdown_worst_usd"),
            "loss_profit_ratio": a.get("loss_profit_ratio"),
            "hsl_liquidation": a.get("liquidated"),
        })
        print(f"  episode {cursor} -> {end_dt} liq={liq} eq={end_equity:,.0f}", flush=True)
        if liq:
            cursor = end_dt + timedelta(days=1)
        else:
            cursor = seg_end + timedelta(days=1)
    # compounded per-year returns across episodes
    years = {}
    for ep in episodes:
        for y, r in ep["year_returns"].items():
            years[y] = years.get(y, 1.0) * (1.0 + r)
    final_multiple = 1.0
    for ep in episodes:
        final_multiple *= ep["end_equity"] / 100_000.0
    return {
        "episodes": episodes,
        "n_liquidations": sum(1 for e in episodes if e["liquidated"]),
        "liquidation_dates": [e["end"] for e in episodes if e["liquidated"]],
        "year_returns_compounded": {y: round(v - 1.0, 4) for y, v in sorted(years.items())},
        "final_equity_multiple": round(final_multiple, 4),
    }


def main():
    results_path = R1X / "eth_v2h_episodes.json"
    results = json.loads(results_path.read_text()) if results_path.exists() else {}
    for regime in REGIMES:
        for side in SIDES:
            key = f"{regime}/{side}"
            if results.get(key, {}).get("episodes"):
                print(f"{key}: done, skip", flush=True)
                continue
            print(f"== {key}", flush=True)
            t0 = time.time()
            try:
                results[key] = run_series(regime, side)
                results[key]["seconds"] = round(time.time() - t0, 1)
            except Exception as e:  # noqa: BLE001
                results[key] = {"error": str(e)[:300]}
                print(f"{key} FAILED {str(e)[:150]}", flush=True)
            results_path.write_text(json.dumps(results, indent=2))
    for key, v in results.items():
        if "error" in v or not v.get("episodes"):
            continue
        yr = " ".join(f"{y}:{r:+.0%}" for y, r in v["year_returns_compounded"].items())
        print(f"{key:22s} liq={v['n_liquidations']} final={v['final_equity_multiple']:.2f}x {yr}")


if __name__ == "__main__":
    main()
