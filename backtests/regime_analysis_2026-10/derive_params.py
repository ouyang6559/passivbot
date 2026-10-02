"""Derive per-coin x per-regime trailing_martingale parameter sets (bot.long only).

Calibration anchors (all from the user's base config + docs/config.bot.md formulas):
- Spacing scale S(coin, regime) = median daily log-range in (coin, regime)
                                  / median across coins of the normal_osc daily range.
  Entry/close grid distances scale roughly linearly with realized range, so S
  converts "how big are moves here" into grid geometry.
- Initial qty scales inversely with sqrt(S): same WEL divided into more ladder
  steps when moves are bigger.
- Defensive regimes (bear / extreme) tilt toward: wider spacing, smaller initial
  qty, lower martingale growth, faster/simpler closes, eager unstuck, tighter
  loss allowance, lower we-excess, short indicator spans.

Outputs:
  params/params_by_coin_regime.json   machine-readable {coin: {regime: bot.long}}
  params/params_annotated.md          annotated tables (one per coin, 5 regimes)
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
STATS = pd.read_csv(ROOT / "regime_stats.csv")
OUT = ROOT / "params"
OUT.mkdir(exist_ok=True)

COINS = ["BTC", "ETH", "XRP", "SOL", "ADA"]
REGIMES = ["normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"]
CN = {
    "normal_osc": "正常震荡",
    "low_vol_osc": "低波动震荡",
    "strong_trend": "强趋势(上行)",
    "bear": "熊市下跌",
    "extreme_vol": "极端波动",
}

# base config anchor values (bot.long)
B = {
    "vol_ema_1h": 1690, "vol_ema_1m": 60,
    "ema0": 770, "ema1": 210,
    "ddf": 0.73, "init_dist": 0.0097, "init_qty": 0.0276,
    "thr": 0.033, "thr_we": 0.135, "thr_v1h": 2.4, "thr_v1m": 0.0,
    "retr": 0.0, "retr_we": 0.0, "retr_v1h": 0.0, "retr_v1m": 0.0,
    "c_qty": 0.1, "c_thr": 0.006, "c_thr_we": -0.004, "c_thr_v1h": 1.0,
    "c_retr": 0.0, "c_retr_v1h": 0.0, "c_retr_v1m": 0.0,
    "u_thr": 0.833, "u_dist": -0.064, "u_close_pct": 0.00936,
    "u_allow": 0.00523, "u_ema0": 770.0, "u_ema1": 210.0,
    "we_excess": 1.64, "f_vol_span": 101, "f_drop": 0.884, "f_volspan": 1660,
}

# per-regime policy tilts (rationale in params_annotated.md)
TILT = {
    "normal_osc":  dict(spacing=1.00, dist=1.00, qty=1.00, ddf=0.74, close=1.00,
                        c_v1h=1.0, span0=770, span1=210, v1h=1690, v1m=60,
                        f_span=101, readiness=0.0, we=1.64, cool=0.0,
                        u_thr=0.833, u_dist=-0.064, u_cp=0.00936, u_al=0.00523),
    "low_vol_osc": dict(spacing=1.00, dist=1.05, qty=1.15, ddf=0.78, close=0.95,
                        c_v1h=1.0, span0=1000, span1=275, v1h=1940, v1m=90,
                        f_span=120, readiness=0.0, we=1.64, cool=0.0,
                        u_thr=0.88, u_dist=-0.045, u_cp=0.007, u_al=0.008),
    "strong_trend": dict(spacing=1.05, dist=1.00, qty=0.95, ddf=0.70, close=1.45,
                         c_v1h=1.2, span0=770, span1=210, v1h=1440, v1m=60,
                         f_span=101, readiness=0.0, we=1.30, cool=0.0,
                         u_thr=0.85, u_dist=-0.055, u_cp=0.00936, u_al=0.005),
    "bear":        dict(spacing=1.15, dist=1.15, qty=0.65, ddf=0.62, close=0.85,
                        c_v1h=0.8, span0=540, span1=150, v1h=1180, v1m=45,
                        f_span=80, readiness=0.25, we=0.80, cool=5.0,
                        u_thr=0.75, u_dist=-0.085, u_cp=0.013, u_al=0.003),
    "extreme_vol": dict(spacing=1.25, dist=1.25, qty=0.50, ddf=0.55, close=0.80,
                        c_v1h=0.6, span0=430, span1=120, v1h=845, v1m=30,
                        f_span=60, readiness=0.25, we=0.50, cool=15.0,
                        u_thr=0.70, u_dist=-0.090, u_cp=0.016, u_al=0.002),
}


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def r4(x):
    return round(float(x), 4)


def r5(x):
    return round(float(x), 5)


def main():
    # baseline: median across coins of the normal_osc median daily log-range
    base_rng = STATS[STATS.regime == "normal_osc"].set_index("coin")["range_1d_med"]
    baseline = base_rng.median()  # == XRP 0.0551
    ranges = STATS.set_index(["coin", "regime"])["range_1d_med"]

    params = {}
    for coin in COINS:
        params[coin] = {}
        for regime in REGIMES:
            t = TILT[regime]
            S = clamp(ranges[(coin, regime)] / baseline, 0.4, 2.2)  # spacing scale
            Sretr = clamp(S, 0.5, 1.5)
            p = {
                "forager": {
                    "score_weights": {
                        "ema_readiness": t["readiness"],
                        "volatility": 1.0 - t["readiness"],
                        "volume": 0.0,
                    },
                    "volatility_ema_span_1m": t["f_span"],
                    "volume_drop_pct": B["f_drop"],
                    "volume_ema_span_1m": B["f_volspan"],
                },
                "risk": {
                    "entry_cooldown_minutes": t["cool"],
                    "n_positions": 4,
                    "total_wallet_exposure_limit": 1,
                    "total_exposure_enforcer_enabled": True,
                    "total_exposure_enforcer_threshold": 0.99,
                    "we_excess_allowance_pct": t["we"],
                    "position_exposure_enforcer_enabled": True,
                    "position_exposure_enforcer_threshold": 0.99,
                },
                "strategy": {"trailing_martingale": {
                    "volatility_ema_span_1h": float(t["v1h"]),
                    "volatility_ema_span_1m": float(t["v1m"]),
                    "entry": {
                        "ema_span_0": t["span0"],
                        "ema_span_1": t["span1"],
                        "double_down_factor": t["ddf"],
                        "initial_ema_dist": r4(clamp(B["init_dist"] * S ** 0.7 * t["dist"], 0.003, 0.035)),
                        "initial_qty_pct": r4(clamp(B["init_qty"] * t["qty"] / S ** 0.5, 0.008, 0.045)),
                        "threshold_base_pct": r4(clamp(B["thr"] * S * t["spacing"], 0.010, 0.10)),
                        "threshold_we_weight": B["thr_we"],
                        "threshold_volatility_1h_weight": B["thr_v1h"] * (t["spacing"] if regime == "extreme_vol" else 1.0) * (0.5 if regime == "extreme_vol" else 1.0),
                        "threshold_volatility_1m_weight": 0.0,
                        "retracement_base_pct": r4(clamp(0.004 * Sretr, 0.002, 0.008)) if regime == "strong_trend" else 0.0,
                        "retracement_we_weight": 0.0,
                        "retracement_volatility_1h_weight": 0.0,
                        "retracement_volatility_1m_weight": 0.0,
                    },
                    "close": {
                        "qty_pct": B["c_qty"],
                        "threshold_base_pct": r4(clamp(B["c_thr"] * S * t["close"], 0.0025, 0.025)),
                        "threshold_we_weight": B["c_thr_we"],
                        "threshold_volatility_1h_weight": t["c_v1h"],
                        "threshold_volatility_1m_weight": 0.0,
                        "retracement_base_pct": r4(clamp(0.003 * Sretr, 0.0015, 0.006)) if regime == "strong_trend" else 0.0,
                        "retracement_volatility_1h_weight": 0.0,
                        "retracement_volatility_1m_weight": 0.0,
                    },
                }},
                "unstuck": {
                    "ema_span_0": B["u_ema0"],
                    "ema_span_1": B["u_ema1"],
                    "close_pct": r5(t["u_cp"]),
                    "ema_dist": t["u_dist"],
                    "enabled": True,
                    "loss_allowance_pct": r5(t["u_al"]),
                    "threshold": t["u_thr"],
                },
            }
            # extreme: halve the volatility weight so spacing doesn't blow out
            if regime == "extreme_vol":
                p["strategy"]["trailing_martingale"]["entry"]["threshold_volatility_1h_weight"] = r5(B["thr_v1h"] * 0.5)
            params[coin][regime] = p

    meta = {
        "source_config": "configs/examples/BTC_ETH_XRP_SOL_ADA_long.json",
        "config_version": "v8.4.0",
        "analysis": "backtests/regime_analysis_2026-10",
        "baseline_daily_log_range": r5(baseline),
        "spacing_scale": {
            f"{coin}|{regime}": r5(clamp(ranges[(coin, regime)] / baseline, 0.4, 2.2))
            for coin in COINS for regime in REGIMES
        },
        "note": "bot.long 参数集;bot.short / live / backtest / optimize 沿用基准配置。"
                "这些是基于历史波动统计的刻度起点,非优化器输出。",
    }
    out = {"_meta": meta, **params}
    (OUT / "params_by_coin_regime.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print("written params/params_by_coin_regime.json")

    # quick console sanity table: entry threshold per coin x regime
    rows = []
    for coin in COINS:
        row = {"coin": coin}
        for regime in REGIMES:
            row[regime] = params[coin][regime]["strategy"]["trailing_martingale"]["entry"]["threshold_base_pct"]
        rows.append(row)
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
