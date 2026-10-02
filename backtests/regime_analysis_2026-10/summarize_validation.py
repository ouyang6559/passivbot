"""Summarize validation_results.json and backfill REPORT.md section 5."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
RUNS = ROOT / "backtest_runs"
MANIFEST = json.loads((RUNS / "manifest.json").read_text())
RESULTS = json.loads((RUNS / "validation_results.json").read_text())
CN = {
    "normal_osc": "正常震荡",
    "low_vol_osc": "低波动震荡",
    "strong_trend": "强趋势(上行)",
    "bear": "熊市下跌",
    "extreme_vol": "极端波动",
}
METRICS = [
    ("adg_pnl", "日均收益率 adg_pnl", 4),
    ("mdg_pnl", "日收益中位数 mdg_pnl", 4),
    ("drawdown_worst_usd", "最差回撤(USD)", 3),
    ("loss_profit_ratio", "亏损/盈利比", 3),
    ("peak_recovery_hours_pnl", "PnL 新高恢复(时)", 1),
    ("position_held_hours_max", "最长持仓(时)", 1),
    ("position_unchanged_hours_max", "最长无成交(时)", 1),
]

L = []
L.append("共 5 个窗口 x 2 配置 = 10 次 1m 回测(同窗口同数据,仅参数不同;5 币齐全)。")
L.append("`regime` 列 = 每币套用其在该状态下的参数集(策略/解套/风险经 coin_overrides,")
L.append("forager 全局套用该状态模板);`base` 列 = 基准配置原样。")
L.append("")
for regime in CN:
    b = RESULTS.get(f"val_{regime}_base.json", {})
    r = RESULTS.get(f"val_{regime}_regime.json", {})
    if "analysis" not in b or "analysis" not in r:
        L.append(f"### {CN[regime]}({MANIFEST[f'val_{regime}_base.json']['start']} ~ "
                 f"{MANIFEST[f'val_{regime}_base.json']['end']})")
        L.append("")
        L.append(f"- 缺失:{'base ' + b.get('error','?') if 'analysis' not in b else ''}"
                 f"{'regime ' + r.get('error','?') if 'analysis' not in r else ''}")
        L.append("")
        continue
    ba, ra = b["analysis"], r["analysis"]
    L.append(f"### {CN[regime]}({MANIFEST[f'val_{regime}_base.json']['start']} ~ "
             f"{MANIFEST[f'val_{regime}_base.json']['end']},{b['seconds']}s/{r['seconds']}s)")
    L.append("")
    L.append("| 指标 | base | regime 状态参数集 |")
    L.append("|---|---|---|")
    for key, label, nd in METRICS:
        L.append(f"| {label} | {ba.get(key, float('nan')):.{nd}f} | {ra.get(key, float('nan')):.{nd}f} |")
    L.append(f"| 完成率 / 爆仓 | {ba.get('backtest_completion_ratio','-')} / {ba.get('liquidated','-')} | "
             f"{ra.get('backtest_completion_ratio','-')} / {ra.get('liquidated','-')} |")
    L.append("")

L.append("**解读口径**:这不是寻优对比——状态参数集的目标是")
L.append("在对应行情状态下表现出与设计一致的防御/进攻倾向")
L.append("(熊市/极端:更低回撤与亏损占比、更短持仓;强趋势:让利润奔跑;低波动:稳定的网格成交),")
L.append("而非单点收益率最大。短窗口结果噪声大,任何结论都应以")
L.append("全历史优化器精调为准。")
L.append("")

report = (ROOT / "REPORT.md").read_text()
marker = "<!-- 由 summarize_validation.py 回填 -->"
assert marker in report
report = report.replace(marker, "\n".join(L))
(ROOT / "REPORT.md").write_text(report)
print("REPORT.md section 5 backfilled")
