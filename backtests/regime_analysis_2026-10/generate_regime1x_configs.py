"""Generate 7 coins x 5 regimes x 3 directions = 105 single-coin 1x-leverage configs.

Parameter calibration extends backtests/regime_analysis_2026-10 (7-coin regime stats):
- grid spacing scales with each coin's median daily log-range in that regime (scale S),
- regime x side matrix: a regime is favorable for one side and adverse for the other
  (strong_trend favors longs, bear favors shorts), so tilts are applied per side:
  favorable = trailing entries + wider TP; adverse = wider spacing, smaller qty,
  slower martingale, faster TP, eager unstuck; extreme_vol = defensive for both.
- practical single-coin 1x setup: n_positions=1, TWEL per regime (1.0 neutral/favorable,
  0.7 adverse, 0.5 extreme), leverage=1, USD collateral (btc_collateral_cap=0),
  minimum_coin_age_days=0 so 2019-era listings are tradable from their first candle.

Outputs:
  configs/regime_1x/<COIN>/<regime>/<long|short|both>.json
  configs/regime_1x/README.md
  backtests/regime_analysis_2026-10/regime1x/params_all.json (machine readable)
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent  # regime_analysis_2026-10
STATS = pd.read_csv(ROOT / "regime_stats.csv")
REPO = Path.cwd()
OUT_CFG = REPO / "configs" / "regime_1x"
OUT_PARAMS = ROOT / "regime1x"
OUT_PARAMS.mkdir(parents=True, exist_ok=True)

COINS = ["BTC", "ETH", "XRP", "SOL", "ADA", "DOGE", "LINK"]
REGIMES = ["normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"]
DIRECTIONS = ["long", "short", "both"]
CN = {
    "normal_osc": "正常震荡", "low_vol_osc": "低波动震荡", "strong_trend": "强趋势(上行)",
    "bear": "熊市下跌", "extreme_vol": "极端波动",
}

BASE = json.loads((REPO / "configs/examples/BTC_ETH_XRP_SOL_ADA_long.json").read_text())

# anchors from the user's optimized long side
B = dict(vol_ema_1h=1690, vol_ema_1m=60, ema0=770, ema1=210, ddf=0.73,
         init_dist=0.0097, init_qty=0.0276, thr=0.033, thr_we=0.135, thr_v1h=2.4,
         c_qty=0.1, c_thr=0.006, c_thr_we=-0.004, c_thr_v1h=1.0,
         u_ema0=770.0, u_ema1=210.0, f_drop=0.884, f_volspan=1660)

# ---- regime x side tilt tables ----
# role from the side's perspective: neutral / favorable / adverse / defensive
ROLE = {
    "long":  {"normal_osc": "neutral", "low_vol_osc": "neutral",
              "strong_trend": "favorable", "bear": "adverse", "extreme_vol": "defensive"},
    "short": {"normal_osc": "neutral", "low_vol_osc": "neutral",
              "strong_trend": "adverse", "bear": "favorable", "extreme_vol": "defensive"},
}
TILT = {
    "neutral":   dict(spacing=1.00, dist=1.00, qty=1.00, ddf=0.74, close=1.00, c_v1h=1.0,
                      span0=770, span1=210, v1h=1690, v1m=60, f_span=101, readiness=0.0,
                      we=1.64, cool=0.0, twel=1.0, u_thr=0.833, u_dist=-0.064,
                      u_cp=0.00936, u_al=0.00523, trailing=False),
    "favorable": dict(spacing=1.05, dist=1.00, qty=0.95, ddf=0.70, close=1.40, c_v1h=1.2,
                      span0=770, span1=210, v1h=1440, v1m=60, f_span=101, readiness=0.0,
                      we=1.30, cool=0.0, twel=1.0, u_thr=0.85, u_dist=-0.055,
                      u_cp=0.00936, u_al=0.005, trailing=True),
    "adverse":   dict(spacing=1.15, dist=1.15, qty=0.65, ddf=0.62, close=0.85, c_v1h=0.8,
                      span0=540, span1=150, v1h=1180, v1m=45, f_span=80, readiness=0.25,
                      we=0.80, cool=5.0, twel=0.7, u_thr=0.75, u_dist=-0.085,
                      u_cp=0.013, u_al=0.003, trailing=False),
    "defensive": dict(spacing=1.25, dist=1.25, qty=0.50, ddf=0.55, close=0.80, c_v1h=0.6,
                      span0=430, span1=120, v1h=845, v1m=30, f_span=60, readiness=0.25,
                      we=0.50, cool=15.0, twel=0.5, u_thr=0.70, u_dist=-0.090,
                      u_cp=0.016, u_al=0.002, trailing=False),
}
# low_vol_osc keeps its own gentler profile for both sides
TILT["neutral_low"] = dict(TILT["neutral"], qty=1.15, ddf=0.78, close=0.95,
                           span0=1000, span1=275, v1h=1940, v1m=90, f_span=120,
                           u_thr=0.88, u_dist=-0.045, u_cp=0.007, u_al=0.008)

SHORT_WE_SCALE = 0.8  # shorts get less excess headroom (squeeze risk)


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def build_side(coin, regime, pside, S):
    role = ROLE[pside][regime]
    t = TILT["neutral_low"] if regime == "low_vol_osc" else TILT[role]
    we = round(t["we"] * (SHORT_WE_SCALE if pside == "short" else 1.0), 2)
    dist_sign = -1.0 if pside == "long" else 1.0  # short: +dist waits above upper band
    trailing_base = round(clamp(0.004 * clamp(S, 0.5, 1.5), 0.002, 0.008), 4)
    close_retr = round(clamp(0.003 * clamp(S, 0.5, 1.5), 0.0015, 0.006), 4)
    return {
        "forager": {
            "score_weights": {"ema_readiness": t["readiness"],
                              "volatility": 1.0 - t["readiness"], "volume": 0.0},
            "volatility_ema_span_1m": t["f_span"],
            "volume_drop_pct": B["f_drop"],
            "volume_ema_span_1m": B["f_volspan"],
        },
        "risk": {
            "entry_cooldown_minutes": t["cool"],
            "n_positions": 1,
            "total_wallet_exposure_limit": t["twel"],
            "total_exposure_enforcer_enabled": True,
            "total_exposure_enforcer_threshold": 0.99,
            "we_excess_allowance_pct": we,
            "position_exposure_enforcer_enabled": True,
            "position_exposure_enforcer_threshold": 0.99,
        },
        "strategy": {"trailing_martingale": {
            "volatility_ema_span_1h": float(t["v1h"]),
            "volatility_ema_span_1m": float(t["v1m"]),
            "entry": {
                "ema_span_0": t["span0"],
                "ema_span_1": t["span1"],
                "double_down_factor": round(t["ddf"] * (0.95 if pside == "short" else 1.0), 2),
                "initial_ema_dist": round(clamp(B["init_dist"] * S ** 0.7 * t["dist"], 0.003, 0.035) * dist_sign, 4),
                "initial_qty_pct": round(clamp(B["init_qty"] * t["qty"] / S ** 0.5, 0.008, 0.045), 4),
                "threshold_base_pct": round(clamp(B["thr"] * S * t["spacing"], 0.010, 0.10), 4),
                "threshold_we_weight": B["thr_we"],
                "threshold_volatility_1h_weight": B["thr_v1h"] * 0.5 if role == "defensive" else B["thr_v1h"],
                "threshold_volatility_1m_weight": 0.0,
                "retracement_base_pct": trailing_base if t["trailing"] else 0.0,
                "retracement_we_weight": 0.0,
                "retracement_volatility_1h_weight": 0.0,
                "retracement_volatility_1m_weight": 0.0,
            },
            "close": {
                "qty_pct": B["c_qty"],
                "threshold_base_pct": round(clamp(B["c_thr"] * S * t["close"], 0.0025, 0.025), 4),
                "threshold_we_weight": B["c_thr_we"],
                "threshold_volatility_1h_weight": t["c_v1h"],
                "threshold_volatility_1m_weight": 0.0,
                "retracement_base_pct": close_retr if t["trailing"] else 0.0,
                "retracement_volatility_1h_weight": 0.0,
                "retracement_volatility_1m_weight": 0.0,
            },
        }},
        "unstuck": {
            "ema_span_0": B["u_ema0"],
            "ema_span_1": B["u_ema1"],
            "close_pct": round(t["u_cp"], 5),
            "ema_dist": t["u_dist"],
            "enabled": True,
            "loss_allowance_pct": round(t["u_al"], 5),
            "threshold": t["u_thr"],
        },
    }


def disabled_side(base_pside):
    side = json.loads(json.dumps(BASE["bot"][base_pside]))
    side["risk"]["total_wallet_exposure_limit"] = 0
    side["risk"]["n_positions"] = 1
    return side


def make_config(coin, regime, direction, S):
    cfg = json.loads(json.dumps(BASE))
    cfg["backtest"]["start_date"] = "2019-01-01"
    cfg["backtest"]["end_date"] = "now"
    cfg["backtest"]["exchanges"] = ["binance"]
    cfg["backtest"]["suite_enabled"] = False
    cfg["backtest"]["scenarios"] = [{"label": f"{coin}_{regime}_{direction}"}]
    cfg["backtest"]["btc_collateral_cap"] = 0
    cfg["backtest"]["btc_collateral_ltv_cap"] = None

    long_side = build_side(coin, regime, "long", S) if direction in ("long", "both") else disabled_side("long")
    short_side = build_side(coin, regime, "short", S) if direction in ("short", "both") else disabled_side("short")
    cfg["bot"]["long"] = long_side
    cfg["bot"]["short"] = short_side

    cfg["live"]["approved_coins"] = {
        "long": [coin] if direction in ("long", "both") else [],
        "short": [coin] if direction in ("short", "both") else [],
    }
    cfg["live"]["leverage"] = 1
    cfg["live"]["minimum_coin_age_days"] = 0
    cfg["live"]["hedge_mode"] = direction == "both"
    return cfg


def main():
    ranges = STATS.set_index(["coin", "regime"])["range_1d_med"]
    base_rng = STATS[STATS.regime == "normal_osc"].set_index("coin")["range_1d_med"]
    baseline = base_rng.median()

    params_all = {}
    manifest = []
    for coin in COINS:
        params_all[coin] = {}
        for regime in REGIMES:
            S = clamp(ranges[(coin, regime)] / baseline, 0.4, 2.2)
            params_all[coin][regime] = {"S": round(S, 3), "long": build_side(coin, regime, "long", S),
                                        "short": build_side(coin, regime, "short", S)}
            for direction in DIRECTIONS:
                cfg = make_config(coin, regime, direction, S)
                rel = Path(coin) / regime / f"{direction}.json"
                path = OUT_CFG / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False))
                manifest.append({"coin": coin, "regime": regime, "direction": direction,
                                 "config": str(rel), "S": round(S, 3)})
    (OUT_PARAMS / "params_all.json").write_text(json.dumps(params_all, indent=2, ensure_ascii=False))
    (OUT_PARAMS / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"configs: {len(manifest)} under {OUT_CFG}")
    print(f"baseline daily log range (median of 7-coin normal_osc): {baseline:.4f}")


if __name__ == "__main__":
    main()
