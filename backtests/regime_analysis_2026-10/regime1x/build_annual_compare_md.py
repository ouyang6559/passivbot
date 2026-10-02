"""Build the single-coin long/short annual-comparison markdown in the
per-symbol yearly-stats table format (年份/收益率/期末资金/最差回撤/Sharpe/成交笔数)."""
import json
from pathlib import Path

import pandas as pd

R1X = Path(__file__).parent
DOCS = Path("docs/单一币多空回测年度对比.md")
annual = json.loads((R1X / "annual_stats.json").read_text())
summary = pd.read_csv(R1X / "summary.csv")
COINS = ["BTC", "ETH", "SOL"]
REGIMES = ["normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"]
SIDES = ["long", "short", "both"]
YEARS = [str(y) for y in range(2019, 2027)]
CN_REGIME = {
    "normal_osc": "正常震荡", "low_vol_osc": "低波动震荡",
    "strong_trend": "强趋势", "bear": "熊市", "extreme_vol": "极端波动",
}


def table(rows_key: str) -> list[str]:
    d = annual[rows_key]
    out = ["| 年份 | 收益率 | 期末资金(USD) | 最差回撤 | Sharpe | 成交笔数 |",
           "|---|---|---|---|---|---|"]
    for y in YEARS:
        rec = d["years"].get(y)
        if rec is None:
            continue
        ret = f"{rec['return']:+.2%}"
        if rec["end_equity"] <= 5500:  # termination level = 5% of 100k
            ret += "(清算)"
        out.append(
            f"| {y} | {ret} | {rec['end_equity']:,.0f} | {rec['worst_dd']:.2%} "
            f"| {rec['sharpe']:.2f} | {rec['n_fills']:,} |"
        )
    if d["liquidated"]:
        liq_year = next(y for y, rec in d["years"].items() if rec["end_equity"] <= 5500)
        out.append(f"\n> {liq_year} 年权益触及起始资金 5%,回测提前终止。")
    return out


lines = []
lines.append("# 单一币多空回测年度统计\n")
lines.append("- 日期:2026-10-02")
lines.append("- 数据:regime_1x 网格 45 个单币全历史回测(BTC / ETH / SOL × 5 行情状态 × "
             "long / short / both,2019/2020 起 ~ 2026-10-01,本地 Binance USDT-M 1m K 线,起始资金 100,000 USD)。")
lines.append("- 口径:逐小时 `usd_total_equity` 按日历年切片。收益率 = 年末/年初权益 - 1;"
             "期末资金 = 年末权益;最差回撤 = 年内权益相对年内高点的最大回撤;"
             "Sharpe = 小时收益率的年化夏普(√(24×365));成交笔数 = 年内 fills 数。")
lines.append("- 明细:`backtests/regime_analysis_2026-10/regime1x/annual_stats.json`"
             "(生成脚本 `compute_annual_stats.py`、`build_annual_compare_md.py`);"
             "全周期指标见同目录 `summary.csv`。")
lines.append("- 性质:私有分析产物,不入库公开。\n")

lines.append("## 1. 全周期总览(方向层面)\n")
lines.append("| 币 | 方向 | 完成/清算 | 日均收益(进攻四档均值 / 极端档) | 最差回撤范围 |")
lines.append("|---|---|---|---|---|")
for coin in COINS:
    for side in SIDES:
        sub = summary[(summary.coin == coin) & (summary.side == side)]
        done = int((sub.completion_ratio >= 0.999).sum())
        liq = int(sub.liquidated.sum())
        act = sub[sub.regime != "extreme_vol"]
        ext = sub[sub.regime == "extreme_vol"]
        lines.append(
            f"| {coin} | {side} | {done}/清算 {liq} "
            f"| {act.adg_pnl.mean():+.3%} / {ext.adg_pnl.mean():+.3%} "
            f"| {sub.dd_worst_usd.min():.2f} ~ {sub.dd_worst_usd.max():.2f} |"
        )
lines.append("")

lines.append("## 2. 年度统计表 —— 主档(正常震荡)配置\n")
lines.append("每币每方向一张表,行 = 年份。其余四档的同格式表格见附录 A。\n")
for coin in COINS:
    for side in SIDES:
        lines.append(f"### {coin}/USDT 永续 —— {side}\n")
        lines += table(f"{coin}/normal_osc/{side}")
        lines.append("")

lines.append("## 3. 年度对比结论\n")
lines.append("""
1. **多头收益高度集中,近年失效**。全部收益来自 2020-2021 与 2023-2024 两段牛市;
   2025-2026 三币全部转平或转负(ETH 2025、2026 连续两年亏损)。
2. **2022 压力年:熊市档最抗跌的进攻档,极端波动档唯一正收益**(见附录 A 各币 bear/extreme_vol 表);
   熊市档比其它档少亏 20~40 个百分点,但牛市收益只有其它档的 1/5~1/3 ——
   档位切换的价值就来自这个差值。
3. **空头/双向全部死于第一次大逆风**:BTC/ETH 死于 2020,SOL 死于 2021(年度 -94%~-97%),
   熊市档也不例外。both 与 short 在全部 15 组对照中死于同一年:多头盈利填不上空头亏损。
4. **极端波动档是唯一普遍存活的配置**(SOL 空头/双向除外),但年度收益趋近于零;
   ETH 空头 2026 年 -7.5% 为其首次显著亏损(持续阴跌+高波动,解套被反复触发)。
5. **SOL 震荡档 2022 年 -93% 幸存**,距清算一步,验证了降 initial_qty_pct、
   提早解套的修正方向(见《针对性配置文件调参数.md》)。
6. **对配置实践的含义**:方向暴露(尤其空头)必须由状态/漂移开关控制;
   熊市档参数作为熊市年的切换目标而非全年配置;静态多空同开不可行。
""")

lines.append("## 附录 A:其余四档年度统计表\n")
for coin in COINS:
    for side in SIDES:
        for regime in REGIMES:
            if regime == "normal_osc":
                continue
            lines.append(f"### {coin}/USDT 永续 —— {side}({CN_REGIME[regime]})\n")
            lines += table(f"{coin}/{regime}/{side}")
            lines.append("")

DOCS.write_text("\n".join(lines), encoding="utf-8")
print(f"written {DOCS} ({len(lines)} lines)")
