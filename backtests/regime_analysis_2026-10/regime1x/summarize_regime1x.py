"""Summarize regime1x full-history backtest results into CSV + markdown tables."""
import json
from pathlib import Path

import pandas as pd

R1X = Path(__file__).parent
results = json.loads((R1X / "results.json").read_text())
COINS = ["BTC", "ETH", "SOL"]
REGIMES = ["normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"]
SIDES = ["long", "short", "both"]

rows = []
for key, v in sorted(results.items()):
    if not v.get("analysis_metrics_done"):
        continue
    coin, regime, side = key.split("/")
    side = side.removesuffix(".json")
    try:
        fills = json.loads((Path(v["run_dir"]) / "analysis.json").read_text()).get("fills_count")
    except Exception:  # noqa: BLE001 - fills are informational
        fills = v.get("n_fills")
    rows.append({
        "coin": coin, "regime": regime, "side": side,
        "adg_pnl": v.get("adg_pnl"), "mdg_pnl": v.get("mdg_pnl"),
        "dd_worst_usd": v.get("drawdown_worst_usd"),
        "loss_profit_ratio": v.get("loss_profit_ratio"),
        "peak_recovery_hours": v.get("peak_recovery_hours_pnl"),
        "position_held_hours_max": v.get("position_held_hours_max"),
        "completion_ratio": round(v.get("backtest_completion_ratio") or 0.0, 4),
        "liquidated": v.get("liquidated"),
        "n_fills": fills,
        "run_dir": v.get("run_dir"),
    })
df = pd.DataFrame(rows)
df.to_csv(R1X / "summary.csv", index=False)

CN = {
    "normal_osc": "正常震荡", "low_vol_osc": "低波动震荡",
    "strong_trend": "强趋势", "bear": "熊市", "extreme_vol": "极端波动",
}
lines = []
for coin in COINS:
    lines.append(f"### {coin}\n")
    header = "| 状态 | 方向 | 日均收益 | 最差回撤 | 亏损/盈利比 | 完成率 | 爆仓 | 成交笔数 |"
    lines += [header, "|---|---|---|---|---|---|---|---|"]
    for regime in REGIMES:
        for side in SIDES:
            r = df[(df.coin == coin) & (df.regime == regime) & (df.side == side)]
            if r.empty:
                continue
            r = r.iloc[0]
            lines.append(
                f"| {CN[regime]} | {side} | {r.adg_pnl:.4f} | {r.dd_worst_usd:.3f} "
                f"| {r.loss_profit_ratio:.3f} | {r.completion_ratio:.2f} "
                f"| {'是' if r.liquidated else '否'} | {int(r.n_fills or 0):,} |"
            )
    lines.append("")

(R1X / "summary_tables.md").write_text("\n".join(lines), encoding="utf-8")
print(f"summary.csv rows={len(df)}, tables written to summary_tables.md")
print(df.groupby(["side"]).agg(
    n=("coin", "size"), liq=("liquidated", "sum"),
    adg=("adg_pnl", "mean"), dd=("dd_worst_usd", "mean"),
).round(4).to_string())
