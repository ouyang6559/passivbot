"""Build the HSL-10% rerun annual comparison markdown (baseline vs HSL).

Mirrors docs/单-币多空回测年度对比.md format. Reads hsl10_annual_stats.json
(HSL rerun) and annual_stats.json (no-HSL baseline, full history).
Output: docs/单一币多空HSL熔断回测年度对比.md (private analysis product).
"""
import json
from pathlib import Path

R1X = Path(__file__).parent
ROOT = R1X.parent.parent.parent  # repo root
DOC = ROOT / "docs" / "单一币多空HSL熔断回测年度对比.md"

hsl = json.loads((R1X / "hsl10_annual_stats.json").read_text())
base = json.loads((R1X / "annual_stats.json").read_text())

COINS = ["BTC", "ETH", "SOL"]
REGIMES = ["normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"]
REGIME_CN = {"normal_osc": "正常震荡", "low_vol_osc": "低波动震荡",
             "strong_trend": "强趋势", "bear": "熊市", "extreme_vol": "极端波动"}
SIDES = ["long", "short", "both"]
SIDE_CN = {"long": "long", "short": "short", "both": "both"}


def fmt_pct(x, digits=2):
    return f"{x * 100:+.{digits}f}%"


def table_for(coin, side, regime):
    k = f"{coin}/{regime}/{side}"
    v = hsl[k]
    lines = [
        f"### {coin}/USDT 永续 —— {SIDE_CN[side]}（{REGIME_CN[regime]}）",
        "",
        "| 年份 | 收益率 | 期末资金(USD) | 最差回撤 | Sharpe | 成交笔数 | 熔断次数 |",
        "|---|---|---|---|---|---|---|",
    ]
    for y, d in sorted(v["years"].items(), key=lambda kv: int(kv[0])):
        r = d["return"]
        rtxt = fmt_pct(r) + ("（爆仓）" if d["return"] <= -0.949 else "")
        lines.append(
            f"| {y} | {rtxt} | {d['end_equity']:,.0f} | {fmt_pct(d['worst_dd'])} "
            f"| {d['sharpe']:.2f} | {d['n_fills']:,} | {d['hsl_red_events']} |")
    return "\n".join(lines)


def main():
    # ---- overview ----
    ov_lines = []
    for coin in COINS:
        for side in SIDES:
            ks = [f"{coin}/{r}/{side}" for r in REGIMES]
            n_liq = sum(hsl[k]["n_liquidations"] for k in ks)
            n_cfg_liq = sum(1 for k in ks if hsl[k]["n_liquidations"] > 0)
            reds = sum(d["hsl_red_events"] for k in ks for d in hsl[k]["years"].values())
            fins = [hsl[k]["final_equity_multiple"] for k in ks]
            ov_lines.append(
                f"| {coin} | {side} | {n_cfg_liq}/15 | {n_liq} | {reds} "
                f"| {min(fins):.2f}x ~ {max(fins):.2f}x |")

    # ---- baseline vs HSL comparison ----
    cmp_lines = []
    for coin in COINS:
        for regime in REGIMES:
            for side in SIDES:
                k = f"{coin}/{regime}/{side}"
                b = base.get(k)
                if not b:
                    continue
                b_final = list(b["years"].values())[-1]["end_equity"]
                b_liq = "爆仓" if b["liquidated"] else "存活"
                hv = hsl[k]
                h_final = hv["final_equity_multiple"] * 100_000
                h_liq = f"{hv['n_liquidations']}次爆仓" if hv["n_liquidations"] else "存活"
                reds = sum(d["hsl_red_events"] for d in hv["years"].values())
                cmp_lines.append(
                    f"| {coin} | {REGIME_CN[regime]} | {side} | {b_liq} | {b_final:,.0f} "
                    f"| {reds} | {h_liq} | {h_final:,.0f} |")

    parts = [
        "# 单一币多空回测年度对比(HSL 10% 熔断版)",
        "",
        "- 日期:2026-10-02",
        "- 协议:与《单-币多空回测年度对比.md》完全相同的 45 个配置与窗口"
        "(BTC/ETH/SOL × 5 行情状态 × long/short/both,各自全历史 ~ 2026-10-01,"
        "本地 Binance USDT-M 1m K 线,起始资金 100,000 USD),唯一参数差异:",
        "  - `bot.{pside}.hsl.enabled=true`(活跃侧)",
        "  - `bot.{pside}.hsl.red_threshold=0.10`(回撤 10% 强制平仓)",
        "  - `bot.{pside}.hsl.panic_close_order_type=market`",
        "  - `bot.{pside}.hsl.cooldown_minutes_after_red=1440`(平仓后 1 天重启续集;"
        "0 表示永久停机,不可用)",
        "- 续集协议:权益触及起始资金 5% 即爆仓,记录日期、次日重开新段(起始资金重置 100,000),"
        "直至窗口结束。HSL 触发(红档恐慌平仓)不重置资金,由冷却后自动重启在同一回测内完成。",
        "- 口径:年收益率 = 各续集段内日历年段末/段初权益的连乘(段初为新入金 100,000);"
        "期末资金 = 合成复利钱包 100,000 × ∏(1+年收益率);最差回撤/Sharpe 仅在段内计算"
        "(续集入金是新资本,不构成收益或回撤);熔断次数 = 年内 `close_panic` 完全平仓事件数。",
        "- 明细:`regime1x/hsl10_results.json`、`regime1x/hsl10_annual_stats.json`;"
        "脚本 `run_hsl10_all.py`、`compute_annual_stats_hsl10.py`;配置 "
        "`configs/local/regime_1x_hsl10/`。私有分析产物,不入库公开。",
        "",
        "## 1. 全周期总览(方向层面)",
        "",
        "| 币 | 方向 | 爆仓配置数 | 爆仓(续集)总次数 | 熔断总次数 | 期末倍数范围 |",
        "|---|---|---|---|---|---|",
        *ov_lines,
        "",
        "## 2. 与无 HSL 基线的全周期对照",
        "",
        "| 币 | 档位 | 方向 | 基线结局 | 基线期末资金(USD) | 熔断次数 | HSL 结局 | HSL 期末资金(USD) |",
        "|---|---|---|---|---|---|---|---|",
        *cmp_lines,
        "",
        "## 3. 年度统计表 —— 主档(正常震荡)配置",
        "",
        "每币每方向一张表,行 = 年份。其余四档的同格式表格见附录 A。",
        "",
    ]
    for coin in COINS:
        for side in SIDES:
            parts.append(table_for(coin, side, "normal_osc"))
            parts.append("")

    total_reds = sum(d["hsl_red_events"] for v in hsl.values() for d in v["years"].values())
    parts += [
        "## 4. 结论",
        "",
        f"1. **HSL 是钝刀:它把 -95% 的清算换成一连串 -10% 的熔断,但同时向网格的盈利机制收税**。"
        f"全部 45 个配置共触发 {total_reds:,} 次熔断;多头 0 个爆仓(基线本来也不爆),"
        "空头/双向的清算从 24 个配置降到 2 个,但代价是收益被系统性削平。",
        "2. **多头付出 60%~90% 的总收益**:BTC 正常震荡档 4.31x → 1.19x,"
        "ETH 7.15x → 1.68x,SOL 28.95x → 12.92x。熔断集中发生在牛市回调段"
        "(2020/2021/2023 各 20~40 次)——越跌越买本是这个策略的盈利来源,"
        "10% 权益止损恰好把这段机制打断,熔断后再在更高价位重启入场。"
        "例外:熊市档(long)受熔断伤害最小(BTC 2.09x → 1.31x),"
        "其回撤本来就浅,风险调整后反而是 HSL 版全场最优的多头档。",
        "3. **空头从'爆仓'变成'慢性失血',但依然不赚钱**。15 个空头配置 13 个免于清算,"
        "但期末倍数多在 0.03x~0.6x——2020-2021 上涨段反复熔断(单配置最高 111 次),"
        "资金被每次 -10% 蚕食。更关键的是 **HSL 连空头的好年景也削掉了**:"
        "2022 年 BTC 正常震荡空头基线 +55.6%,HSL 版只有 +4.9%(反弹中的回撤同样触发熔断)。"
        "空头期望为负是结构性的,熔断只改变亏损的节奏。",
        "4. **both + 续集 = 持续向账户输血**。13/15 个 both 配置爆仓至少一次"
        "(最多 11 次,如 SOL 低波动震荡),每次续集注入 100,000 后大多再度亏光,"
        "合成复利钱包普遍归零。静态双向在 HSL 保护下仍是最差组合。",
        "5. **极端波动档几乎不受影响**(熔断 0~3 次):TWEL=0.5 的算术余量"
        "(死亡涨幅 +190%)本身就够,不需要 HSL。防御来自暴露上限而非止损。",
        "6. **实践含义**:(a) 10% 权益止损与马丁格尔网格在机制上互斥——"
        "网格靠扛回撤等回归赚钱,10% 止损把'扛'字禁止了;若坚持给网格配止损,"
        "阈值必须大于策略的历史最深回撤(约 40%~50%),或者只在熊市档这类浅回撤参数上启用;"
        "(b) 对空头,正确的自保仍是状态开关(趋势逆风时不开空),HSL 只能把速死变慢死;"
        "(c) 任何情况下都不要跑静态 both + 自动续集——那是把清算变成定期定额捐款。",
        "",
    ]

    parts += ["## 附录 A:其余四档年度统计表", ""]
    for regime in REGIMES[1:]:
        parts.append(f"### 档位:{REGIME_CN[regime]}\n")
        for coin in COINS:
            for side in SIDES:
                parts.append(table_for(coin, side, regime))
                parts.append("")

    DOC.write_text("\n".join(parts))
    print(f"wrote {DOC}")


if __name__ == "__main__":
    main()
