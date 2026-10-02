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
