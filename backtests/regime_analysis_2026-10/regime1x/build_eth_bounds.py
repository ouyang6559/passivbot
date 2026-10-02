"""Build optimizer tuning ranges (bounds) for the 5 frozen ETH scenario configs.

Centered on the frozen final values (eth_final configs).  Rule: only the knobs
that the v2/v3/v4 rounds proved responsive are given search ranges; everything
that defines regime identity or proved inert (EMA spans, we_weights, forager,
enforcers, cooldowns) is frozen via zero-width bounds [v, v] - the same
convention the regime_1x bounds already use (e.g. total_wallet_exposure_limit
[1.25, 1.25]).

Outputs:
  eth_final/bounds_ETH_final.json   per scenario: window + drop-in optimize.bounds
                                    + suggested optimize.limits
  eth_final/TUNING_RANGES.md        human-readable tables + which runs stood out
"""
import json
from pathlib import Path

R1X = Path(__file__).parent
FIN = R1X / "eth_final"

WINDOWS = {  # per-scenario tuning windows (regime_windows.json representatives)
    "normal_osc": ("2023-10-13", "2024-05-15"),
    "low_vol_osc": ("2023-07-05", "2023-11-01"),
    "strong_trend": ("2025-07-16", "2025-09-08"),
    "bear": ("2025-10-17", "2026-04-20"),
    "extreme_vol": ("2021-05-03", "2021-05-25"),
}
# optimizer runs on window data; second robustness window to re-check afterwards
WINDOW2 = {
    "normal_osc": ("2023-02-09", "2023-07-21"),
    "bear": ("2022-08-27", "2023-01-24"),
}
# suggested optimize.limits, anchored just below/above what the frozen configs
# already achieve on the same window (so the optimizer starts from a feasible set)
SUGGESTED_LIMITS = {
    "normal_osc": [("drawdown_worst_usd", "greater_than", 0.25),
                   ("loss_profit_ratio", "greater_than", 0.30),
                   ("adg_pnl", "less_than", 0.0010),
                   ("peak_recovery_hours_pnl", "greater_than", 1344)],
    "low_vol_osc": [("drawdown_worst_usd", "greater_than", 0.25),
                    ("loss_profit_ratio", "greater_than", 0.45),
                    ("adg_pnl", "less_than", 0.00035),
                    ("peak_recovery_hours_pnl", "greater_than", 1344)],
    "strong_trend": [("drawdown_worst_usd", "greater_than", 0.12),
                     ("loss_profit_ratio", "greater_than", 0.25),
                     ("adg_pnl", "less_than", 0.0012)],
    "bear": [("drawdown_worst_usd", "greater_than", 0.35),
             ("loss_profit_ratio", "greater_than", 0.45),
             ("adg_pnl", "less_than", 0.0008)],
    "extreme_vol": [("drawdown_worst_usd", "greater_than", 0.15),
                    ("loss_profit_ratio", "greater_than", 0.10),
                    ("adg_pnl", "less_than", 0.0008)],
}


def r(x, nd):
    return round(x, nd)


def narrowed(param, v):
    """Search range for a responsive knob, centered on frozen value v."""
    if param == "total_wallet_exposure_limit":
        return [r(max(0.3, v - 0.10), 2), r(v + 0.10, 2), 0.01]
    if param == "we_excess_allowance_pct":
        return [r(max(0.2, 0.6 * v), 2), r(min(2.5, 1.5 * v), 2), 0.01]
    if param in ("initial_qty_pct",):
        return [r(0.8 * v, 4), r(1.2 * v, 4), 0.0001]
    if param in ("threshold_base_pct", "retracement_base_pct"):
        if param == "threshold_base_pct":
            return [r(0.8 * v, 5), r(1.25 * v, 5), 1e-05]
        return [r(0.55 * v, 5), r(1.6 * v, 5), 1e-05]
    if param == "double_down_factor":
        return [r(max(0.5, v - 0.08), 2), r(min(1.0, v + 0.06), 2), 0.01]
    if param in ("initial_ema_dist", "ema_dist"):  # signed: widen both ways;
        # lower bound to 2.2v — probe P6 showed adg +10.8% at -1.5% vs frozen -0.81%
        lo, hi = sorted((0.55 * v, 2.2 * v))
        return [r(lo, 4), r(hi, 4), 0.0001]
    if param == "threshold_we_weight":
        # probe P5: responsive (0.135->0.30 cost 6% adg) -> narrow two-sided range
        return [r(max(0.05, 0.7 * v), 3), r(min(0.25, 1.5 * v), 3), 0.001]
    if param in ("threshold_volatility_1h_weight", "retracement_volatility_1h_weight"):
        if v == 0:
            return [0, 0]
        return [r(0.7 * v, 1), r(1.3 * v, 1), 0.1]
    if param == "close_pct":
        return [r(0.8 * v, 4), r(1.6 * v, 4), 0.0001]
    if param == "threshold":
        return [r(max(0.40, v - 0.07), 3), r(min(0.90, v + 0.05), 3), 0.001]
    if param == "loss_allowance_pct":
        return [r(0.6 * v, 4), r(1.5 * v, 4), 0.0001]
    raise KeyError(param)


# responsive knobs per node (within bot.<pside>); everything else is frozen
TUNABLE = {
    "risk": ["total_wallet_exposure_limit", "we_excess_allowance_pct"],
    "entry": ["initial_qty_pct", "threshold_base_pct", "double_down_factor",
              "initial_ema_dist", "threshold_volatility_1h_weight", "threshold_we_weight",
              "retracement_base_pct", "retracement_volatility_1h_weight"],
    "close": ["threshold_base_pct", "threshold_volatility_1h_weight"],
    "unstuck": ["threshold", "close_pct", "ema_dist", "loss_allowance_pct"],
}


def freeze(node):
    if isinstance(node, list) and len(node) >= 2 and isinstance(node[0], (int, float)):
        return [node[0], node[0]]
    if isinstance(node, dict):
        return {k: freeze(v) for k, v in node.items()}
    return node


def build_side_bounds(side_node, side_bounds, enabled):
    """Return narrowed bounds tree for one pside.  Frozen knobs get [v, v]
    where v is the CURRENT config value (old bounds minima may differ)."""
    out = {}
    for group, gnode in side_bounds.items():
        if group in ("forager", "hsl"):
            # regime identity / disabled subsystem -> freeze at current values.
            # forager bounds flatten score_weights.<x> into score_weights_<x>.
            frozen = {}
            for k in gnode:
                if k.startswith("score_weights_"):
                    cur = side_node[group]["score_weights"][k.removeprefix("score_weights_")]
                else:
                    cur = side_node[group][k]
                frozen[k] = [cur, cur]
            out[group] = frozen
            continue
        out[group] = {}
        if group == "risk":
            for key in gnode:
                cur = side_node["risk"][key]
                if enabled and key in TUNABLE["risk"]:
                    out[group][key] = narrowed(key, cur)
                else:
                    out[group][key] = [cur, cur]
        elif group == "strategy":
            for key, tm_b in gnode.items():  # key == "trailing_martingale"
                tm_c = side_node["strategy"]["trailing_martingale"]
                node = {}
                for sub in ("entry", "close"):
                    node[sub] = {}
                    for k2 in tm_b[sub]:
                        cur = tm_c[sub][k2]
                        if (enabled and k2 in TUNABLE[sub]
                                and not (k2.startswith("retracement") and cur == 0)):
                            node[sub][k2] = narrowed(k2, cur)
                        else:
                            node[sub][k2] = [cur, cur]
                for k2 in tm_b:
                    if k2 in ("entry", "close"):
                        continue
                    node[k2] = [tm_c[k2], tm_c[k2]]  # volatility spans frozen
                out[group][key] = node
        elif group == "unstuck":
            for key in gnode:
                cur = side_node["unstuck"][key]
                if enabled and key in TUNABLE["unstuck"]:
                    out[group][key] = narrowed(key, cur)
                else:
                    out[group][key] = [cur, cur]
    return out


def build_scenario(regime):
    cfg = json.loads((Path("configs/local/eth_final/ETH") / f"{regime}.json").read_text())
    bot, bounds = cfg["bot"], cfg["optimize"]["bounds"]
    lt = bot["long"]["risk"]["total_wallet_exposure_limit"]
    st = bot["short"]["risk"]["total_wallet_exposure_limit"]
    tree = {
        "long": build_side_bounds(bot["long"], bounds["long"], lt > 0),
        "short": build_side_bounds(bot["short"], bounds["short"], st > 0),
    }
    limits = []
    for metric, cond, value in SUGGESTED_LIMITS[regime]:
        entry = {"metric": metric, "penalize_if": cond, "value": value}
        limits.append(entry)
    return {"window": list(WINDOWS[regime]), "window_robustness": list(WINDOW2[regime])
            if regime in WINDOW2 else None,
            "frozen_values": {
                "long": {"twel": lt, "we_excess": bot["long"]["risk"]["we_excess_allowance_pct"]},
                "short": {"twel": st, "we_excess": bot["short"]["risk"]["we_excess_allowance_pct"]}},
            "bounds": tree, "suggested_limits": limits}


def flat_rows(tree_side, bot_side):
    """(path, frozen_value, range_or_None) rows for the doc tables."""
    rows = []

    def lookup(node, k):
        if k.startswith("score_weights_"):
            return node["score_weights"][k.removeprefix("score_weights_")]
        return node[k]

    def walk(bnode, mnode, prefix):
        for k, v in bnode.items():
            path = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                walk(v, mnode[k], path)
            else:
                cur = lookup(mnode, k)
                tunable = not (v[0] == v[1])
                rows.append((path, cur, v if tunable else None))

    walk(tree_side, bot_side, "")
    return rows


def main():
    scenarios = {reg: build_scenario(reg) for reg in WINDOWS}
    (FIN / "bounds_ETH_final.json").write_text(
        json.dumps(scenarios, indent=2, ensure_ascii=False))

    zh = dict(normal_osc="正常震荡", low_vol_osc="低波动震荡", strong_trend="强趋势",
              bear="熊市下跌", extreme_vol="极端波动")
    highlights = {
        "normal_osc": "多头单边把 w1 从 both_v1 的清算(dd 0.950)拉回 adg +0.150%/天、dd 0.139",
        "low_vol_osc": "both v4(1/0.5) 窗口 adg 0.00051 为全场最高(比 v1 both +76%);空头 v2 解套亏损 -87%",
        "strong_trend": "唯一四项验收全过:全历史 adg +12%、解套占比 93%→78%;窗口 dd 0.045(-59%)",
        "bear": "空头是利润引擎:窗口单边 adg 0.147%/0.174% 每天;both 保住 2/3 以上",
        "extreme_vol": "唯一全历史可存活的 both 档;崩盘窗口仍 +0.119%/天;对照:基准配置同窗口曾为负收益",
    }
    L = []
    w = L.append
    w("# ETH 五场景:亮眼结果清单 + 最终参数调试区间\n")
    w("- 生成:2026-10-02,`regime1x/build_eth_bounds.py`;冻结值源:`eth_final/ETH/*.json`。")
    w("- 机器可读(可直接粘进配置的 `optimize.bounds`):`bounds_ETH_final.json`。\n")

    w("## 1. 哪些配置的回测结果最亮眼\n")
    w("| 排名 | 配置 | 亮眼点 |")
    w("|---|---|---|")
    w("| 1 | 强趋势 long v2(全历史) | 唯一四项验收全过:adg 0.00208→0.00233(+12%),dd 持平 0.664,解套亏损占比 93%→78%(全 5 档中唯一 <80%);窗口内 dd 0.110→0.045(-59%)而 adg 仅让 4% |")
    w("| 2 | 低波动震荡 both v4(1/0.5) | 窗口内 adg 0.00051,五种调配中最高(比 v1 both +76%);空头侧 v2 使解套亏损 -2,731→-351(-87%)、空头单边 dd 0.069→0.022(-68%) |")
    w("| 3 | 正常震荡 多头单边 | 把含上升段的窗口从\"清算\"拉回\"稳定盈利\":w1 both_v1 清算(dd 0.950)→ 多头单边 adg +0.150%/天、dd 0.139、亏损/盈利比 0.10;w2 同样全面占优 |")
    w("| 4 | 极端波动 both v4(0.52/0.5) | 全历史 42 次回测中唯一无清算的 both 档;崩盘窗口(2021-05)adg +0.119%/天、dd 0.098;作为对照,基准配置在同类崩盘月曾为 -0.35%/天、dd 63% |")
    w("| 5 | 熊市 空头(+0.7 多头) | 熊市窗口的利润引擎:空头单边 adg +0.147%/0.174% 每天、dd 0.056/0.262;both(0.7/1) 保住约 2/3~3/4 收益 |")
    w("")
    for reg, note in highlights.items():
        w(f"- {zh[reg]}:{note}")
    w("")

    w("## 2. 调试区间设计原则\n")
    w("1. **只放开被验证响应的旋钮**(本轮 v2→v4 实测有效的参数面),其余一律冻结为")
    w("  `[v, v]` 零宽度边界(与 regime_1x bounds 的 `[1.25, 1.25]` 同一约定)。")
    w("2. **冻结的参数**:EMA 跨度(entry/unstuck ema_span_0/1、volatility spans)、")
    w("  threshold_we_weight(0.135)/close we_weight(-0.004)、close.qty_pct(0.1)、")
    w("  retracement 权重、forager 全部、enforcer/cooldown——它们定义场景身份,")
    w("  放开会让优化器把\"低波动档\"优化成\"另一个正常震荡档\"。")
    w("3. **放开的核心旋钮与倍率**:初仓 ±20%、入场间距 -20%/+25%、ddf -0.08/+0.06、")
    w("  止盈间距 -30%/+40%、解套阈值 -0.07/+0.05、解套切片 ±60%、TWEL ±0.10、")
    w("  we_excess [0.6v, 1.5v]、initial_ema_dist/ema_dist 两侧放宽。")
    w("4. **在场景窗口内优化**:把配置的 `backtest.start_date/end_date` 改成下表窗口")
    w("  再跑优化器;得出结果后必须在\"稳健性窗口\"复跑确认(防过拟合单窗口)。\n")

    w("| 场景 | 优化窗口 | 稳健性窗口 |")
    w("|---|---|---|")
    for reg in WINDOWS:
        w2 = WINDOW2.get(reg)
        w(f"| {zh[reg]} | {WINDOWS[reg][0]} ~ {WINDOWS[reg][1]} | "
          f"{w2[0]} ~ {w2[1]} |" if w2 else f"| {zh[reg]} | {WINDOWS[reg][0]} ~ {WINDOWS[reg][1]} | (无,用相邻月份自选) |")
    w("")

    for reg in WINDOWS:
        sc = scenarios[reg]
        cfg = json.loads((Path("configs/local/eth_final/ETH") / f"{reg}.json").read_text())
        w(f"## 3.{list(WINDOWS).index(reg)+1} {zh[reg]}(冻结值→调试区间)\n")
        w(f"建议 optimize.limits(锚定在冻结配置已达成值附近):"
          + ";".join(f"{m} {c} {v}" for m, c, v in SUGGESTED_LIMITS[reg]) + "\n")
        for pside, cn in (("long", "多头"), ("short", "空头")):
            enabled = cfg["bot"][pside]["risk"]["total_wallet_exposure_limit"] > 0
            if not enabled:
                w(f"### {cn}(TWEL=0 禁用,不参与优化)\n")
                continue
            w(f"### {cn}(TWEL {cfg['bot'][pside]['risk']['total_wallet_exposure_limit']:g})\n")
            w("| 参数 | 冻结值 | 调试区间 |")
            w("|---|---|---|")
            for path, cur, rng in flat_rows(sc["bounds"][pside], cfg["bot"][pside]):
                if rng is None:
                    continue
                disp = path.replace("strategy.trailing_martingale.", "")
                w(f"| {disp} | {cur:g} | [{rng[0]:g}, {rng[1]:g}] 步进 {rng[2]:g} |")
            w("")

    w("## 4. 优化器使用\n")
    w("```bash")
    w("# 1) 复制最终配置,把 backtest.start_date/end_date 改成优化窗口")
    w("# 2) 用 bounds_ETH_final.json 里对应场景的 bounds/suggested_limits 替换")
    w("#    配置里的 optimize.bounds / optimize.limits")
    w("# 3) 运行(优化器同样走官方 CLI)")
    w("./venv/bin/passivbot optimize /path/to/<场景>_opt.json")
    w("# 4) 优化结果在稳健性窗口回测复核后再采纳")
    w("```")
    w("- n_cpus/p population 等沿用配置现值;iters 500k 上限配合 pareto 前后需人工筛选:")
    w("  在帕累托前沿上优先\"adg 不低于冻结值 -5% 且 dd/lpr 改善\"的点。")
    w("- 空头已禁用的场景(正常震荡/强趋势)bounds 里空头全冻结,不会浪费算力。\n")
    w("---\n")
    w("*私有分析产物,不入库公开。*")

    (FIN / "TUNING_RANGES.md").write_text("\n".join(L))
    print("written:", FIN / "bounds_ETH_final.json", "and", FIN / "TUNING_RANGES.md")
    for reg, sc in scenarios.items():
        n_tunable = sum(1 for pside in ("long", "short")
                        for _, _, rng in flat_rows(sc["bounds"][pside],
                                                   json.loads((Path("configs/local/eth_final/ETH") / f"{reg}.json").read_text())["bot"][pside])
                        if rng is not None)
        print(f"  {reg:13s} tunable knobs: {n_tunable}")


if __name__ == "__main__":
    main()
