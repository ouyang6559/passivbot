# ETH 五场景:亮眼结果清单 + 最终参数调试区间

- 生成:2026-10-02,`regime1x/build_eth_bounds.py`;冻结值源:`eth_final/ETH/*.json`。
- 机器可读(可直接粘进配置的 `optimize.bounds`):`bounds_ETH_final.json`。

## 1. 哪些配置的回测结果最亮眼

| 排名 | 配置 | 亮眼点 |
|---|---|---|
| 1 | 强趋势 long v2(全历史) | 唯一四项验收全过:adg 0.00208→0.00233(+12%),dd 持平 0.664,解套亏损占比 93%→78%(全 5 档中唯一 <80%);窗口内 dd 0.110→0.045(-59%)而 adg 仅让 4% |
| 2 | 低波动震荡 both v4(1/0.5) | 窗口内 adg 0.00051,五种调配中最高(比 v1 both +76%);空头侧 v2 使解套亏损 -2,731→-351(-87%)、空头单边 dd 0.069→0.022(-68%) |
| 3 | 正常震荡 多头单边 | 把含上升段的窗口从"清算"拉回"稳定盈利":w1 both_v1 清算(dd 0.950)→ 多头单边 adg +0.150%/天、dd 0.139、亏损/盈利比 0.10;w2 同样全面占优 |
| 4 | 极端波动 both v4(0.52/0.5) | 全历史 42 次回测中唯一无清算的 both 档;崩盘窗口(2021-05)adg +0.119%/天、dd 0.098;作为对照,基准配置在同类崩盘月曾为 -0.35%/天、dd 63% |
| 5 | 熊市 空头(+0.7 多头) | 熊市窗口的利润引擎:空头单边 adg +0.147%/0.174% 每天、dd 0.056/0.262;both(0.7/1) 保住约 2/3~3/4 收益 |

- 正常震荡:多头单边把 w1 从 both_v1 的清算(dd 0.950)拉回 adg +0.150%/天、dd 0.139
- 低波动震荡:both v4(1/0.5) 窗口 adg 0.00051 为全场最高(比 v1 both +76%);空头 v2 解套亏损 -87%
- 强趋势:唯一四项验收全过:全历史 adg +12%、解套占比 93%→78%;窗口 dd 0.045(-59%)
- 熊市下跌:空头是利润引擎:窗口单边 adg 0.147%/0.174% 每天;both 保住 2/3 以上
- 极端波动:唯一全历史可存活的 both 档;崩盘窗口仍 +0.119%/天;对照:基准配置同窗口曾为负收益

## 2. 调试区间设计原则

1. **只放开被验证响应的旋钮**(本轮 v2→v4 实测有效的参数面),其余一律冻结为
  `[v, v]` 零宽度边界(与 regime_1x bounds 的 `[1.25, 1.25]` 同一约定)。
2. **冻结的参数**:EMA 跨度(entry/unstuck ema_span_0/1、volatility spans)、
  threshold_we_weight(0.135)/close we_weight(-0.004)、close.qty_pct(0.1)、
  retracement 权重、forager 全部、enforcer/cooldown——它们定义场景身份,
  放开会让优化器把"低波动档"优化成"另一个正常震荡档"。
3. **放开的核心旋钮与倍率**:初仓 ±20%、入场间距 -20%/+25%、ddf -0.08/+0.06、
  止盈间距 -30%/+40%、解套阈值 -0.07/+0.05、解套切片 ±60%、TWEL ±0.10、
  we_excess [0.6v, 1.5v]、initial_ema_dist/ema_dist 两侧放宽。
4. **在场景窗口内优化**:把配置的 `backtest.start_date/end_date` 改成下表窗口
  再跑优化器;得出结果后必须在"稳健性窗口"复跑确认(防过拟合单窗口)。

| 场景 | 优化窗口 | 稳健性窗口 |
|---|---|---|
| 正常震荡 | 2023-10-13 ~ 2024-05-15 | 2023-02-09 ~ 2023-07-21 |
| 低波动震荡 | 2023-07-05 ~ 2023-11-01 | (无,用相邻月份自选) |
| 强趋势 | 2025-07-16 ~ 2025-09-08 | (无,用相邻月份自选) |
| 熊市下跌 | 2025-10-17 ~ 2026-04-20 | 2022-08-27 ~ 2023-01-24 |
| 极端波动 | 2021-05-03 ~ 2021-05-25 | (无,用相邻月份自选) |

## 3.1 正常震荡(冻结值→调试区间)

建议 optimize.limits(锚定在冻结配置已达成值附近):drawdown_worst_usd greater_than 0.25;loss_profit_ratio greater_than 0.3;adg_pnl less_than 0.001;peak_recovery_hours_pnl greater_than 1344

### 多头(TWEL 1)

| 参数 | 冻结值 | 调试区间 |
|---|---|---|
| risk.total_wallet_exposure_limit | 1 | [0.9, 1.1] 步进 0.01 |
| risk.we_excess_allowance_pct | 1.64 | [0.98, 2.46] 步进 0.01 |
| unstuck.close_pct | 0.00936 | [0.0075, 0.015] 步进 0.0001 |
| unstuck.ema_dist | -0.064 | [-0.1408, -0.0352] 步进 0.0001 |
| unstuck.loss_allowance_pct | 0.00523 | [0.0031, 0.0078] 步进 0.0001 |
| unstuck.threshold | 0.833 | [0.763, 0.883] 步进 0.001 |
| entry.double_down_factor | 0.74 | [0.66, 0.8] 步进 0.01 |
| entry.initial_qty_pct | 0.0313 | [0.025, 0.0376] 步进 0.0001 |
| entry.initial_ema_dist | -0.0081 | [-0.0178, -0.0045] 步进 0.0001 |
| entry.threshold_base_pct | 0.0256 | [0.02048, 0.032] 步进 1e-05 |
| entry.threshold_we_weight | 0.135 | [0.095, 0.203] 步进 0.001 |
| entry.threshold_volatility_1h_weight | 2.4 | [1.7, 3.1] 步进 0.1 |
| close.threshold_base_pct | 0.0047 | [0.00376, 0.00588] 步进 1e-05 |
| close.threshold_volatility_1h_weight | 1 | [0.7, 1.3] 步进 0.1 |

### 空头(TWEL=0 禁用,不参与优化)

## 3.2 低波动震荡(冻结值→调试区间)

建议 optimize.limits(锚定在冻结配置已达成值附近):drawdown_worst_usd greater_than 0.25;loss_profit_ratio greater_than 0.45;adg_pnl less_than 0.00035;peak_recovery_hours_pnl greater_than 1344

### 多头(TWEL 1)

| 参数 | 冻结值 | 调试区间 |
|---|---|---|
| risk.total_wallet_exposure_limit | 1 | [0.9, 1.1] 步进 0.01 |
| risk.we_excess_allowance_pct | 1.64 | [0.98, 2.46] 步进 0.01 |
| unstuck.close_pct | 0.012 | [0.0096, 0.0192] 步进 0.0001 |
| unstuck.ema_dist | -0.045 | [-0.099, -0.0248] 步进 0.0001 |
| unstuck.loss_allowance_pct | 0.008 | [0.0048, 0.012] 步进 0.0001 |
| unstuck.threshold | 0.78 | [0.71, 0.83] 步进 0.001 |
| entry.double_down_factor | 0.72 | [0.64, 0.78] 步进 0.01 |
| entry.initial_qty_pct | 0.04 | [0.032, 0.048] 步进 0.0001 |
| entry.initial_ema_dist | -0.0052 | [-0.0114, -0.0029] 步进 0.0001 |
| entry.threshold_base_pct | 0.015 | [0.012, 0.01875] 步进 1e-05 |
| entry.threshold_we_weight | 0.135 | [0.095, 0.203] 步进 0.001 |
| entry.threshold_volatility_1h_weight | 2.4 | [1.7, 3.1] 步进 0.1 |
| close.threshold_base_pct | 0.0025 | [0.002, 0.00313] 步进 1e-05 |
| close.threshold_volatility_1h_weight | 1 | [0.7, 1.3] 步进 0.1 |

### 空头(TWEL 0.5)

| 参数 | 冻结值 | 调试区间 |
|---|---|---|
| risk.total_wallet_exposure_limit | 0.5 | [0.4, 0.6] 步进 0.01 |
| risk.we_excess_allowance_pct | 1.31 | [0.79, 1.97] 步进 0.01 |
| unstuck.close_pct | 0.012 | [0.0096, 0.0192] 步进 0.0001 |
| unstuck.ema_dist | -0.045 | [-0.099, -0.0248] 步进 0.0001 |
| unstuck.loss_allowance_pct | 0.008 | [0.0048, 0.012] 步进 0.0001 |
| unstuck.threshold | 0.75 | [0.68, 0.8] 步进 0.001 |
| entry.double_down_factor | 0.72 | [0.64, 0.78] 步进 0.01 |
| entry.initial_qty_pct | 0.03 | [0.024, 0.036] 步进 0.0001 |
| entry.initial_ema_dist | 0.0052 | [0.0029, 0.0114] 步进 0.0001 |
| entry.threshold_base_pct | 0.017 | [0.0136, 0.02125] 步进 1e-05 |
| entry.threshold_we_weight | 0.135 | [0.095, 0.203] 步进 0.001 |
| entry.threshold_volatility_1h_weight | 2.4 | [1.7, 3.1] 步进 0.1 |
| close.threshold_base_pct | 0.0025 | [0.002, 0.00313] 步进 1e-05 |
| close.threshold_volatility_1h_weight | 1 | [0.7, 1.3] 步进 0.1 |

## 3.3 强趋势(冻结值→调试区间)

建议 optimize.limits(锚定在冻结配置已达成值附近):drawdown_worst_usd greater_than 0.12;loss_profit_ratio greater_than 0.25;adg_pnl less_than 0.0012

### 多头(TWEL 1)

| 参数 | 冻结值 | 调试区间 |
|---|---|---|
| risk.total_wallet_exposure_limit | 1 | [0.9, 1.1] 步进 0.01 |
| risk.we_excess_allowance_pct | 1.3 | [0.78, 1.95] 步进 0.01 |
| unstuck.close_pct | 0.00936 | [0.0075, 0.015] 步进 0.0001 |
| unstuck.ema_dist | -0.055 | [-0.121, -0.0303] 步进 0.0001 |
| unstuck.loss_allowance_pct | 0.005 | [0.003, 0.0075] 步进 0.0001 |
| unstuck.threshold | 0.75 | [0.68, 0.8] 步进 0.001 |
| entry.double_down_factor | 0.7 | [0.62, 0.76] 步进 0.01 |
| entry.initial_qty_pct | 0.0274 | [0.0219, 0.0329] 步进 0.0001 |
| entry.initial_ema_dist | -0.0091 | [-0.02, -0.005] 步进 0.0001 |
| entry.threshold_base_pct | 0.0316 | [0.02528, 0.0395] 步进 1e-05 |
| entry.threshold_we_weight | 0.135 | [0.095, 0.203] 步进 0.001 |
| entry.threshold_volatility_1h_weight | 2.4 | [1.7, 3.1] 步进 0.1 |
| entry.retracement_base_pct | 0.0037 | [0.00204, 0.00592] 步进 1e-05 |
| close.threshold_base_pct | 0.01 | [0.008, 0.0125] 步进 1e-05 |
| close.threshold_volatility_1h_weight | 1.2 | [0.8, 1.6] 步进 0.1 |

### 空头(TWEL=0 禁用,不参与优化)

## 3.4 熊市下跌(冻结值→调试区间)

建议 optimize.limits(锚定在冻结配置已达成值附近):drawdown_worst_usd greater_than 0.35;loss_profit_ratio greater_than 0.45;adg_pnl less_than 0.0008

### 多头(TWEL 0.7)

| 参数 | 冻结值 | 调试区间 |
|---|---|---|
| risk.total_wallet_exposure_limit | 0.7 | [0.6, 0.8] 步进 0.01 |
| risk.we_excess_allowance_pct | 0.8 | [0.48, 1.2] 步进 0.01 |
| unstuck.close_pct | 0.013 | [0.0104, 0.0208] 步进 0.0001 |
| unstuck.ema_dist | -0.085 | [-0.187, -0.0468] 步进 0.0001 |
| unstuck.loss_allowance_pct | 0.003 | [0.0018, 0.0045] 步进 0.0001 |
| unstuck.threshold | 0.75 | [0.68, 0.8] 步进 0.001 |
| entry.double_down_factor | 0.62 | [0.54, 0.68] 步进 0.01 |
| entry.initial_qty_pct | 0.0189 | [0.0151, 0.0227] 步进 0.0001 |
| entry.initial_ema_dist | -0.0103 | [-0.0227, -0.0057] 步进 0.0001 |
| entry.threshold_base_pct | 0.034 | [0.0272, 0.0425] 步进 1e-05 |
| entry.threshold_we_weight | 0.135 | [0.095, 0.203] 步进 0.001 |
| entry.threshold_volatility_1h_weight | 2.4 | [1.7, 3.1] 步进 0.1 |
| close.threshold_base_pct | 0.0046 | [0.00368, 0.00575] 步进 1e-05 |
| close.threshold_volatility_1h_weight | 0.8 | [0.6, 1] 步进 0.1 |

### 空头(TWEL 1)

| 参数 | 冻结值 | 调试区间 |
|---|---|---|
| risk.total_wallet_exposure_limit | 1 | [0.9, 1.1] 步进 0.01 |
| risk.we_excess_allowance_pct | 1.04 | [0.62, 1.56] 步进 0.01 |
| unstuck.close_pct | 0.00936 | [0.0075, 0.015] 步进 0.0001 |
| unstuck.ema_dist | -0.055 | [-0.121, -0.0303] 步进 0.0001 |
| unstuck.loss_allowance_pct | 0.005 | [0.003, 0.0075] 步进 0.0001 |
| unstuck.threshold | 0.85 | [0.78, 0.9] 步进 0.001 |
| entry.double_down_factor | 0.66 | [0.58, 0.72] 步进 0.01 |
| entry.initial_qty_pct | 0.0277 | [0.0222, 0.0332] 步进 0.0001 |
| entry.initial_ema_dist | 0.009 | [0.005, 0.0198] 步进 0.0001 |
| entry.threshold_base_pct | 0.0311 | [0.02488, 0.03887] 步进 1e-05 |
| entry.threshold_we_weight | 0.135 | [0.095, 0.203] 步进 0.001 |
| entry.threshold_volatility_1h_weight | 2.4 | [1.7, 3.1] 步进 0.1 |
| entry.retracement_base_pct | 0.0036 | [0.00198, 0.00576] 步进 1e-05 |
| close.threshold_base_pct | 0.0075 | [0.006, 0.00937] 步进 1e-05 |
| close.threshold_volatility_1h_weight | 1.2 | [0.8, 1.6] 步进 0.1 |

## 3.5 极端波动(冻结值→调试区间)

建议 optimize.limits(锚定在冻结配置已达成值附近):drawdown_worst_usd greater_than 0.15;loss_profit_ratio greater_than 0.1;adg_pnl less_than 0.0008

### 多头(TWEL 0.52)

| 参数 | 冻结值 | 调试区间 |
|---|---|---|
| risk.total_wallet_exposure_limit | 0.52 | [0.42, 0.62] 步进 0.01 |
| risk.we_excess_allowance_pct | 0.5 | [0.3, 0.75] 步进 0.01 |
| unstuck.close_pct | 0.016 | [0.0128, 0.0256] 步进 0.0001 |
| unstuck.ema_dist | -0.09 | [-0.198, -0.0495] 步进 0.0001 |
| unstuck.loss_allowance_pct | 0.002 | [0.0012, 0.003] 步进 0.0001 |
| unstuck.threshold | 0.7 | [0.63, 0.75] 步进 0.001 |
| entry.double_down_factor | 0.55 | [0.5, 0.61] 步进 0.01 |
| entry.initial_qty_pct | 0.0098 | [0.0078, 0.0118] 步进 0.0001 |
| entry.initial_ema_dist | -0.0211 | [-0.0464, -0.0116] 步进 0.0001 |
| entry.threshold_base_pct | 0.0908 | [0.07264, 0.1135] 步进 1e-05 |
| entry.threshold_we_weight | 0.135 | [0.095, 0.203] 步进 0.001 |
| entry.threshold_volatility_1h_weight | 1.2 | [0.8, 1.6] 步进 0.1 |
| close.threshold_base_pct | 0.0106 | [0.00848, 0.01325] 步进 1e-05 |
| close.threshold_volatility_1h_weight | 0.6 | [0.4, 0.8] 步进 0.1 |

### 空头(TWEL 0.5)

| 参数 | 冻结值 | 调试区间 |
|---|---|---|
| risk.total_wallet_exposure_limit | 0.5 | [0.4, 0.6] 步进 0.01 |
| risk.we_excess_allowance_pct | 0.4 | [0.24, 0.6] 步进 0.01 |
| unstuck.close_pct | 0.016 | [0.0128, 0.0256] 步进 0.0001 |
| unstuck.ema_dist | -0.09 | [-0.198, -0.0495] 步进 0.0001 |
| unstuck.loss_allowance_pct | 0.002 | [0.0012, 0.003] 步进 0.0001 |
| unstuck.threshold | 0.7 | [0.63, 0.75] 步进 0.001 |
| entry.double_down_factor | 0.52 | [0.5, 0.58] 步进 0.01 |
| entry.initial_qty_pct | 0.0093 | [0.0074, 0.0112] 步进 0.0001 |
| entry.initial_ema_dist | 0.0211 | [0.0116, 0.0464] 步进 0.0001 |
| entry.threshold_base_pct | 0.0908 | [0.07264, 0.1135] 步进 1e-05 |
| entry.threshold_we_weight | 0.135 | [0.095, 0.203] 步进 0.001 |
| entry.threshold_volatility_1h_weight | 1.2 | [0.8, 1.6] 步进 0.1 |
| close.threshold_base_pct | 0.0106 | [0.00848, 0.01325] 步进 1e-05 |
| close.threshold_volatility_1h_weight | 0.6 | [0.4, 0.8] 步进 0.1 |

## 4. 优化器使用

```bash
# 1) 复制最终配置,把 backtest.start_date/end_date 改成优化窗口
# 2) 用 bounds_ETH_final.json 里对应场景的 bounds/suggested_limits 替换
#    配置里的 optimize.bounds / optimize.limits
# 3) 运行(优化器同样走官方 CLI)
./venv/bin/passivbot optimize /path/to/<场景>_opt.json
# 4) 优化结果在稳健性窗口回测复核后再采纳
```
- n_cpus/p population 等沿用配置现值;iters 500k 上限配合 pareto 前后需人工筛选:
  在帕累托前沿上优先"adg 不低于冻结值 -5% 且 dd/lpr 改善"的点。
- 空头已禁用的场景(正常震荡/强趋势)bounds 里空头全冻结,不会浪费算力。

---

*私有分析产物,不入库公开。*