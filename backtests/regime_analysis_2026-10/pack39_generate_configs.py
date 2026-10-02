"""Parse the 13-coin research-package doc and emit 39 single-coin backtest configs.

Reads `docs/Passivbot_13币_多空_39套参数_回测研究包(chatgpt).md` yaml blocks, maps
them onto the validated local regime_1x_bt template, and writes one config per
(coin, mode) under pack39/configs. Window: 2022-01-01 .. 2026-10-02, maker fee 0
and zero slippage per the doc's unified execution constraints.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent
REPO = ROOT.parent.parent
DOC = REPO / "docs" / "Passivbot_13币_多空_39套参数_回测研究包(chatgpt).md"
TEMPLATE = REPO / "configs" / "local" / "regime_1x_bt" / "BTC" / "normal_osc" / "long.json"
OUT = ROOT / "pack39" / "configs"

START, END = "2022-01-01", "2026-10-02"
STARTING_BALANCE = 100_000
MAKER_FEE = 0.0
SLIPPAGE = 0.0

# neutral forager (configs/examples/default_trailing_martingale_long.json)
FORAGER = {
    "score_weights": {"ema_readiness": 0.21, "volatility": 0.61, "volume": 0.18},
    "volatility_ema_span_1m": 2274.0,
    "volume_drop_pct": 0.04,
    "volume_ema_span_1m": 310.0,
}


def parse_yaml_block(text: str) -> dict:
    params = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.lower() in ("true", "false"):
            val = v.lower() == "true"
        else:
            try:
                val = float(v) if "." in v or "e" in v.lower() else int(v)
            except ValueError:
                val = v
        params[k.strip()] = val
    return params


def parse_doc() -> dict:
    """profiles[coin][mode][pside] = params, mode in long/short/both."""
    profiles: dict = {}
    coin = None
    mode = None
    lines = DOC.read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^### ([A-Z]{2,5})\s*$", line)
        if m:
            coin = m.group(1)
            mode = None
            profiles.setdefault(coin, {})
            i += 1
            continue
        m = re.match(r"^#### (LONG|SHORT|BOTH)\s*$", line)
        if m and coin:
            mode = m.group(1).lower()
            profiles[coin].setdefault(mode, {})
            i += 1
            continue
        if coin and mode and line.strip().startswith("```yaml"):
            block = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                block.append(lines[i])
                i += 1
            params = parse_yaml_block("\n".join(block))
            pside = params.get("side")
            profiles[coin][mode][pside] = params
        i += 1
    return profiles


def map_strategy_params(p: dict) -> tuple[dict, dict, dict]:
    """doc params -> (strategy.trailing_martingale, unstuck, risk)."""
    strategy = {
        "volatility_ema_span_1h": p["volatility_ema_span_1h"],
        "volatility_ema_span_1m": p["volatility_ema_span_1m"],
        "entry": {
            "ema_span_0": p["entry.ema_span_0"],
            "ema_span_1": p["entry.ema_span_1"],
            "ema_gate_mode": p["entry.ema_gate_mode"],
            "double_down_factor": p["entry.double_down_factor"],
            "initial_ema_dist": p["entry.initial_ema_dist"],
            "initial_qty_pct": p["entry.initial_qty_pct"],
            "threshold_base_pct": p["entry.threshold_base_pct"],
            "threshold_we_weight": p["entry.threshold_we_weight"],
            "threshold_volatility_1h_weight": p["entry.threshold_volatility_1h_weight"],
            "threshold_volatility_1m_weight": p["entry.threshold_volatility_1m_weight"],
            "retracement_base_pct": p["entry.retracement_base_pct"],
            "retracement_we_weight": p["entry.retracement_we_weight"],
            "retracement_volatility_1h_weight": p["entry.retracement_volatility_1h_weight"],
            "retracement_volatility_1m_weight": p["entry.retracement_volatility_1m_weight"],
        },
        "close": {
            "qty_pct": p["close.close_qty_pct"],
            "threshold_base_pct": p["close.close_threshold_base_pct"],
            "threshold_we_weight": p["close.close_threshold_we_weight"],
            "threshold_volatility_1h_weight": p["close.close_threshold_volatility_1h_weight"],
            "threshold_volatility_1m_weight": p["close.close_threshold_volatility_1m_weight"],
            "retracement_base_pct": p["close.close_retracement_base_pct"],
            "retracement_volatility_1h_weight": p["close.close_retracement_volatility_1h_weight"],
            "retracement_volatility_1m_weight": p["close.close_retracement_volatility_1m_weight"],
        },
    }
    unstuck = {
        "ema_span_0": p["unstuck.ema_span_0"],
        "ema_span_1": p["unstuck.ema_span_1"],
        "close_pct": p["unstuck_close_pct"],
        "ema_dist": p["unstuck_ema_dist"],
        "enabled": p["unstuck_enabled"],
        "loss_allowance_pct": p["unstuck_loss_allowance_pct"],
        "threshold": p["unstuck_threshold"],
    }
    risk = {
        "entry_cooldown_minutes": p["risk.entry_cooldown_minutes"],
        "n_positions": p["risk.n_positions"],
        "total_wallet_exposure_limit": p["risk.total_wallet_exposure_limit"],
        "total_exposure_enforcer_enabled": p["risk.total_exposure_enforcer_enabled"],
        "total_exposure_enforcer_threshold": p["risk.total_exposure_enforcer_threshold"],
        "position_exposure_enforcer_enabled": p["risk.position_exposure_enforcer_enabled"],
        "position_exposure_enforcer_threshold": p["risk.position_exposure_enforcer_threshold"],
        "we_excess_allowance_pct": p["risk.we_excess_allowance_pct"],
    }
    return strategy, unstuck, risk


def build_config(coin: str, mode: str, profile: dict) -> dict:
    cfg = json.loads(TEMPLATE.read_text())
    # drop template metadata snapshots: they freeze the template's coin list
    # (_coins_sources records approved_coins as BTC and wins over live.approved_coins)
    for k in ("_raw", "_raw_effective", "_transform_log", "_coins_sources", "optimize"):
        cfg.pop(k, None)
    enabled_sides = ["long"] if mode == "long" else ["short"] if mode == "short" else ["long", "short"]
    for pside in ("long", "short"):
        bot = cfg["bot"][pside]
        bot["forager"] = dict(FORAGER)
        if pside in enabled_sides:
            strategy, unstuck, risk = map_strategy_params(profile[pside])
            bot["strategy"]["trailing_martingale"] = strategy
            bot["unstuck"] = unstuck
            bot["risk"] = risk
    cfg["live"]["approved_coins"] = {
        "long": [coin] if "long" in enabled_sides else [],
        "short": [coin] if "short" in enabled_sides else [],
    }
    cfg["live"]["leverage"] = 1
    cfg["live"]["market_orders_allowed"] = False
    cfg["live"]["time_in_force"] = "good_till_cancelled"
    bt = cfg["backtest"]
    bt["start_date"] = START
    bt["end_date"] = END
    bt["starting_balance"] = STARTING_BALANCE
    bt["maker_fee_override"] = MAKER_FEE
    bt["market_order_slippage_pct"] = SLIPPAGE
    bt["ohlcv_source_dir"] = str(REPO / "caches" / "ft_source")
    bt["offline"] = True
    return cfg


def main():
    profiles = parse_doc()
    n_blocks = sum(len(m) for c in profiles.values() for m in c.values())
    print(f"parsed {len(profiles)} coins, {n_blocks} side-blocks")
    missing = [c for c in profiles for m in ("long", "short", "both") if m not in profiles[c]]
    if missing:
        raise SystemExit(f"missing modes: {missing}")
    bad = [f"{c}/{m}/{s}" for c in profiles for m in profiles[c] for s in profiles[c][m] if s not in ("long", "short")]
    if bad:
        raise SystemExit(f"unexpected side keys: {bad}")
    (ROOT / "pack39").mkdir(parents=True, exist_ok=True)
    (ROOT / "pack39" / "profiles_parsed.json").write_text(json.dumps(profiles, indent=2, default=str))
    n = 0
    for coin in sorted(profiles):
        for mode in ("long", "short", "both"):
            cfg = build_config(coin, mode, profiles[coin][mode])
            path = OUT / coin / f"{mode}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(cfg, indent=4))
            n += 1
    print(f"wrote {n} configs under {OUT}")


if __name__ == "__main__":
    main()
