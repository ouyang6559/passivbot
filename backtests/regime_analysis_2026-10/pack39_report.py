"""Build the pack39 annual-comparison markdown report from annual_stats.json.

Mirrors the format of the earlier 单一币多空回测年度统计 docs: per (coin, mode)
yearly return / end equity / worst drawdown / Sharpe / fills, plus a compact
overview table. Writes pack39/REPORT.md.
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent
stats = json.loads((ROOT / "pack39" / "annual_stats.json").read_text())
results = json.loads((ROOT / "pack39" / "results.json").read_text())

COINS = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "LINK", "DOT", "UNI", "LTC", "XMR"]
MODES = ["long", "short", "both"]
YEARS = ["2022", "2023", "2024", "2025", "2026"]
MODE_LABEL = {"long": "LONG", "short": "SHORT", "both": "LONG+SHORT"}


def pct(v: float | None, digits: int = 2) -> str:
    return "—" if v is None else f"{v * 100:+.{digits}f}%"


def build() -> str:
    lines = []
    lines.append("# Passivbot 13币 × 39套研究包参数 —— 2022 起年度回测")
    lines.append("")
    lines.append("- 日期: 2026-10-02")
    lines.append("- 参数来源: `docs/Passivbot_13币_多空_39套参数_回测研究包(chatgpt).md`,13 币 × long / short / both 共 39 套 profile,逐套单币回测。")
    lines.append("- 窗口: 2022-01-01 ~ 2026-10-02,起始资金 100,000 USD,n_positions=1,leverage=1x,strategy=trailing_martingale,entry EMA gate=all,纯限价(maker)成交。")
    lines.append("- 执行假设: 按研究包统一约束 maker 费率 = 0、滑点 = 0(敏感性更强场景需另行加费率复测)。数据: 本地 Binance USDT-M 1m K线(2021-09-01 起预热)。")
    lines.append("- 口径: 年收益率 = 日历年年末权益/年初权益 - 1;最差回撤 = 年内权益对年内高点的最大回撤;Sharpe = 小时收益率年化(√(24×365));成交笔数 = 年内 fills 数。清算 = 权益触及起始资金 5%,回测提前终止。")
    lines.append("- 明细: `pack39/annual_stats.json`(逐小时权益切片),回测结果目录见 `pack39/results.json`;脚本 `pack39_generate_configs.py`、`pack39_run.py`、`pack39_annual_stats.py`、`pack39_report.py`。")
    lines.append("- 性质: 私有分析产物,不入库公开。")
    lines.append("")
    # overview
    lines.append("## 1. 总览(全窗口 2022-01-01 ~ 2026-10-02)")
    lines.append("")
    lines.append("| 币 | 模式 | 总倍数 | 2022 | 2023 | 2024 | 2025 | 2026* | 清算 |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---|")
    for coin in COINS:
        for mode in MODES:
            k = f"{coin}/{mode}"
            d = stats.get(k)
            if d is None:
                lines.append(f"| {coin} | {MODE_LABEL[mode]} | — | — | — | — | — | — | 未完成 |")
                continue
            ys = d["years"]
            cells = []
            for y in YEARS:
                if y in ys:
                    r = ys[y]["return"]
                    mark = "清算" if r <= -0.95 else pct(r, 1)
                else:
                    mark = "—"
                cells.append(mark)
            lines.append(
                f"| {coin} | {MODE_LABEL[mode]} | {d['total_return_mult']:.3f} | "
                + " | ".join(cells)
                + f" | {'是' if d['liquidated'] else '否'} |"
            )
    lines.append("")
    lines.append("\\* 2026 年截至 10-02。清算指该 profile 在窗口内权益触及起始资金 5%(总倍数 0.05)。")
    lines.append("")
    # per coin detail
    lines.append("## 2. 分币年度明细")
    lines.append("")
    for coin in COINS:
        lines.append(f"### {coin}/USDT 永续")
        lines.append("")
        any_detail = False
        for mode in MODES:
            k = f"{coin}/{mode}"
            d = stats.get(k)
            if d is None:
                lines.append(f"**{MODE_LABEL[mode]}**:未完成(数据或运行缺失)。")
                lines.append("")
                continue
            any_detail = True
            lines.append(f"**{MODE_LABEL[mode]}**(总倍数 {d['total_return_mult']:.3f},清算={'是' if d['liquidated'] else '否'},完成度 {d['completion'] if d['completion'] is not None else '—'})")
            lines.append("")
            lines.append("| 年份 | 年收益率 | 期末资金(USD) | 最差回撤 | Sharpe | 成交笔数 |")
            lines.append("|---|---:|---:|---:|---:|---:|")
            for y in YEARS:
                if y not in d["years"]:
                    lines.append(f"| {y} | — | — | — | — | — |")
                    continue
                yd = d["years"][y]
                r = yd["return"]
                ret = f"{r * 100:+.2f}%" + ("(清算)" if r <= -0.95 else "")
                lines.append(
                    f"| {y} | {ret} | {yd['end_equity']:,.0f} | {yd['worst_dd'] * 100:.2f}% "
                    f"| {yd['sharpe']:.2f} | {yd['n_fills']:,} |"
                )
            lines.append("")
        if not any_detail:
            lines.pop()  # remove trailing blank if nothing
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    report = build()
    (ROOT / "pack39" / "REPORT.md").write_text(report)
    n_done = sum(1 for c in COINS for m in MODES if f"{c}/{m}" in stats)
    print(f"REPORT.md written ({n_done}/39 profiles done)")
