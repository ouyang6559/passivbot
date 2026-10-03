

正常震荡、低波动震荡、强趋势、熊市下跌、极端波动

hsl.enabled=true  防止极端行情直接止损 


Tier 1：SSS级 — 综合最优
sol 多空
BTC多
ETH多
S级别：
avax、doge、uni、link多空
A：
bnb多、xrp、ltc两个多空

B：
ada多、dot小仓位、xmr门罗币（不推荐）


核心结论：从回测数据+流动性+社区实战三维交叉验证，
SOL是Passivbot马丁策略的绝对首选（波动大、深度好、回撤频繁），
其次是BTC/ETH作为安全底仓。
高波动四天王（SOL/DOGE/AVAX/UNI）适合追求收益，但必须严格控制TWEL。XMR不推荐。


xmr 10倍杠杆多空双向持仓   就是两核两g的服务器，一年109元   


# 一、ETH五场景最终参数与多空调配

| 场景 | 多头 TWEL | 空头 TWEL | 关键参数改动（相对 regime_1x v1） |
| --- | --- | --- | --- |
| 正常震荡 | 1.00 | 0 禁用 | 无改动（v1 即最优） |
| 低波动震荡 | 1.00 | 0.50 | 多头：初仓4.5→4.0%、间距1.37→1.50%、ddf 0.78→0.72、解套0.88→0.78/切片0.7→1.2%；空头：§6.3 的 v2 参数 |
| 强趋势 | 1.00 | 0 禁用 | 止盈 base 0.77→1.0%、解套 0.85→0.75 |
| 熊市下跌 | 0.70 | 1.00 | 无改动（实测 we_excess 改动逐笔无差异，回退） |
| 极端波动 | 0.52 | 0.50 | TWEL 0.5→0.52、初仓 0.93→0.98%（微升敞口提收益） |



# 二、最终 ETH 的参数调试区间
设计原则：只放开本轮 v2→v4 实测响应的旋钮，其余全部冻结（EMA 跨度、we 权重、forager、enforcer 等定义场景身份的参数用零宽度边界 [v,v] 锁死，防止优化器把“低波动档”优化成“另一个正常震荡档”）。放开的核心旋钮与倍率：

| 旋钮 | 区间规则（v=冻结值） | 旋钮 | 区间规则 |
| --- | --- | --- | --- |
| 初仓 initial_qty_pct | [0.8v, 1.2v] | 解套阈值 unstuck.threshold | [v-0.07, v+0.05]，限 [0.40, 0.90] |
| 入场间距 entry.threshold_base_pct | [0.8v, 1.25v] | 解套切片 unstuck.close_pct | [0.8v, 1.6v] |
| 加仓系数 ddf | [v-0.08, v+0.06] | TWEL | [v-0.10, v+0.10] |
| 止盈间距 close.threshold_base_pct | [0.7v, 1.4v] | we_excess | [0.6v, 1.5v] |
| 波动率权重(入/平) | [0.7v, 1.3v] | initial_ema_dist / unstuck.ema_dist | 两侧放宽（0.55v~1.7v） |


# 各参数在死亡中的角色
| 参数 | 角色 |
| --- | --- |
| TWEL | 唯一生死参数，决定能扛多大的上涨(+95%/+136%/+190% 三档) |
| 入场参数(iq/ddf/间距) | 只决定多久走到死和途中损耗：低波动档最密(4.5% 初始、1.37% 间距)→ 顶格最快、解套 2,947 次、途中失血最大，但结局与正常档相同 |
| 止盈参数 | 与死亡无关——价格越过半程后止盈在数学上不可达 |
| 解套参数 | 唯一降风险通道，但 loss_allowance_pct 把降风险速度锁在 ~1,300 USD/30 天，而需卸的敞口是 16.4 万且名义已膨胀到 30 万——需要 4~5 年卸完的仓位，市场只给 3 周；解套是小失血(占死因 5~40%),不是死因 |
| 暴露执行器 | 按成本价修剪，对市价名义膨胀完全失效；死亡时实际名义/余额 = 1.65~1.97,远超 TWEL 面值 |
| HSL | 全部配置 hsl.enabled=false ——唯一能救它的机制(权益 -20% 恐慌平仓)被关掉了，-20% 的熔断变成了 -95% 的清算 |



探针结果：两个冻结参数其实该放开（已回写 bounds）
以 normal_osc 全历史为基线（adg +0.250%/天、dd 0.671）：

| 探针 | 改动 | 结果 | 判定 |
| --- | --- | --- | --- |
| P6 首次入场距离 | -0.81%→-1.5% | adg +0.277%（+10.8%），dd 持平；成交密度 4.49→4.85 笔/天 | 强响应且为正 → bounds 下界已放宽到 2.2v |
| P5 入场 we 权重 | 0.135→0.30 | adg -6%，但亏损/盈利比改善 | 有响应 → 已放开窄幅 [0.7v, 1.5v] |
| P2 入场 EMA 跨度 ×0.7 | 770/210→540/147 | adg +1.2%，lpr 全场最好 | 低敏感，二轮可窄幅 [0.85v, 1.15v] |
| P1 入场 EMA 跨度 ×1.3 | 770/210→1000/273 | adg -1.6% | 冻结合理 |
| P3 止盈切片 qty_pct | 0.1→0.2 | adg -1.2% | 冻结合理 |
| P4 1m 波动率跨度 | 60→300 | 逐笔完全相同 | 它只在 volatility_1m_weight>0 时才生效——单独放开毫无意义，必须联动 |




```shell
# 每日跑一次（dry run）：判别 + 与上次生效状态对比
./venv/bin/python backtests/regime_analysis_2026-10/regime_switcher.py --coin ETH --history 21

# 确认切换后记录到 state 文件（regime_switcher_state.json）
./venv/bin/python backtests/regime_analysis_2026-10/regime_switcher.py --coin ETH --apply

# 自定义某状态用别的配置（比如未来优化好 ema_anchor 后）
... --map strong_trend=configs/local/eth_anchor_bt/ETH/strong_trend.json
```




```python
"""Regime switcher: classify the current market regime offline and map it to a
passivbot config.

This is the deployment-layer piece the regime analysis assumes (REPORT.md §2
note 4): passivbot itself runs ONE config and has no native regime switching.
The switcher

1. resamples local 1m klines (freqtrade feather) to 1h,
2. recomputes the exact daily regime rules from analyze_regimes.py with
   point-in-time thresholds (trailing `--ref-days` quantiles, no lookahead),
3. applies hysteresis (trailing `--hyst` days, extreme_vol overrides instantly),
4. maps the effective regime to a config file and diffs it against the last
   applied decision in the state file.

It NEVER touches processes or the network: applying a switch means restarting
your bot process with the recommended config yourself (or via your supervisor;
`src/live/restart_executor.py` is the repo's local-only restart tool).  All
data access is local files; no exchange requests, no credentials.

Usage:
  ./venv/bin/python regime_switcher.py --coin ETH            # dry run
  ./venv/bin/python regime_switcher.py --coin ETH --apply    # record decision
  ./venv/bin/python regime_switcher.py --coin ETH --history 30
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

FT_DIR = Path("/Users/liu/Documents/go/gopath/src/rust-pro/freqtrade-wc/user_data/data/binance/futures")
CFG_MAP_DEFAULT = "configs/local/eth_final/ETH/{regime}.json"
STATE = Path(__file__).parent / "regime_switcher_state.json"


# ---------- data ----------
def load_1h(coin: str) -> pd.DataFrame:
    f = FT_DIR / f"{coin}_USDT_USDT-1m-futures.feather"
    if not f.exists():
        raise FileNotFoundError(f"no local 1m feather for {coin}: {f}")
    df = pd.read_feather(f)
    df = df.set_index("date").sort_index()
    h = pd.DataFrame({
        "open": df["open"].resample("1h").first(),
        "high": df["high"].resample("1h").max(),
        "low": df["low"].resample("1h").min(),
        "close": df["close"].resample("1h").last(),
        "volume": df["volume"].resample("1h").sum(),
    }).dropna(subset=["close"])
    return h


def daily_metrics(df: pd.DataFrame) -> pd.DataFrame:
    h1r = np.log(df["close"] / df["close"].shift(1))
    day = df.index.floor("D")
    g = h1r.groupby(day)
    d = pd.DataFrame({"rv_1d": g.std(ddof=1) * np.sqrt(24)})
    oc = df["close"].resample("1D").last()
    hi = df["high"].resample("1D").max()
    lo = df["low"].resample("1D").min()
    d = d.reindex(oc.index)
    d["close"] = oc
    d["ret_1d"] = np.log(oc / oc.shift(1))
    d["ema30"] = oc.ewm(span=30, adjust=False).mean()
    d["ema90"] = oc.ewm(span=90, adjust=False).mean()
    d["trend_14d"] = np.log(oc / oc.shift(14))
    d["trend_30d"] = np.log(oc / oc.shift(30))
    d["dd_90"] = oc / oc.rolling(90).max() - 1.0
    return d.dropna(subset=["rv_1d", "trend_30d"])


# ---------- classification (same rules as analyze_regimes.classify) ----------
def classify(d: pd.DataFrame, ref_days: int, min_periods: int = 180) -> pd.Series:
    # point-in-time thresholds: trailing quantiles, no lookahead
    def q(col, level):
        return d[col].rolling(f"{ref_days}D", min_periods=min_periods).quantile(level)

    rv98, ret98 = q("rv_1d", 0.98), d["ret_1d"].abs().rolling(
        f"{ref_days}D", min_periods=min_periods).quantile(0.98)
    t15, t85 = q("trend_30d", 0.15), q("trend_30d", 0.85)
    rv30, t14_40 = q("rv_1d", 0.30), d["trend_14d"].abs().rolling(
        f"{ref_days}D", min_periods=min_periods).quantile(0.40)

    extreme = (d["rv_1d"] >= rv98) | (d["ret_1d"].abs() >= ret98)
    bear = (d["close"] < d["ema90"]) & (d["trend_30d"] < 0) & \
           ((d["trend_30d"] <= np.minimum(t15, -0.08)) | (d["dd_90"] <= -0.20)) & ~extreme
    strong = (d["trend_30d"] >= np.maximum(t85, 0.08)) & (d["close"] >= d["ema90"]) & \
             ~extreme & ~bear
    lowvol = (d["rv_1d"] <= rv30) & (d["trend_14d"].abs() <= t14_40) & \
             ~extreme & ~bear & ~strong
    labels = pd.Series("normal_osc", index=d.index)
    for name, cond in (("low_vol_osc", lowvol), ("strong_trend", strong),
                       ("bear", bear), ("extreme_vol", extreme)):
        labels[cond.fillna(False)] = name
    return labels


# ---------- hysteresis ----------
def effective_regime(labels: pd.Series, hyst_days: int, prev: str | None):
    last = labels.iloc[-1]
    if last == "extreme_vol":  # burst state: switch immediately, both ways
        return "extreme_vol", "extreme_vol 命中,立即生效"
    recent = labels.iloc[-hyst_days:]
    recent = recent[recent != "extreme_vol"]  # bursts do not vote
    if len(recent) == 0:
        return prev or "normal_osc", "近端全为 extreme_vol 之后无数据"
    counts = recent.value_counts()
    cand, n = counts.index[0], counts.iloc[0]
    if n / max(len(recent), 1) >= 0.6 and recent.iloc[-1] == cand:
        if cand != prev:
            return cand, f"近{hyst_days}天内 {n}/{len(recent)} 天为 {cand},达到切换条件"
        return cand, "保持"
    return prev or "normal_osc", f"未达滞回条件(候选 {cand} {n}/{len(recent)} 天),保持 {prev or 'normal_osc'}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--coin", default="ETH")
    ap.add_argument("--feather-dir", default=str(FT_DIR))
    ap.add_argument("--ref-days", type=int, default=730,
                    help="分位阈值参考窗口(逐日滚动,无未来函数)")
    ap.add_argument("--hyst", type=int, default=7, help="非极端状态切换滞回天数")
    ap.add_argument("--history", type=int, default=0, help="打印最近 N 天逐日标签")
    ap.add_argument("--map", action="append", default=[],
                    help="regime=config路径,可多次;默认 configs/local/eth_final/ETH/<regime>.json")
    ap.add_argument("--apply", action="store_true",
                    help="把判定写入 state 文件(只写本地文件,不重启任何进程)")
    args = ap.parse_args()

    df = load_1h(args.coin)
    d = daily_metrics(df)
    labels = classify(d, args.ref_days)
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    prev = state.get(args.coin, {}).get("effective_regime")
    eff, why = effective_regime(labels, args.hyst, prev)

    cmap = dict((k, CFG_MAP_DEFAULT.format(regime=k)) for k in
                ("normal_osc", "low_vol_osc", "strong_trend", "bear", "extreme_vol"))
    for m in args.map:
        k, _, v = m.partition("=")
        cmap[k] = v
    cfg_path = cmap[eff]
    kind = "?"
    if Path(cfg_path).exists():
        kind = json.loads(Path(cfg_path).read_text()).get("live", {}).get("strategy_kind", "?")

    print(f"== {args.coin} 状态切换器(离线判别,数据至 {d.index[-1].date()})")
    print(f"当前逐日标签: {labels.iloc[-1]} | 生效状态: {eff}")
    print(f"判据: {why}")
    print(f"建议配置: {cfg_path} (strategy_kind={kind})")
    if state.get(args.coin):
        s = state[args.coin]
        flag = "" if s.get("effective_regime") == eff else "  <-- 与已生效状态不同,需要切换"
        print(f"已生效: {s.get('effective_regime')} @ {s.get('since', '?')}{flag}")
    if args.history:
        print(f"--- 最近 {args.history} 天逐日标签 ---")
        print(labels.iloc[-args.history:].value_counts(sort=False).to_string())
        print(labels.iloc[-args.history:].iloc[::max(1, args.history // 30)].to_string())
    if args.apply:
        state[args.coin] = {
            "effective_regime": eff,
            "since": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "daily_label": str(labels.iloc[-1]),
            "recommended_config": cfg_path,
            "strategy_kind": kind,
        }
        STATE.write_text(json.dumps(state, indent=2, ensure_ascii=False))
        print(f"state 已更新: {STATE}")
    print("注意: 本脚本只读本地数据、只写本地 state;切换生效需你按自己的部署方式"
          "用建议配置重启 bot 进程(本地重启工具见 src/live/restart_executor.py)。")


if __name__ == "__main__":
    main()
```




# SOL/USDT 永续 —— long（正常震荡） 年度统计表 —— 主档(正常震荡)配置
| 年份 | 收益率 | 期末资金(USD) | 最差回撤 | Sharpe | 成交笔数 | 熔断次数 |
| --- | --- | --- | --- | --- | --- | --- |
| 2020 | -15.30% | 84,705 | -30.17% | 0.00 | 474 | 4 |
| 2021 | +511.22% | 517,733 | -29.71% | 2.91 | 3,346 | 6 |
| 2022 | -14.84% | 440,879 | -37.65% | 0.02 | 2,183 | 10 |
| 2023 | +39.92% | 616,868 | -17.32% | 1.60 | 1,535 | 3 |
| 2024 | +69.29% | 1,044,297 | -18.85% | 1.82 | 1,752 | 2 |
| 2025 | +21.60% | 1,269,851 | -27.69% | 0.71 | 1,504 | 3 |
| 2026 | +1.74% | 1,291,994 | -12.30% | 0.22 | 773 | 2 |




# 三币的核心差异（证据要点）
|  | BTC | ETH | SOL |
| --- | --- | --- | --- |
| 主档 long 全历史 | 4.31x | 7.15x | 28.95x |
| 熊市档 long（底盘） | 2.09x，2022 -43% | 2.63x，2022 -37% | 8.33x，2022 -54%（HSL10 版 +5.1%） |
| 特殊性 | 最均衡 | 对紧止损最敏感（低波动档+HSL10 仅 0.32x）；有 v4 实测叠加（首入距 -1.5%、低波动档降 iq/ddf 等） | 切换价值最大；熊市档+HSL10 的 5.19x 是全部 45 个 HSL 配置中最优单配置 |



# 而 HSL 的红档逻辑是“权益回撤超阈值 → 恐慌平仓该侧全部仓位”。10% 的阈值恰好会在网格 deepest 建仓的回调段把它打断。HSL10 那次 45 配置重跑把这笔账算得很清楚：
|  | 无 HSL 基线 | HSL 10% 版 | 差异 |
| --- | --- | --- | --- |
| BTC 正常震荡 long | 4.31x | 1.19x | -72% |
| ETH 正常震荡 long | 7.15x | 1.68x | -77% |
| SOL 正常震荡 long | 28.95x | 12.92x | -55% |