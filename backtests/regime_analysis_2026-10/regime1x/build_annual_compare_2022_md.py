"""Build the 2022-based annual-stats markdown for all 45 regime_1x runs.

Window: 2022-01-01 -> 2026-10-01. Computes per-calendar-year return / ending
equity / worst drawdown / annualized Sharpe / fill count from each run's
equity curve and fills, writes annual_stats_2022.json plus the doc.
"""
import json
from pathlib import Path

import pandas as pd

R1X = Path(__file__).parent
DOCS = Path("docs/单一币多空回测年度统计_2022起.md")
results = json.loads((R1X / "results_2022_sb.json").read_text())
COINS = ["BTC", "ETH", "SOL"]
REGIMES = ["normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"]
SIDES = ["long", "short", "both"]
YEARS = [str(y) for y in range(2022, 2027)]
CN_REGIME = {
    "normal_osc": "正常震荡", "low_vol_osc": "低波动震荡",
    "strong_trend": "强趋势", "bear": "熊市", "extreme_vol": "极端波动",
}

annual = {}
for key, v in sorted(results.items()):
    if not v.get("analysis_metrics_done"):
        continue
    coin, regime, side = key.split("/")
    side = side.removesuffix(".json")
    eq_df = pd.read_csv(Path(v["run_dir"]) / "balance_and_equity.csv.gz")
    eq_df["dt"] = pd.to_datetime(eq_df["Unnamed: 0"])
    eq = eq_df.set_index("dt")["usd_total_equity"]
    ret_h = eq.pct_change().clip(-0.5, 0.5)
    fills = pd.read_csv(Path(v["run_dir"]) / "fills.csv", parse_dates=["timestamp"])
    fill_years = fills["timestamp"].dt.year.value_counts().to_dict()
    years = {}
    for year, seg in eq.groupby(eq.index.year):
        dd = (seg / seg.cummax() - 1.0).min()
        r = ret_h.loc[seg.index]
        sharpe = float(r.mean() / r.std() * (24 * 365) ** 0.5) if r.std() > 0 else 0.0
        years[str(int(year))] = {
            "return": round(seg.iloc[-1] / seg.iloc[0] - 1.0, 4),
            "worst_dd": round(dd, 4),
            "end_equity": round(float(seg.iloc[-1]), 0),
            "sharpe": round(sharpe, 2),
            "n_fills": int(fill_years.get(year, 0)),
        }
    annual[f"{coin}/{regime}/{side}"] = {
        "liquidated": bool(v.get("liquidated")),
        "adg_pnl": v.get("adg_pnl"),
        "drawdown_worst_usd": v.get("drawdown_worst_usd"),
        "years": years,
    }
(R1X / "annual_stats_2022.json").write_text(json.dumps(annual, indent=2))


def table(key: str) -> list[str]:
    d = annual[key]
    out = ["| 年份 | 年收益率 | 期末资金(USD) | 最差回撤 | Sharpe | 成交笔数 |",
           "|---|---|---|---|---|---|"]
    for y in YEARS:
        rec = d["years"].get(y)
        if rec is None:
            out.append(f"| {y} | — (已终止) | — | — | — | — |")
            continue
        ret = f"{rec['return']:+.2%}"
        if rec["end_equity"] <= 5500:
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
lines.append("# 单一币多空回测年度统计(2022-01-01 起)\n")
lines.append("- 日期:2026-10-02")
lines.append("- 数据:regime_1x 网格全部 45 个单币回测(BTC / ETH / SOL × 5 行情状态 × "
             "long / short / both),窗口统一为 **2022-01-01 ~ 2026-10-01**,起始资金 100,000 USD,"
             "本地 Binance USDT-M 1m K 线。目的:剔除 2020-2021 极端牛熊后再比较多空。")
lines.append("- 口径:**年收益率 = 日历年年末权益 / 年初权益 - 1**(每年都是完整自然年,2026 至 10-01);"
             "期末资金 = 年末权益(含浮动盈亏);最差回撤 = 年内权益对年内高点的最大回撤;"
             "Sharpe = 小时收益率年化(√(24×365));成交笔数 = 年内 fills 数。"
             "2022 年的年初权益即回测起始权益,因此全年 5 行连乘 ≈ 全窗口总倍数。")
lines.append("- 明细:`regime1x/annual_stats_2022.json`;回测结果 `regime1x/results_2022_sb.json`;"
             "脚本 `run_2022_short_both.py`、本文件生成脚本 `build_annual_compare_2022_md.py`。")
lines.append("- 性质:私有分析产物,不入库公开。\n")

lines.append("## 1. 全周期总览(2022-01-01 ~ 2026-10-01)\n")
lines.append("| 币 | 方向 | 完成/清算 | 日均收益(进攻四档均值 / 极端档) | 最差回撤范围 |")
lines.append("|---|---|---|---|---|")
for coin in COINS:
    for side in SIDES:
        keys = [f"{coin}/{r}/{side}" for r in REGIMES]
        subs = [annual[k] for k in keys]
        done = sum(1 for s in subs if not s["liquidated"])
        liq = len(subs) - done
        act = [s["adg_pnl"] for s, k in zip(subs, keys) if "extreme_vol" not in k]
        ext = [s["adg_pnl"] for s, k in zip(subs, keys) if "extreme_vol" in k]
        dds = [s["drawdown_worst_usd"] for s in subs]
        lines.append(
            f"| {coin} | {side} | {done}/清算 {liq} "
            f"| {sum(act)/len(act):+.3%} / {sum(ext)/len(ext):+.3%} "
            f"| {min(dds):.2f} ~ {max(dds):.2f} |"
        )
lines.append("")

lines.append("## 2. 年度统计表 —— 主档(正常震荡)配置\n")
lines.append("每币每方向一张表,行 = 年份,收益率单位为年。其余四档见附录 A。\n")
for coin in COINS:
    for side in SIDES:
        lines.append(f"### {coin}/USDT 永续 —— {side}\n")
        lines += table(f"{coin}/normal_osc/{side}")
        lines.append("")

lines.append("## 3. 结论(2022 窗口)\n")
lines.append("""
1. **多头 15/15 全部存活**,但 2022 年付出重大代价:BTC 震荡档 -59%~-64%、
   SOL 震荡档约 -83%~-93%(年内回撤 -94%)。2023 年全部强力修复,2025-2026 转平/负。
2. **空头/双向 24/30 清算**,全部死在上升年:2022 熊市年空头全部盈利
   (SOL 空头 +180%~+336%),2023 年牛市清算大多数(SOL -98%~-99%),其余 2024 年死亡。
   起点挪到 2022 只改变死亡年份,不改变结局——清算根因是趋势逆风下的
   暴露上限机制,不是 2021 极端行情。
3. **极端波动档是唯一全方向存活的配置**(TWEL=0.5),但年收益率趋近 0(±5% 内);
   ETH 强趋势 both 是唯一存活的非防御配置(靠 2023 +81% 修复)。
4. 全窗口正年收益率且每年为正的组合不存在:多头在 2022 巨亏,空头在 2023 巨亏,
   防御档存活但无收益。**年度正收益的稳定性只能来自状态切换(熊市档/多头档轮动),
   而不是任何单一静态参数集。**
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
print(f"written {DOCS} ({len(lines)} lines), annual_stats_2022.json: {len(annual)} runs")
