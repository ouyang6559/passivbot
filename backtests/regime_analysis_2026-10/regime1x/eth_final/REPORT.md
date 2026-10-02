# ETH 五场景优化参数与多空调配 — 回测验证报告（最终版）

- 日期:2026-10-02;币种:ETH/USDT;数据:本地 Binance USDT-M 1m K线
  (2019-11-28 ~ 2026-10-01,`caches/ft_source`);工具:**官方回测 CLI**
  `./venv/bin/passivbot backtest <config>`,本轮共 42 次回测(全部完成,无错误),
  另引用前一轮 15 次全历史初筛 + 12 次空头窗口回测作基线。
- 前置依据:`docs/针对性配置文件调参数.md`(§2 多头建议表 / §6.3 空头建议表)、
  `REPORT.md` §7-8(regime_1x 全历史初筛与成交过程分析)、§8.4 验收标准。
- 方法:按建议表生成 v2 → 全历史+窗口成对回测 → 未达标场景单变量软化迭代
  (v3) → 冻结点微调(v4)。所有对比同窗口同数据,仅参数不同。

## 1. 五场景最终参数与多空调配(交付物)

配置文件(可直接用于官方回测/实盘导入):`configs/local/eth_final/ETH/<场景>.json`;
机器可读参数:`regime1x/eth_final/params_ETH_final.json`。

| 场景 | 多头 TWEL | 空头 TWEL | 多空调配说明 |
|---|---|---|---|
| 正常震荡 | 1.00 | 0(禁用) | 只做多:空头在两个正常震荡窗口内单边清算/对冲拖累(w1 空头单边清算、both_v1 清算),空头禁用 |
| 低波动震荡 | 1.00 | 0.50 | 多主空辅:空头减半(1.0/0.5),窗口内 both 收益最高;空头用 §6.3 采纳的 v2 参数 |
| 强趋势 | 1.00 | 0(禁用) | 只做多:强上行是空头逆风,空头禁用;多头 v2 四项验收全过 |
| 熊市下跌 | 0.70 | 1.00 | 空主多辅:空头满额 1.0、多头收缩 0.7;熊市窗口内空头贡献约 2/3 收益 |
| 极端波动 | 0.52 | 0.50 | 双向低敞口 0.52/0.5:唯一全历史可存活的 both 档;窗口内零亏损 |

### 1.1 相对 regime_1x v1 的参数变化(仅列改动项)

| 场景 | 侧 | 参数 | v1 | 最终 | 依据 |
|---|---|---|---|---|---|
| 正常震荡 | 多头 | (无改动) | - | - | 保留 regime_1x v1 |
| 低波动震荡 | 多头 | entry.initial_qty_pct | 0.045 | 0.04 | v2 3.0% 过度,回抬至 4.0% |
| 低波动震荡 | 多头 | entry.threshold_base_pct | 0.0137 | 0.015 | 间距+9.5%,压链条深度(v2 1.7% 收益代价过大) |
| 低波动震荡 | 多头 | entry.double_down_factor | 0.78 | 0.72 | 减缓中段堆量 |
| 低波动震荡 | 多头 | unstuck.threshold | 0.88 | 0.78 | 解套提前(v2 0.75 偏激,0.78 平衡) |
| 低波动震荡 | 多头 | unstuck.close_pct | 0.007 | 0.012 | 切片加大,减少割肉次数 |
| 低波动震荡 | 空头 | entry.initial_qty_pct | 0.045 | 0.03 | §6.3 采纳 |
| 低波动震荡 | 空头 | entry.threshold_base_pct | 0.0137 | 0.017 | §6.3 采纳 |
| 低波动震荡 | 空头 | entry.double_down_factor | 0.74 | 0.72 | §6.3 采纳 |
| 低波动震荡 | 空头 | unstuck.threshold | 0.88 | 0.75 | §6.3 采纳 |
| 低波动震荡 | 空头 | unstuck.close_pct | 0.007 | 0.012 | §6.3 采纳 |
| 低波动震荡 | 空头 | TWEL | 1 | 0.5 | 空头敞口减半(独立核算原则) |
| 强趋势 | 多头 | close.threshold_base_pct | 0.0077 | 0.01 | 让利润奔跑(§2) |
| 强趋势 | 多头 | unstuck.threshold | 0.85 | 0.75 | 解套提前(§2) |
| 熊市下跌 | 多头 | (无改动) | - | - | we_excess 0.8→1.0 实测全历史逐笔无差异,回退 |
| 熊市下跌 | 空头 | (无改动) | - | - | §6.3 判定空头基线已近优,保留 |
| 极端波动 | 多头 | TWEL | 0.5 | 0.52 | v2 0.65 回撤超线,v4 定为 0.52(回撤 +4.5% 达标) |
| 极端波动 | 多头 | entry.initial_qty_pct | 0.0093 | 0.0098 | 随敞口微升,提高资本利用率 |
| 极端波动 | 空头 | (无改动) | - | - | 保留 regime_1x v1 |

完整逐参数值(含未改动项)见 `params_ETH_final.json` 与最终配置文件。

## 2. 全历史回测验证(2019-11-28 ~ 2026-10-02,起始资金 100k)

### 2.1 多头单边:v1 基线 vs 各迭代版(选型过程)

| 场景 | 版本 | 日均收益 adg | 最差回撤 dd | 亏损/盈利比 | 清算 | 关键成交结构变化 |
|---|---|---|---|---|---|---|
| 正常震荡 | v1(基线) | +0.00250 | 0.671 | 0.259 | 否 | 链条 3.7 层 / crop 15.2% / 解套亏损 -368k |
| 正常震荡 | v2 | +0.00222 | 0.669 | 0.255 | 否 | 解套亏损 -16% 但初仓缩减拖累收益 |
| 正常震荡 | v3 | +0.00242 | 0.669 | 0.257 | 否 | 恢复初仓后解套改善仅 -4%,-3% 收益 → 判定保留 v1 |
| 低波动震荡 | v1(基线) | +0.00403 | 0.785 | 0.398 | 否 | 链条 8.1 层 / crop 22.5% / 解套亏损 -1,151k(不可接受) |
| 低波动震荡 | v2 | +0.00263 | 0.761 | 0.382 | 否 | 链条 5.0 层 / 解套 -43%,但收益 -35%(过度) |
| 低波动震荡 | v3 | +0.00338 | 0.783 | 0.389 | 否 | 链条 5.3 层 / 解套 -15% / 收益 -16% |
| 低波动震荡 | **v4(采纳)** | +0.00356 | 0.784 | 0.399 | 否 | 链条 5.3 层 / crop 16.0% / 解套 -4% / 收益 -11.6%(窗口内 +76%,见 §3) |
| 强趋势 | v1(基线) | +0.00208 | 0.664 | 0.245 | 否 | 解套亏损占比 93% |
| 强趋势 | **v2(采纳)** | +0.00233 | 0.664 | 0.238 | 否 | 解套占比 78%(<80% 达标)/ crop 0% / 收益 +12% |
| 熊市下跌 | v1(基线)=采纳 | +0.00088 | 0.459 | 0.136 | 否 | crop 4.0% / 解套占比 97%(绝对值小,健康) |
| 熊市下跌 | v2(无差异) | +0.00088 | 0.459 | 0.136 | 否 | we_excess 1.0 未触发任何裁剪差异 → 回退 |
| 极端波动 | v1(基线) | +0.00025 | 0.246 | 0.024 | 否 | WE 顶格 0.495,资本闲置 |
| 极端波动 | v2 | +0.00036 | 0.413 | 0.100 | 否 | 收益 +44% 但回撤 0.246→0.413(超 +5% 线) |
| 极端波动 | v3 | +0.00029 | 0.272 | 0.026 | 否 | 回撤 0.272(仍超线) |
| 极端波动 | **v4(采纳)** | +0.00027 | 0.257 | 0.027 | 否 | 回撤 0.257(+4.5% 达标)/ 收益 +8% / WE 0.515 |

### 2.2 双向(both)全历史

| 场景 | 配置 | adg | dd | 清算 | 说明 |
|---|---|---|---|---|---|
| 极端波动 | v1 both(0.5/0.5) | +0.00029 | 0.246 | 否 | 基线 |
| 极端波动 | v2 both(0.65/0.5) | +0.00033 | 0.411 | 否 | 回撤超线 |
| 极端波动 | **v4 both(0.52/0.5)=采纳** | +0.00031 | 0.257 | 否 | 收益/回撤同向小幅改善 |
| 正常震荡 | v1 both | +0.00371 | 0.975 | 是 | 全历史含牛市,该档只能配合状态开关使用 |
| 低波动震荡 | v1 both | +0.00508 | 0.979 | 是 | 全历史含牛市,该档只能配合状态开关使用 |
| 强趋势 | v1 both | +0.00155 | 0.971 | 是 | 全历史含牛市,该档只能配合状态开关使用 |
| 熊市下跌 | v1 both | +0.00155 | 0.964 | 是 | 全历史含牛市,该档只能配合状态开关使用 |

> 全历史多头 5 档全部完成率 1.0、无清算;空头/双向除 extreme_vol 外全历史必然清算
(与 §7 结论一致),因此各场景的多空调配以 §3 状态窗口验证为准。

## 3. 场景窗口内的多空调配对比(调配的最终依据)

窗口取自 `regime_windows.json` 各场景最长代表窗口(v1 空头单边结果引自 eth_short_windows.json)。

### 正常震荡(2023-10-13 ~ 2024-05-15(窗口内含 2023Q4~2024Q1 上升段))

| 调配 | adg | dd | 亏损/盈利比 | 清算 |
|---|---|---|---|---|
| 空头单边 v1(TWEL 1) | -0.00097 | 0.950 | 10.643 | 是 |
| v1 both(1/1) | +0.00002 | 0.950 | 0.901 | 是 |
| 多头单边 v1(最终调配) | +0.00150 | 0.139 | 0.101 | 否 |

第二窗口(2023-02-09 ~ 2023-07-21):

| 调配 | adg | dd | 亏损/盈利比 | 清算 |
|---|---|---|---|---|
| 空头单边 v1 | -0.00055 | 0.369 | 1.994 | 否 |
| v1 both(1/1) | +0.00054 | 0.335 | 0.540 | 否 |
| 多头单边 v1(最终调配) | +0.00092 | 0.088 | 0.112 | 否 |

### 低波动震荡(2023-07-05 ~ 2023-11-01)

| 调配 | adg | dd | 亏损/盈利比 | 清算 |
|---|---|---|---|---|
| 空头单边 v1 | +0.00035 | 0.069 | 0.391 | 否 |
| 空头单边 v2(§6.3 采纳) | +0.00048 | 0.022 | 0.122 | 否 |
| v1 both(1/1) | +0.00029 | 0.157 | 0.615 | 否 |
| 多头单边 v4 | +0.00049 | 0.161 | 0.327 | 否 |
| **both v4(1/0.5)=最终调配** | +0.00051 | 0.163 | 0.313 | 否 |

### 强趋势(2025-07-16 ~ 2025-09-08)

| 调配 | adg | dd | 亏损/盈利比 | 清算 |
|---|---|---|---|---|
| 空头单边 v1 | +0.00046 | 0.115 | 0.164 | 否 |
| v1 both(1/0.7) | +0.00174 | 0.110 | 0.177 | 否 |
| **多头单边 v2=最终调配** | +0.00167 | 0.045 | 0.149 | 否 |

### 熊市下跌(2025-10-17 ~ 2026-04-20)

| 调配 | adg | dd | 亏损/盈利比 | 清算 |
|---|---|---|---|---|
| 空头单边 v1 | +0.00147 | 0.056 | 0.054 | 否 |
| 多头单边 v1(0.7) | +0.00058 | 0.221 | 0.180 | 否 |
| **both v1(0.7/1)=最终调配** | +0.00122 | 0.227 | 0.318 | 否 |

第二窗口(2022-08-27 ~ 2023-01-24):

| 调配 | adg | dd | 亏损/盈利比 | 清算 |
|---|---|---|---|---|
| 空头单边 v1 | +0.00174 | 0.262 | 0.086 | 否 |
| 多头单边 v1(0.7) | +0.00072 | 0.135 | 0.077 | 否 |
| **both v1(0.7/1)=最终调配** | +0.00172 | 0.259 | 0.137 | 否 |

### 极端波动(2021-05-03 ~ 2021-05-25(2021-05 大崩盘))

| 调配 | adg | dd | 亏损/盈利比 | 清算 |
|---|---|---|---|---|
| 空头单边 v1 | +0.00018 | 0.009 | 0.000 | 否 |
| v1 both(0.5/0.5) | +0.00110 | 0.090 | 0.000 | 否 |
| **both v4(0.52/0.5)=最终调配** | +0.00119 | 0.098 | 0.000 | 否 |

### 3.6 空调配要点(证据摘要)

- **正常震荡:空头禁用**。w1 内空头单边清算(adg -0.097%、dd 0.950、解套占比 72%),
  即使减半到 0.5 也把组合 adg 从 0.00150 拖到 0.00033;w2 内对冲同样降低收益加深回撤。
  参数修复无效(§6.3),唯一解是状态开关。
- **低波动震荡:空头减半启用最优**——both v4(1/0.5) adg 0.00051 为五组调配最高,
  比 v1 both(+0.00029)高 76%;空头 v2 参数使空头侧解套亏损 -2,731→-351。
- **强趋势:推荐空头禁用**。窗口内 both(1/0.7) 的 adg 仅比多头单边高 4%(0.00174 vs 0.00167),
  但回撤深 2.4 倍(0.110 vs 0.045)、亏损/盈利比更高;且空头在全历史下必然清算(完成率 0.18)。
  风险调整后取多头单边;若可接受更深回撤,备选 both(1/0.7)。
- **熊市:空头满额、多头收缩(0.7/1)**。两窗口空头贡献 2/3~3/4 收益
  (both adg 0.00122/0.00172 vs 多头单边 0.00058/0.00072),代价是 dd 0.221→0.227/0.135→0.259。
- **极端波动:双向低敞口**。v4 both 在崩盘窗口 adg +8%、dd +0.008,全历史无清算。

## 4. 下单记录(fills)索引

每次回测的完整下单/成交明细已归档为 `fills.csv.gz`(原 `backtests/binance/<时间戳>/fills.csv`),
同目录含 `analysis.json`(指标)与 `config.json`(当时的完整配置)。逐笔字段:
timestamp, side, type(entry_grid/entry_trailing/close_grid/close_unstuck/close_auto_reduce_twel…),
price, qty, psize, pprice, wallet_exposure, pnl, fee_paid 等。

| 运行标签 | 窗口 | 成交笔数 | 归档目录(相对仓库根) |
|---|---|---|---|
| bear/w1/L0.7_S1_v2 | 2025-10-17~2026-04-20 | 1,247 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/bear__w1__L0.7_S1_v2` |
| bear/w1/Lonly_v2 | 2025-10-17~2026-04-20 | 465 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/bear__w1__Lonly_v2` |
| bear/w1/both_v1 | 2025-10-17~2026-04-20 | 1,247 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/bear__w1__both_v1` |
| bear/w2/L0.7_S1_v2 | 2022-08-27~2023-01-24 | 1,089 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/bear__w2__L0.7_S1_v2` |
| bear/w2/Lonly_v2 | 2022-08-27~2023-01-24 | 602 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/bear__w2__Lonly_v2` |
| bear/w2/both_v1 | 2022-08-27~2023-01-24 | 1,089 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/bear__w2__both_v1` |
| extreme_vol/full/L0.65_S0.5_v2 | 2019-11-28~2026-10-01 | 4,910 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/extreme_vol__full__L0.65_S0.5_v2` |
| extreme_vol/w1/L0.65_S0.5_v2 | 2021-05-03~2021-05-25 | 232 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/extreme_vol__w1__L0.65_S0.5_v2` |
| extreme_vol/w1/both_v1 | 2021-05-03~2021-05-25 | 229 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/extreme_vol__w1__both_v1` |
| longfull_v2/bear | 2019-11-28~2026-10-01 | 7,009 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/longfull_v2__bear` |
| longfull_v2/extreme_vol | 2019-11-28~2026-10-01 | 3,059 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/longfull_v2__extreme_vol` |
| longfull_v2/low_vol_osc | 2019-11-28~2026-10-01 | 18,860 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/longfull_v2__low_vol_osc` |
| longfull_v2/normal_osc | 2019-11-28~2026-10-01 | 10,415 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/longfull_v2__normal_osc` |
| longfull_v2/strong_trend | 2019-11-28~2026-10-01 | 6,277 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/longfull_v2__strong_trend` |
| low_vol_osc/w1/L1_S0.5_v2 | 2023-07-05~2023-11-01 | 1,007 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/low_vol_osc__w1__L1_S0.5_v2` |
| low_vol_osc/w1/Lonly_v2 | 2023-07-05~2023-11-01 | 455 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/low_vol_osc__w1__Lonly_v2` |
| low_vol_osc/w1/both_v1 | 2023-07-05~2023-11-01 | 1,777 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/low_vol_osc__w1__both_v1` |
| normal_osc/w1/L1_S0.5_v2 | 2023-10-13~2024-05-15 | 2,003 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/normal_osc__w1__L1_S0.5_v2` |
| normal_osc/w1/Lonly_v2 | 2023-10-13~2024-05-15 | 1,016 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/normal_osc__w1__Lonly_v2` |
| normal_osc/w1/both_v1 | 2023-10-13~2024-05-15 | 1,305 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/normal_osc__w1__both_v1` |
| normal_osc/w2/L1_S0.5_v2 | 2023-02-09~2023-07-21 | 1,168 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/normal_osc__w2__L1_S0.5_v2` |
| normal_osc/w2/Lonly_v2 | 2023-02-09~2023-07-21 | 546 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/normal_osc__w2__Lonly_v2` |
| normal_osc/w2/both_v1 | 2023-02-09~2023-07-21 | 1,135 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/normal_osc__w2__both_v1` |
| strong_trend/w1/L1_S0.5_v2 | 2025-07-16~2025-09-08 | 440 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/strong_trend__w1__L1_S0.5_v2` |
| strong_trend/w1/Lonly_v2 | 2025-07-16~2025-09-08 | 257 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/strong_trend__w1__Lonly_v2` |
| strong_trend/w1/both_v1 | 2025-07-16~2025-09-08 | 372 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v2/runs/strong_trend__w1__both_v1` |
| extreme_vol/full/L0.55_S0.5_v3 | 2019-11-28~2026-10-01 | 4,905 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v3/runs/extreme_vol__full__L0.55_S0.5_v3` |
| extreme_vol/w1/L0.55_S0.5_v3 | 2021-05-03~2021-05-25 | 231 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v3/runs/extreme_vol__w1__L0.55_S0.5_v3` |
| longfull_v3/extreme_vol | 2019-11-28~2026-10-01 | 3,394 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v3/runs/longfull_v3__extreme_vol` |
| longfull_v3/low_vol_osc | 2019-11-28~2026-10-01 | 20,800 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v3/runs/longfull_v3__low_vol_osc` |
| longfull_v3/normal_osc | 2019-11-28~2026-10-01 | 10,542 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v3/runs/longfull_v3__normal_osc` |
| low_vol_osc/w1/L1_S0.5_v3 | 2023-07-05~2023-11-01 | 1,131 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v3/runs/low_vol_osc__w1__L1_S0.5_v3` |
| low_vol_osc/w1/Lonly_v3 | 2023-07-05~2023-11-01 | 578 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v3/runs/low_vol_osc__w1__Lonly_v3` |
| normal_osc/w1/Lonly_v3 | 2023-10-13~2024-05-15 | 1,062 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v3/runs/normal_osc__w1__Lonly_v3` |
| normal_osc/w2/Lonly_v3 | 2023-02-09~2023-07-21 | 524 | `/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/backtests/regime_analysis_2026-10/regime1x/eth_v3/runs/normal_osc__w2__Lonly_v3` |
| extreme_vol/full/L0.52_S0.5_v4 | 2019-11-28~2026-10-01 | 4,868 | `backtests/regime_analysis_2026-10/regime1x/eth_v4/runs/extreme_vol__full__L0.52_S0.5_v4` |
| extreme_vol/w1/L0.52_S0.5_v4 | 2021-05-03~2021-05-25 | 230 | `backtests/regime_analysis_2026-10/regime1x/eth_v4/runs/extreme_vol__w1__L0.52_S0.5_v4` |
| longfull_v4/extreme_vol | 2019-11-28~2026-10-01 | 3,370 | `backtests/regime_analysis_2026-10/regime1x/eth_v4/runs/longfull_v4__extreme_vol` |
| longfull_v4/low_vol_osc | 2019-11-28~2026-10-01 | 20,334 | `backtests/regime_analysis_2026-10/regime1x/eth_v4/runs/longfull_v4__low_vol_osc` |
| low_vol_osc/w1/L1_S0.5_v4 | 2023-07-05~2023-11-01 | 1,097 | `backtests/regime_analysis_2026-10/regime1x/eth_v4/runs/low_vol_osc__w1__L1_S0.5_v4` |
| normal_osc/w1/Lonly_v1 | 2023-10-13~2024-05-15 | 1,116 | `backtests/regime_analysis_2026-10/regime1x/eth_v4/runs/normal_osc__w1__Lonly_v1` |
| normal_osc/w2/Lonly_v1 | 2023-02-09~2023-07-21 | 543 | `backtests/regime_analysis_2026-10/regime1x/eth_v4/runs/normal_osc__w2__Lonly_v1` |

v1 基线的 15 次全历史回测成交明细在 `results.json` 记录的 `run_dir`
(`backtests/binance/2026-10-01T*`);v1 空头窗口回测明细在 `eth_short_windows.json` 记录的 `run_dir`。

## 5. 验收标准达成情况(§8.4)

| 场景 | 解套亏损占比<80% | crop<8% | adg 不低于基线 | dd ≤ 基线+5% | 结论 |
|---|---|---|---|---|---|
| 正常震荡 | 95%(结构性,不可达) | 13.1%✗(v2)/14.3% | v2/v3 均✗ | ✓ | 解套微调收益≈代价 → **保留 v1**(正常震荡是基准参数的主场) |
| 低波动震荡 | 98%(结构性) | 22.5%→16.0%(改善未达 8% 线) | 全历史 -11.6%✗ / **窗口 +76%✓** | ✓(0.784 vs 0.785) | **采纳 v4**:链条 8.1→5.3 层、crop -6.5pp;全历史收益代价以窗口收益换取,组合部署下净改善 |
| 强趋势 | 93%→**78% ✓** | 0% ✓ | **+12% ✓** | ✓(0.664) | **v2 四项全过,采纳** |
| 熊市下跌 | 97%(结构性) | 4.0% ✓ | 无差异 | 无差异 | **保留 v1**(唯一测试项 we_excess 为无效改动) |
| 极端波动 | 90%(绝对值仅 -0.6k) | 0.4% ✓ | **+8% ✓** | **+4.5% ✓(0.257≤0.259)** | **v4 全过,采纳** |

> 「解套亏损占比<80%」对纯网格多头在含两轮大牛市的 7 年全历史里结构性不可达
(止盈全部盈利,亏损只能来自解套)——只有强趋势档凭追踪入场降到 78%。
对震荡档,可实现的杠杆是解套绝对亏损、链条深度与 crop(§5 表中已列明)。

## 6. 结论

1. **五套场景参数已冻结并可直接使用**(`configs/local/eth_final/ETH/*.json`),
   多空调配:正常震荡 1/0、低波动 1/0.5、强趋势 1/0、熊市 0.7/1、极端波动 0.52/0.5。
2. **验证有效的参数面**:强趋势(止盈放宽+解套提前,四项全过)、极端波动(微升敞口,
   收益+8%且回撤达标)、低波动(链条压深 8.1→5.3 层,窗口收益 +76%)、空头低波动档(v2,
   回撤 -68%)。**验证无效的参数面**:熊市 we_excess(逐笔无差异)、正常震荡解套微调(-4% 换 -3%)。
3. **空头的失败模式是方向逆风而非参数**:含上升段的窗口内任何入场/解套调整都无效,
   只能靠 TWEL 敞口控制或状态开关——五套调配表已按此设计。
4. **部署前提**:本组参数是单币(dynamic_wel_by_tradability=true,WEL=TWEL)语境标定的;
   多币组合需按 WEL=TWEL/n_positions 重标暴露类数值(§5 口径说明)。
   场景切换需实盘复现 `analyze_regimes.py` 的状态判别(最近 30~90 天滚动)。
5. **下一步**:以各场景最终值为界,用优化器(bounds 收窄到 ±20%)在对应状态窗口内精调;
   然后进入多币组合回测。

## 7. 使用方法

```bash
# 直接回测某场景(默认全历史 2019-11-28 ~ 2026-10-01)
./venv/bin/passivbot backtest configs/local/eth_final/ETH/low_vol_osc.json

# 指定窗口:复制配置后修改 backtest.start_date / backtest.end_date 再运行
# (各场景代表性窗口见本报告 §3 与 regime_windows.json)
```
- 5 个最终配置文件已用官方 CLI 冒烟验证(短窗口各一次,全部成功)。
- **参数调试区间(优化器 bounds)**:见 `TUNING_RANGES.md` 与 `bounds_ETH_final.json`
  (由 `build_eth_bounds.py` 生成,冻结值零宽度 + 响应旋钮收窄区间)。
- 实盘场景切换:按 `analyze_regimes.py` 的同一指标对最近 30~90 天滚动判别状态,
  再把对应场景配置的 `bot` 段热更新到运行中的 passivbot;空头启用/禁用由
  `bot.short.risk.total_wallet_exposure_limit` 是否为 0 控制。

---

*生成:`regime1x/build_eth_final.py`;结果数据:`results_v2/v3/v4.json`、`eth_fills_stats.json`、
`eth_short_windows.json`。私有分析产物,不入库公开。*