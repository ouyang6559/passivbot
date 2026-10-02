"""Build backtest validation configs: 5 regime windows x {base, regime-params}.

Per window the regime config sets:
- global bot.long.forager from the regime template (forager is not per-coin overrideable),
- per-coin strategy/unstuck/risk (allowlisted fields only) via coin_overrides.

Both configs of a window share identical data settings (binance-only, same dates,
same coins) so the comparison is like-for-like and the second run reuses the cache.
"""
import json
from pathlib import Path

ROOT = Path(__file__).parent
RUNS = ROOT / "backtest_runs"
RUNS.mkdir(exist_ok=True)
PARAMS = json.loads((ROOT / "params" / "params_by_coin_regime.json").read_text())
BASE = json.loads(Path("configs/examples/BTC_ETH_XRP_SOL_ADA_long.json").read_text())
COINS = ["BTC", "ETH", "XRP", "SOL", "ADA"]

WINDOWS = {
    # regime: (start, end, rationale)
    "normal_osc":   ("2023-03-15", "2023-04-30", "BTC/ETH 均为正常震荡"),
    "low_vol_osc":  ("2023-07-05", "2023-08-28", "BTC+ETH 同期低波动震荡"),
    "strong_trend": ("2023-11-01", "2024-01-15", "SOL/ADA 强趋势,BTC 同向"),
    "bear":         ("2022-05-01", "2022-07-31", "LUNA 崩盘后的市场级熊市"),
    "extreme_vol":  ("2021-05-10", "2021-06-08", "2021-05 大崩盘窗口"),
}

# fields allowed per-coin by src/config/overrides.py (risk subset)
RISK_OVERRIDEABLE = [
    "entry_cooldown_minutes",
    "we_excess_allowance_pct",
    "position_exposure_enforcer_enabled",
    "position_exposure_enforcer_threshold",
]


def deep(src, *paths):
    node = src
    for p in paths:
        node = node[p]
    return node


def make_regime_config(regime: str) -> dict:
    cfg = json.loads(json.dumps(BASE))  # deep copy
    tpl = PARAMS["BTC"][regime]  # template = any coin's regime set for global parts
    # global forager from template (forager not per-coin overrideable)
    cfg["bot"]["long"]["forager"] = tpl["forager"]
    # per-coin patches: strategy + unstuck + risk subset
    cfg["coin_overrides"] = {}
    for coin in COINS:
        p = PARAMS[coin][regime]
        patch = {
            "strategy": p["strategy"],
            "unstuck": p["unstuck"],
            "risk": {k: p["risk"][k] for k in RISK_OVERRIDEABLE},
        }
        cfg["coin_overrides"][coin] = {"bot": {"long": patch}}
    return cfg


def main():
    manifest = {}
    for regime, (start, end, why) in WINDOWS.items():
        for kind in ["base", "regime"]:
            cfg = json.loads(json.dumps(BASE)) if kind == "base" else make_regime_config(regime)
            cfg["backtest"]["start_date"] = start
            cfg["backtest"]["end_date"] = end
            cfg["backtest"]["exchanges"] = ["binance"]
            cfg["backtest"]["suite_enabled"] = False
            cfg["backtest"]["scenarios"] = [{"label": f"val_{regime}_{kind}"}]
            name = f"val_{regime}_{kind}.json"
            (RUNS / name).write_text(json.dumps(cfg, indent=2))
            manifest[name] = {"regime": regime, "kind": kind, "start": start, "end": end, "why": why}
    (RUNS / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print("configs written:")
    for k in manifest:
        print(" ", k)


if __name__ == "__main__":
    main()
