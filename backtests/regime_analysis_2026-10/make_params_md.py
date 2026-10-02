"""Generate the annotated params_annotated.md from params_by_coin_regime.json."""
import json
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "params"
data = json.loads((OUT / "params_by_coin_regime.json").read_text())
stats_rows = {}
import csv
with open(ROOT / "regime_stats.csv") as f:
    for row in csv.DictReader(f):
        stats_rows[(row["coin"], row["regime"])] = row
windows = json.loads((ROOT / "regime_windows.json").read_text())

COINS = ["BTC", "ETH", "XRP", "SOL", "ADA"]
REGIMES = ["normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"]
CN = {
    "normal_osc": "正常震荡",
    "low_vol_osc": "低波动震荡",
    "strong_trend": "强趋势(上行)",
    "bear": "熊市下跌",
    "extreme_vol": "极端波动",
}

def pct(x):
    return f"{100 * float(x):.2f}%"

def fmt_param(path, getter, fmt=str):
    return [fmt(getter(data[c][r], path)) for c in COINS for r in REGIMES]

L = []
L.append("# 五种行情状态参数集(每币 x 5 状态,共 25 套)")
L.append("")
L.append("> 生成:`backtests/regime_analysis_2026-10`(分析脚本与中间数据同目录)。")
L.append("> 数据源:Binance USDT-M 合约公开 1h K 线(2021-01-01 ~ 2026-10-01,无鉴权行情数据)。")
L.append("> 基准配置:`configs/examples/BTC_ETH_XRP_SOL_ADA_long.json`(v8.4.0,trailing_martingale,仅多头)。")
L.append(">")
L.append("> **这些参数是基于历史波动统计的刻度起点,不是优化器输出。**")
L.append("> 建议把它们作为起始点,用仓库优化器对各币再精调")
L.append(">(把 `optimize.bounds` 收窄到本文件数值 ±20% 左右)。")
L.append("")

L.append("## 1. 行情状态定义(每币独立标定)")
L.append("")
L.append("| 状态 | 判定规则(按优先级,基于每币自身分布的分位数) |")
L.append("|---|---|")
L.append("| 极端波动 | 日实现波动率 ≥ P98,或单日涨跌幅绝对值 ≥ P98(崩盘/插针日) |")
L.append("| 熊市下跌 | 价格 < EMA90,且 30 日收益处于最差 P15 且为负(或距 90 日高点回撤 > 20%) |")
L.append("| 强趋势(上行) | 30 日收益处于最好 P15 且 > +8%,价格 ≥ EMA90 |")
L.append("| 低波动震荡 | 日实现波动率 ≤ P30,且 14 日漂移小(≤ P40 的 \\|漂移\\|) |")
L.append("| 正常震荡 | 其余情况 |")
L.append("")

L.append("## 2. 刻度原理(每条规则对应参数)")
L.append("")
L.append("- **间距比例 S**:状态内中位日振幅 ÷ 五币正常震荡中位振幅(XRP 5.51%)。")
L.append("  入场/止盈网格距离与已实现振幅近似线性相关(`docs/config.bot.md` 中阈值公式),故按 S 缩放,")
L.append("  再叠加状态倾向系数(熊市/极端再放宽 15%/25% 防接刀)。")
L.append("- **首次入场量**:∝ 1/√S —— 波动越大,同等 WEL 切成更多阶梯;熊市/极端再乘 0.65/0.50。")
L.append("- **补仓系数 double_down_factor**:马丁格尔增速,防御状态调低(0.74 → 0.62 → 0.55)。")
L.append("- **止盈距离**:强趋势 ×1.45 让利润奔跑;熊市/极端 ×0.85/0.80 快速止盈离场。")
L.append("- **追踪模式**:仅强趋势启用(retracement_base_pct > 0),先突破后回踩确认,顺趋势接回调;")
L.append("  其余状态保持网格(与基准配置及 scenarios 中 pure_grid 一致)。")
L.append("- **波动率 EMA 跨度**:熊市/极端缩短(更快反应),低波动拉长(滤噪)。")
L.append("- **风险敞口**:we_excess_allowance(借槽位额度)防御状态下调;entry_cooldown 熊市 5 分钟、极端 15 分钟,")
L.append("  崩盘中暂停连续补仓。")
L.append("- **解套**:防御状态提前触发(threshold ↓、ema_dist 更负)、单次量加大、亏损预算收紧。")
L.append("- **选币**:熊市/极端加入 0.25 的 ema_readiness 权重(优先选已靠近入场带、不再追高动量的币),")
L.append("  并缩短波动率 EMA 跨度。")
L.append("")

L.append("## 3. 每币状态占比与代表窗口(2021-01 ~ 2026-10)")
L.append("")
L.append("| 币种 | 正常震荡 | 低波动震荡 | 强趋势 | 熊市下跌 | 极端波动 |")
L.append("|---|---|---|---|---|---|")
for c in COINS:
    shares = [f'{float(stats_rows[(c, r)]["share_pct"]):.0f}%' for r in REGIMES]
    L.append(f"| {c} | " + " | ".join(shares) + " |")
L.append("")
L.append("代表窗口(每币每状态最长的连续区间,用于单状态回测检验):")
L.append("")
for c in COINS:
    parts = []
    for r in REGIMES:
        ws = windows.get(c, {}).get(r)
        if ws:
            parts.append(f"{CN[r]} {ws[0][0]}~{ws[0][1]}({ws[0][2]}天)")
    L.append(f"- **{c}**:" + ";".join(parts))
L.append("")

# per-coin tables
def gv(coin, regime, path):
    node = data[coin][regime]
    for k in path.split("."):
        node = node[k]
    return node

def fmt_val(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return f"{v:g}"
    return str(v)

ROW_DEFS = [
    ("forager.score_weights.volatility", "选币波动率权重"),
    ("forager.score_weights.ema_readiness", "选币 EMA 就绪权重"),
    ("forager.volatility_ema_span_1m", "选币波动率 EMA 跨度(分)"),
    ("risk.entry_cooldown_minutes", "加仓冷却(分)"),
    ("risk.we_excess_allowance_pct", "单仓超额额度"),
    ("strategy.trailing_martingale.volatility_ema_span_1h", "波动 EMA 1h 跨度(时)"),
    ("strategy.trailing_martingale.volatility_ema_span_1m", "波动 EMA 1m 跨度(分)"),
    ("strategy.trailing_martingale.entry.ema_span_0", "入场 EMA 跨度 0(分)"),
    ("strategy.trailing_martingale.entry.ema_span_1", "入场 EMA 跨度 1(分)"),
    ("strategy.trailing_martingale.entry.initial_ema_dist", "首入距 EMA 带"),
    ("strategy.trailing_martingale.entry.initial_qty_pct", "首次入场占 WEL"),
    ("strategy.trailing_martingale.entry.double_down_factor", "补仓系数"),
    ("strategy.trailing_martingale.entry.threshold_base_pct", "补仓基准距离"),
    ("strategy.trailing_martingale.entry.threshold_we_weight", "补仓暴露权重"),
    ("strategy.trailing_martingale.entry.threshold_volatility_1h_weight", "补仓 1h 波动权重"),
    ("strategy.trailing_martingale.entry.retracement_base_pct", "补仓回踩确认"),
    ("strategy.trailing_martingale.close.threshold_base_pct", "止盈基准距离"),
    ("strategy.trailing_martingale.close.threshold_we_weight", "止盈暴露权重"),
    ("strategy.trailing_martingale.close.threshold_volatility_1h_weight", "止盈 1h 波动权重"),
    ("strategy.trailing_martingale.close.retracement_base_pct", "止盈回踩确认"),
    ("strategy.trailing_martingale.close.qty_pct", "递归止盈每片"),
    ("unstuck.threshold", "解套触发阈值"),
    ("unstuck.ema_dist", "解套 EMA 偏移"),
    ("unstuck.close_pct", "解套单次平仓占 WEL"),
    ("unstuck.loss_allowance_pct", "解套亏损预算"),
]

for coin in COINS:
    L.append(f"## 4.{COINS.index(coin) + 1} {coin}")
    L.append("")
    L.append("| 参数 | " + " | ".join(CN[r] for r in REGIMES) + " |")
    L.append("|---|" + "---|" * 5)
    for path, label in ROW_DEFS:
        vals = [fmt_val(gv(coin, r, path)) for r in REGIMES]
        L.append(f"| {label} | " + " | ".join(vals) + " |")
    L.append("")
    L.append(f"固定不变项(全部状态):n_positions=4,TWEL=1,总/单仓暴露执行器 0.99,"
             f"选币 volume_drop_pct=0.884、volume_ema_span_1m=1660,"
             f"unstuck.ema_span=770/210,close.qty_pct=0.1。")
    L.append("")

L.append("## 5. 用法")
L.append("")
L.append("```json")
L.append('"coin_overrides": {')
L.append('    "SOL": { "bot": { "long": <本文件 4.4 表中对应状态的整列参数> } },')
L.append('    ...')
L.append('}')
L.append("```")
L.append("")
L.append("- 把对应币当前所处状态的整列参数放进 `coin_overrides.<coin>.bot.long`,其余 bot 参数沿用基准配置;")
L.append("  或者手动把整套 `bot.long` 换成对应状态的参数(临时切换用 `forced_mode_long` 更直接)。")
L.append("- 实时判断当前状态:用 `analyze_regimes.py` 中同样的指标(日实现波动率分位、30 日收益、EMA90 位置)")
L.append("  对最近 30~90 天滚动计算即可;图表 `charts/regimes_<COIN>.png` 可对照历史。")
L.append("- 数值可能超出基准配置的 optimize.bounds 搜索范围(基准对所有币共用一套边界);")
L.append("  若要按币优化,请把 bounds 放宽到本文件数值附近。")
L.append("")

(OUT / "params_annotated.md").write_text("\n".join(L), encoding="utf-8")
print("written params/params_annotated.md")
