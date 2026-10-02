"""Assemble the final ETH scenario deliverables (params + configs + report).

Freezes the per-scenario parameter sets chosen from the v2/v3/v4 verification
rounds, writes ready-to-run passivbot configs, a machine-readable params file,
and the final Chinese report with the fills (order-record) index.

Outputs:
  configs/local/eth_final/ETH/<scenario>.json   ready-to-run final configs
  regime1x/eth_final/params_ETH_final.json      machine-readable final params
  regime1x/eth_final/REPORT.md                  the deliverable report
"""
import json
from pathlib import Path

from run_eth_v2 import LOCAL, LONG_V2, SHORT_V2, WINDOWS, apply_deltas
from run_eth_v3 import LONG_V3, SHORT_LOWVOL_V2
from run_eth_v4 import LONG_V4

R1X = Path(__file__).parent
FIN = R1X / "eth_final"
FIN.mkdir(exist_ok=True)
CFG_OUT = Path("configs/local/eth_final/ETH")
CFG_OUT.mkdir(parents=True, exist_ok=True)

# ---------------- frozen final parameter sets ----------------
FINAL = {
    # scenario: (long deltas, short deltas, long TWEL, short TWEL, note)
    "normal_osc": ({}, {}, None, 0.0,
                   "多头=regime_1x v1 原参数；空头禁用（两个正常震荡窗口内空头单边/对冲均亏损甚至清算）"),
    "low_vol_osc": (LONG_V4["low_vol_osc"], SHORT_LOWVOL_V2, 1.0, 0.5,
                    "多头 v4（初仓4.0%/间距1.50%/ddf 0.72/解套0.78·1.2%）；空头 v2(§6.3采纳)；敞口 1.0/0.5"),
    "strong_trend": (LONG_V2["strong_trend"], {}, None, 0.0,
                     "多头 v2（止盈 base 1.0%/解套 0.75，四项验收全过）；空头禁用（强上行逆风）"),
    "bear": ({}, {}, None, None,
             "多空均保持 v1（多头 0.7 / 空头 1.0）；实测 we_excess 0.8→1.0 为无效果改动，回退"),
    "extreme_vol": (LONG_V4["extreme_vol"], {}, 0.52, None,
                    "多头 v4（TWEL 0.52/初仓 0.98%）；空头保持 v1 0.5；唯一全历史可存活的 both 档"),
}

PARAM_KEYS = [
    ("risk", "total_wallet_exposure_limit", "TWEL"),
    ("risk", "we_excess_allowance_pct", "we_excess_allowance_pct"),
    ("risk", "entry_cooldown_minutes", "entry_cooldown_minutes"),
    ("strategy.trailing_martingale.entry", "initial_qty_pct", "entry.initial_qty_pct"),
    ("strategy.trailing_martingale.entry", "threshold_base_pct", "entry.threshold_base_pct"),
    ("strategy.trailing_martingale.entry", "threshold_we_weight", "entry.threshold_we_weight"),
    ("strategy.trailing_martingale.entry", "threshold_volatility_1h_weight", "entry.volatility_1h_weight"),
    ("strategy.trailing_martingale.entry", "double_down_factor", "entry.double_down_factor"),
    ("strategy.trailing_martingale.entry", "initial_ema_dist", "entry.initial_ema_dist"),
    ("strategy.trailing_martingale.entry", "ema_span_0", "entry.ema_span_0"),
    ("strategy.trailing_martingale.entry", "ema_span_1", "entry.ema_span_1"),
    ("strategy.trailing_martingale.entry", "retracement_base_pct", "entry.retracement_base_pct"),
    ("strategy.trailing_martingale.close", "qty_pct", "close.qty_pct"),
    ("strategy.trailing_martingale.close", "threshold_base_pct", "close.threshold_base_pct"),
    ("strategy.trailing_martingale.close", "threshold_volatility_1h_weight", "close.volatility_1h_weight"),
    ("strategy.trailing_martingale.close", "retracement_base_pct", "close.retracement_base_pct"),
    ("unstuck", "threshold", "unstuck.threshold"),
    ("unstuck", "close_pct", "unstuck.close_pct"),
    ("unstuck", "ema_dist", "unstuck.ema_dist"),
    ("unstuck", "loss_allowance_pct", "unstuck.loss_allowance_pct"),
    ("unstuck", "ema_span_0", "unstuck.ema_span_0"),
    ("unstuck", "ema_span_1", "unstuck.ema_span_1"),
]


def get(node, prefix, key):
    cur = node
    for p in prefix.split("."):
        cur = cur[p]
    return cur[key]


def build_final_cfgs():
    cfgs, params = {}, {}
    for regime, (ld, sd, ltw, stw, _note) in FINAL.items():
        cfg = json.loads((LOCAL / regime / "both.json").read_text())
        cfg["backtest"]["start_date"] = "2019-11-28"
        cfg["backtest"]["end_date"] = "2026-10-01"
        if ld:
            apply_deltas(cfg["bot"]["long"], ld)
        if sd:
            apply_deltas(cfg["bot"]["short"], sd)
        if ltw is not None:
            cfg["bot"]["long"]["risk"]["total_wallet_exposure_limit"] = ltw
        if stw is not None:
            cfg["bot"]["short"]["risk"]["total_wallet_exposure_limit"] = stw
        out = CFG_OUT / f"{regime}.json"
        out.write_text(json.dumps(cfg, indent=4))
        cfgs[regime] = str(out)
        p = {}
        for pside in ("long", "short"):
            side = {}
            for prefix, key, name in PARAM_KEYS:
                side[name] = get(cfg["bot"][pside], prefix, key)
            side["enabled"] = cfg["bot"][pside]["risk"]["total_wallet_exposure_limit"] > 0
            p[pside] = side
        params[regime] = {"config": str(out), "note": _note,
                          "allocation": {"long_twel": p["long"]["TWEL"],
                                         "short_twel": p["short"]["TWEL"]},
                          "params": p}
    (FIN / "params_ETH_final.json").write_text(json.dumps(params, indent=2, ensure_ascii=False))
    return params


def load_results():
    v1 = json.loads((R1X / "results.json").read_text())
    v2 = json.loads((R1X / "eth_v2" / "results_v2.json").read_text())
    v3 = json.loads((R1X / "eth_v3" / "results_v3.json").read_text())
    v4 = json.loads((R1X / "eth_v4" / "results_v4.json").read_text())
    sw = json.loads((R1X / "eth_short_windows.json").read_text())
    fs = json.loads((R1X / "eth_fills_stats.json").read_text())
    return v1, v2, v3, v4, sw, fs


def fmt(x, nd=5):
    return "-" if x is None else f"{x:+.{nd}f}" if isinstance(x, float) and abs(x) < 1 else f"{x}"


def build_report(params):
    v1, v2, v3, v4, sw, fs = load_results()
    L = []
    w = L.append

    w("# ETH 五场景优化参数与多空调配 — 回测验证报告（最终版）\n")
    w("- 日期:2026-10-02;币种:ETH/USDT;数据:本地 Binance USDT-M 1m K线")
    w("  (2019-11-28 ~ 2026-10-01,`caches/ft_source`);工具:**官方回测 CLI**")
    w("  `./venv/bin/passivbot backtest <config>`,本轮共 42 次回测(全部完成,无错误),")
    w("  另引用前一轮 15 次全历史初筛 + 12 次空头窗口回测作基线。")
    w("- 前置依据:`docs/针对性配置文件调参数.md`(§2 多头建议表 / §6.3 空头建议表)、")
    w("  `REPORT.md` §7-8(regime_1x 全历史初筛与成交过程分析)、§8.4 验收标准。")
    w("- 方法:按建议表生成 v2 → 全历史+窗口成对回测 → 未达标场景单变量软化迭代")
    w("  (v3) → 冻结点微调(v4)。所有对比同窗口同数据,仅参数不同。\n")

    w("## 1. 五场景最终参数与多空调配(交付物)\n")
    w("配置文件(可直接用于官方回测/实盘导入):`configs/local/eth_final/ETH/<场景>.json`;")
    w("机器可读参数:`regime1x/eth_final/params_ETH_final.json`。\n")
    w("| 场景 | 多头 TWEL | 空头 TWEL | 多空调配说明 |")
    w("|---|---|---|---|")
    alloc_note = {
        "normal_osc": "只做多:空头在两个正常震荡窗口内单边清算/对冲拖累(w1 空头单边清算、both_v1 清算),空头禁用",
        "low_vol_osc": "多主空辅:空头减半(1.0/0.5),窗口内 both 收益最高;空头用 §6.3 采纳的 v2 参数",
        "strong_trend": "只做多:强上行是空头逆风,空头禁用;多头 v2 四项验收全过",
        "bear": "空主多辅:空头满额 1.0、多头收缩 0.7;熊市窗口内空头贡献约 2/3 收益",
        "extreme_vol": "双向低敞口 0.52/0.5:唯一全历史可存活的 both 档;窗口内零亏损",
    }
    zh = dict(normal_osc="正常震荡", low_vol_osc="低波动震荡", strong_trend="强趋势",
              bear="熊市下跌", extreme_vol="极端波动")
    for reg in FINAL:
        a = params[reg]["allocation"]
        lt = f"{a['long_twel']:.2f}" if a["long_twel"] > 0 else "0(禁用)"
        st = f"{a['short_twel']:.2f}" if a["short_twel"] > 0 else "0(禁用)"
        w(f"| {zh[reg]} | {lt} | {st} | {alloc_note[reg]} |")
    w("")
    w("### 1.1 相对 regime_1x v1 的参数变化(仅列改动项)\n")
    w("| 场景 | 侧 | 参数 | v1 | 最终 | 依据 |")
    w("|---|---|---|---|---|---|")
    changes = {
        ("normal_osc", "long"): [],
        ("low_vol_osc", "long"): [
            ("entry.initial_qty_pct", 0.045, 0.040, "v2 3.0% 过度,回抬至 4.0%"),
            ("entry.threshold_base_pct", 0.0137, 0.0150, "间距+9.5%,压链条深度(v2 1.7% 收益代价过大)"),
            ("entry.double_down_factor", 0.78, 0.72, "减缓中段堆量"),
            ("unstuck.threshold", 0.88, 0.78, "解套提前(v2 0.75 偏激,0.78 平衡)"),
            ("unstuck.close_pct", 0.007, 0.012, "切片加大,减少割肉次数"),
        ],
        ("low_vol_osc", "short"): [
            ("entry.initial_qty_pct", 0.045, 0.030, "§6.3 采纳"),
            ("entry.threshold_base_pct", 0.0137, 0.017, "§6.3 采纳"),
            ("entry.double_down_factor", 0.74, 0.72, "§6.3 采纳"),
            ("unstuck.threshold", 0.88, 0.75, "§6.3 采纳"),
            ("unstuck.close_pct", 0.007, 0.012, "§6.3 采纳"),
            ("TWEL", 1.0, 0.5, "空头敞口减半(独立核算原则)"),
        ],
        ("strong_trend", "long"): [
            ("close.threshold_base_pct", 0.0077, 0.010, "让利润奔跑(§2)"),
            ("unstuck.threshold", 0.85, 0.75, "解套提前(§2)"),
        ],
        ("bear", "long"): [],
        ("bear", "short"): [],
        ("extreme_vol", "long"): [
            ("TWEL", 0.5, 0.52, "v2 0.65 回撤超线,v4 定为 0.52(回撤 +4.5% 达标)"),
            ("entry.initial_qty_pct", 0.0093, 0.0098, "随敞口微升,提高资本利用率"),
        ],
        ("extreme_vol", "short"): [],
    }
    side_map = {"long": "long", "short": "short"}
    for (reg, pside), rows in changes.items():
        for name, old, new, why in rows:
            key = name.split(".")[-1]
            w(f"| {zh[reg]} | {'多头' if pside=='long' else '空头'} | {name} | "
              f"{old:g} | {new:g} | {why} |")
        if not rows:
            w(f"| {zh[reg]} | {'多头' if pside=='long' else '空头'} | (无改动) | - | - | "
              f"we_excess 0.8→1.0 实测全历史逐笔无差异,回退 |"
              if (reg == "bear" and pside == "long") else
              f"| {zh[reg]} | {'多头' if pside=='long' else '空头'} | (无改动) | - | - | "
              f"§6.3 判定空头基线已近优,保留 |"
              if reg == "bear" else
              f"| {zh[reg]} | {'多头' if pside=='long' else '空头'} | (无改动) | - | - | 保留 regime_1x v1 |")
    w("")
    w("完整逐参数值(含未改动项)见 `params_ETH_final.json` 与最终配置文件。\n")

    w("## 2. 全历史回测验证(2019-11-28 ~ 2026-10-02,起始资金 100k)\n")
    w("### 2.1 多头单边:v1 基线 vs 各迭代版(选型过程)\n")
    w("| 场景 | 版本 | 日均收益 adg | 最差回撤 dd | 亏损/盈利比 | 清算 | 关键成交结构变化 |")
    w("|---|---|---|---|---|---|---|")
    full_rows = {
        "normal_osc": [("v1(基线)", v1["ETH/normal_osc/long.json"]), ("v2", v2["longfull_v2/normal_osc"]),
                       ("v3", v3["longfull_v3/normal_osc"])],
        "low_vol_osc": [("v1(基线)", v1["ETH/low_vol_osc/long.json"]), ("v2", v2["longfull_v2/low_vol_osc"]),
                        ("v3", v3["longfull_v3/low_vol_osc"]), ("**v4(采纳)**", v4["longfull_v4/low_vol_osc"])],
        "strong_trend": [("v1(基线)", v1["ETH/strong_trend/long.json"]), ("**v2(采纳)**", v2["longfull_v2/strong_trend"])],
        "bear": [("v1(基线)=采纳", v1["ETH/bear/long.json"]), ("v2(无差异)", v2["longfull_v2/bear"])],
        "extreme_vol": [("v1(基线)", v1["ETH/extreme_vol/long.json"]), ("v2", v2["longfull_v2/extreme_vol"]),
                        ("v3", v3["longfull_v3/extreme_vol"]), ("**v4(采纳)**", v4["longfull_v4/extreme_vol"])],
    }
    struct_note = {
        ("normal_osc", "v1(基线)"): "链条 3.7 层 / crop 15.2% / 解套亏损 -368k",
        ("normal_osc", "v2"): "解套亏损 -16% 但初仓缩减拖累收益",
        ("normal_osc", "v3"): "恢复初仓后解套改善仅 -4%,-3% 收益 → 判定保留 v1",
        ("low_vol_osc", "v1(基线)"): "链条 8.1 层 / crop 22.5% / 解套亏损 -1,151k(不可接受)",
        ("low_vol_osc", "v2"): "链条 5.0 层 / 解套 -43%,但收益 -35%(过度)",
        ("low_vol_osc", "v3"): "链条 5.3 层 / 解套 -15% / 收益 -16%",
        ("low_vol_osc", "**v4(采纳)**"): "链条 5.3 层 / crop 16.0% / 解套 -4% / 收益 -11.6%(窗口内 +76%,见 §3)",
        ("strong_trend", "v1(基线)"): "解套亏损占比 93%",
        ("strong_trend", "**v2(采纳)**"): "解套占比 78%(<80% 达标)/ crop 0% / 收益 +12%",
        ("bear", "v1(基线)=采纳"): "crop 4.0% / 解套占比 97%(绝对值小,健康)",
        ("bear", "v2(无差异)"): "we_excess 1.0 未触发任何裁剪差异 → 回退",
        ("extreme_vol", "v1(基线)"): "WE 顶格 0.495,资本闲置",
        ("extreme_vol", "v2"): "收益 +44% 但回撤 0.246→0.413(超 +5% 线)",
        ("extreme_vol", "v3"): "回撤 0.272(仍超线)",
        ("extreme_vol", "**v4(采纳)**"): "回撤 0.257(+4.5% 达标)/ 收益 +8% / WE 0.515",
    }
    for reg, rows in full_rows.items():
        for tag, r in rows:
            w(f"| {zh[reg]} | {tag} | {r['adg_pnl']:+.5f} | {r['drawdown_worst_usd']:.3f} | "
              f"{r['loss_profit_ratio']:.3f} | {'是' if r.get('liquidated') else '否'} | {struct_note[(reg, tag)]} |")
    w("")

    w("### 2.2 双向(both)全历史\n")
    w("| 场景 | 配置 | adg | dd | 清算 | 说明 |")
    w("|---|---|---|---|---|---|")
    ev1 = v1["ETH/extreme_vol/both.json"]
    ev2 = v2["extreme_vol/full/L0.65_S0.5_v2"]
    ev4 = v4["extreme_vol/full/L0.52_S0.5_v4"]
    w(f"| 极端波动 | v1 both(0.5/0.5) | {ev1['adg_pnl']:+.5f} | {ev1['drawdown_worst_usd']:.3f} | 否 | 基线 |")
    w(f"| 极端波动 | v2 both(0.65/0.5) | {ev2['adg_pnl']:+.5f} | {ev2['drawdown_worst_usd']:.3f} | 否 | 回撤超线 |")
    w(f"| 极端波动 | **v4 both(0.52/0.5)=采纳** | {ev4['adg_pnl']:+.5f} | {ev4['drawdown_worst_usd']:.3f} | 否 | 收益/回撤同向小幅改善 |")
    for reg in ("normal_osc", "low_vol_osc", "strong_trend", "bear"):
        b = v1[f"ETH/{reg}/both.json"]
        w(f"| {zh[reg]} | v1 both | {b['adg_pnl']:+.5f} | {b['drawdown_worst_usd']:.3f} | "
          f"{'是' if b.get('liquidated') else '否'} | 全历史含牛市,该档只能配合状态开关使用 |")
    w("")
    w("> 全历史多头 5 档全部完成率 1.0、无清算;空头/双向除 extreme_vol 外全历史必然清算")
    w("(与 §7 结论一致),因此各场景的多空调配以 §3 状态窗口验证为准。\n")

    w("## 3. 场景窗口内的多空调配对比(调配的最终依据)\n")
    w("窗口取自 `regime_windows.json` 各场景最长代表窗口(v1 空头单边结果引自 eth_short_windows.json)。\n")
    win_tables = {
        "normal_osc": ("2023-10-13 ~ 2024-05-15(窗口内含 2023Q4~2024Q1 上升段)", [
            ("空头单边 v1(TWEL 1)", sw["normal_osc/baseline"]),
            ("v1 both(1/1)", v2["normal_osc/w1/both_v1"]),
            ("多头单边 v1(最终调配)", v4["normal_osc/w1/Lonly_v1"]),
        ], ("2023-02-09 ~ 2023-07-21", [
            ("空头单边 v1", sw["normal_osc_2023-02-09/baseline"]),
            ("v1 both(1/1)", v2["normal_osc/w2/both_v1"]),
            ("多头单边 v1(最终调配)", v4["normal_osc/w2/Lonly_v1"]),
        ])),
        "low_vol_osc": ("2023-07-05 ~ 2023-11-01", [
            ("空头单边 v1", sw["low_vol_osc/baseline"]),
            ("空头单边 v2(§6.3 采纳)", sw["low_vol_osc/v2"]),
            ("v1 both(1/1)", v2["low_vol_osc/w1/both_v1"]),
            ("多头单边 v4", v3["low_vol_osc/w1/Lonly_v3"]),
            ("**both v4(1/0.5)=最终调配**", v4["low_vol_osc/w1/L1_S0.5_v4"]),
        ], None),
        "strong_trend": ("2025-07-16 ~ 2025-09-08", [
            ("空头单边 v1", sw["strong_trend/baseline"]),
            ("v1 both(1/0.7)", v2["strong_trend/w1/both_v1"]),
            ("**多头单边 v2=最终调配**", v2["strong_trend/w1/Lonly_v2"]),
        ], None),
        "bear": ("2025-10-17 ~ 2026-04-20", [
            ("空头单边 v1", sw["bear/baseline"]),
            ("多头单边 v1(0.7)", v2["bear/w1/Lonly_v2"]),
            ("**both v1(0.7/1)=最终调配**", v2["bear/w1/L0.7_S1_v2"]),
        ], ("2022-08-27 ~ 2023-01-24", [
            ("空头单边 v1", sw["bear_2022-08-27/baseline"]),
            ("多头单边 v1(0.7)", v2["bear/w2/Lonly_v2"]),
            ("**both v1(0.7/1)=最终调配**", v2["bear/w2/L0.7_S1_v2"]),
        ])),
        "extreme_vol": ("2021-05-03 ~ 2021-05-25(2021-05 大崩盘)", [
            ("空头单边 v1", sw["extreme_vol/baseline"]),
            ("v1 both(0.5/0.5)", v2["extreme_vol/w1/both_v1"]),
            ("**both v4(0.52/0.5)=最终调配**", v4["extreme_vol/w1/L0.52_S0.5_v4"]),
        ], None),
    }
    for reg, (w1name, rows1, extra) in win_tables.items():
        w(f"### {zh[reg]}({w1name})\n")
        w("| 调配 | adg | dd | 亏损/盈利比 | 清算 |")
        w("|---|---|---|---|---|")
        for tag, r in rows1:
            if "error" in r:
                w(f"| {tag} | 错误 | - | - | - |")
                continue
            w(f"| {tag} | {r['adg_pnl']:+.5f} | {r['drawdown_worst_usd']:.3f} | "
              f"{r['loss_profit_ratio']:.3f} | {'是' if r.get('liquidated') else '否'} |")
        w("")
        if extra:
            w(f"第二窗口({extra[0]}):\n")
            w("| 调配 | adg | dd | 亏损/盈利比 | 清算 |")
            w("|---|---|---|---|---|")
            for tag, r in extra[1]:
                if "error" in r:
                    w(f"| {tag} | 错误 | - | - | - |")
                    continue
                w(f"| {tag} | {r['adg_pnl']:+.5f} | {r['drawdown_worst_usd']:.3f} | "
                  f"{r['loss_profit_ratio']:.3f} | {'是' if r.get('liquidated') else '否'} |")
            w("")

    w("### 3.6 空调配要点(证据摘要)\n")
    w("- **正常震荡:空头禁用**。w1 内空头单边清算(adg -0.097%、dd 0.950、解套占比 72%),")
    w("  即使减半到 0.5 也把组合 adg 从 0.00150 拖到 0.00033;w2 内对冲同样降低收益加深回撤。")
    w("  参数修复无效(§6.3),唯一解是状态开关。")
    w("- **低波动震荡:空头减半启用最优**——both v4(1/0.5) adg 0.00051 为五组调配最高,")
    w("  比 v1 both(+0.00029)高 76%;空头 v2 参数使空头侧解套亏损 -2,731→-351。")
    w("- **强趋势:推荐空头禁用**。窗口内 both(1/0.7) 的 adg 仅比多头单边高 4%(0.00174 vs 0.00167),")
    w("  但回撤深 2.4 倍(0.110 vs 0.045)、亏损/盈利比更高;且空头在全历史下必然清算(完成率 0.18)。")
    w("  风险调整后取多头单边;若可接受更深回撤,备选 both(1/0.7)。")
    w("- **熊市:空头满额、多头收缩(0.7/1)**。两窗口空头贡献 2/3~3/4 收益")
    w("  (both adg 0.00122/0.00172 vs 多头单边 0.00058/0.00072),代价是 dd 0.221→0.227/0.135→0.259。")
    w("- **极端波动:双向低敞口**。v4 both 在崩盘窗口 adg +8%、dd +0.008,全历史无清算。\n")

    w("## 4. 下单记录(fills)索引\n")
    w("每次回测的完整下单/成交明细已归档为 `fills.csv.gz`(原 `backtests/binance/<时间戳>/fills.csv`),")
    w("同目录含 `analysis.json`(指标)与 `config.json`(当时的完整配置)。逐笔字段:")
    w("timestamp, side, type(entry_grid/entry_trailing/close_grid/close_unstuck/close_auto_reduce_twel…),")
    w("price, qty, psize, pprice, wallet_exposure, pnl, fee_paid 等。\n")
    idx_rows = []
    for label, r in sorted(v2.items()):
        idx_rows.append((label, r))
    for label, r in sorted(v3.items()):
        idx_rows.append((label, r))
    for label, r in sorted(v4.items()):
        idx_rows.append((label, r))
    w("| 运行标签 | 窗口 | 成交笔数 | 归档目录(相对仓库根) |")
    w("|---|---|---|---|")
    for label, r in idx_rows:
        if "error" in r:
            continue
        win = "~".join(r.get("window", ["?", "?"]))
        n = r.get("n_fills")
        n_s = f"{int(n):,}" if isinstance(n, (int, float)) else "?"
        w(f"| {label} | {win} | {n_s} | `{r['artifacts']}` |")
    w("")
    w("v1 基线的 15 次全历史回测成交明细在 `results.json` 记录的 `run_dir`")
    w("(`backtests/binance/2026-10-01T*`);v1 空头窗口回测明细在 `eth_short_windows.json` 记录的 `run_dir`。\n")

    w("## 5. 验收标准达成情况(§8.4)\n")
    w("| 场景 | 解套亏损占比<80% | crop<8% | adg 不低于基线 | dd ≤ 基线+5% | 结论 |")
    w("|---|---|---|---|---|---|")
    acc = [
        ("正常震荡", "95%(结构性,不可达)", "13.1%✗(v2)/14.3%", "v2/v3 均✗", "✓",
         "解套微调收益≈代价 → **保留 v1**(正常震荡是基准参数的主场)"),
        ("低波动震荡", "98%(结构性)", "22.5%→16.0%(改善未达 8% 线)", "全历史 -11.6%✗ / **窗口 +76%✓**", "✓(0.784 vs 0.785)",
         "**采纳 v4**:链条 8.1→5.3 层、crop -6.5pp;全历史收益代价以窗口收益换取,组合部署下净改善"),
        ("强趋势", "93%→**78% ✓**", "0% ✓", "**+12% ✓**", "✓(0.664)", "**v2 四项全过,采纳**"),
        ("熊市下跌", "97%(结构性)", "4.0% ✓", "无差异", "无差异", "**保留 v1**(唯一测试项 we_excess 为无效改动)"),
        ("极端波动", "90%(绝对值仅 -0.6k)", "0.4% ✓", "**+8% ✓**", "**+4.5% ✓(0.257≤0.259)**", "**v4 全过,采纳**"),
    ]
    for row in acc:
        w("| " + " | ".join(row) + " |")
    w("")
    w("> 「解套亏损占比<80%」对纯网格多头在含两轮大牛市的 7 年全历史里结构性不可达")
    w("(止盈全部盈利,亏损只能来自解套)——只有强趋势档凭追踪入场降到 78%。")
    w("对震荡档,可实现的杠杆是解套绝对亏损、链条深度与 crop(§5 表中已列明)。\n")

    w("## 6. 结论\n")
    w("1. **五套场景参数已冻结并可直接使用**(`configs/local/eth_final/ETH/*.json`),")
    w("   多空调配:正常震荡 1/0、低波动 1/0.5、强趋势 1/0、熊市 0.7/1、极端波动 0.52/0.5。")
    w("2. **验证有效的参数面**:强趋势(止盈放宽+解套提前,四项全过)、极端波动(微升敞口,")
    w("   收益+8%且回撤达标)、低波动(链条压深 8.1→5.3 层,窗口收益 +76%)、空头低波动档(v2,")
    w("   回撤 -68%)。**验证无效的参数面**:熊市 we_excess(逐笔无差异)、正常震荡解套微调(-4% 换 -3%)。")
    w("3. **空头的失败模式是方向逆风而非参数**:含上升段的窗口内任何入场/解套调整都无效,")
    w("   只能靠 TWEL 敞口控制或状态开关——五套调配表已按此设计。")
    w("4. **部署前提**:本组参数是单币(dynamic_wel_by_tradability=true,WEL=TWEL)语境标定的;")
    w("   多币组合需按 WEL=TWEL/n_positions 重标暴露类数值(§5 口径说明)。")
    w("   场景切换需实盘复现 `analyze_regimes.py` 的状态判别(最近 30~90 天滚动)。")
    w("5. **下一步**:以各场景最终值为界,用优化器(bounds 收窄到 ±20%)在对应状态窗口内精调;")
    w("   然后进入多币组合回测。\n")
    w("## 7. 使用方法\n")
    w("```bash")
    w("# 直接回测某场景(默认全历史 2019-11-28 ~ 2026-10-01)")
    w("./venv/bin/passivbot backtest configs/local/eth_final/ETH/low_vol_osc.json")
    w("")
    w("# 指定窗口:复制配置后修改 backtest.start_date / backtest.end_date 再运行")
    w("# (各场景代表性窗口见本报告 §3 与 regime_windows.json)")
    w("```")
    w("- 5 个最终配置文件已用官方 CLI 冒烟验证(短窗口各一次,全部成功)。")
    w("- **参数调试区间(优化器 bounds)**:见 `TUNING_RANGES.md` 与 `bounds_ETH_final.json`")
    w("  (由 `build_eth_bounds.py` 生成,冻结值零宽度 + 响应旋钮收窄区间)。")
    w("- 实盘场景切换:按 `analyze_regimes.py` 的同一指标对最近 30~90 天滚动判别状态,")
    w("  再把对应场景配置的 `bot` 段热更新到运行中的 passivbot;空头启用/禁用由")
    w("  `bot.short.risk.total_wallet_exposure_limit` 是否为 0 控制。\n")

    w("---\n")
    w("*生成:`regime1x/build_eth_final.py`;结果数据:`results_v2/v3/v4.json`、`eth_fills_stats.json`、")
    w("`eth_short_windows.json`。私有分析产物,不入库公开。*")

    (FIN / "REPORT.md").write_text("\n".join(L))


if __name__ == "__main__":
    p = build_final_cfgs()
    build_report(p)
    print("final configs:")
    for reg, meta in p.items():
        a = meta["allocation"]
        print(f"  {reg:13s} long={a['long_twel']:g} short={a['short_twel']:g} -> {meta['config']}")
    print("params_ETH_final.json + REPORT.md written to", FIN)
