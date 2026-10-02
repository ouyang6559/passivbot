# Passivbot v8.4.0：13币种 × 做多/做空/多空 参数研究包

> 目的：提供给其他 AI 做统一、可复现的 Passivbot `trailing_martingale` 回测输入。覆盖 BTC / ETH / SOL / BNB / XRP / DOGE / ADA / AVAX / LINK / DOT / UNI / LTC / XMR，每个币分别给出 Long、Short、Long+Short 三套候选参数。

> **重要**：这些是“实战数据锚定的候选参数”，不是已经证明的全局最优参数。BTC/ETH/SOL 有你此前提供的实测波动率作为锚点；其余币种采用相对波动/流动性分层进行参数外推，必须通过同一套历史数据、同一手续费、同一成交模型进行二次回测验证。


## 1. 数据与证据基线

- 你此前提供的实测波动数据：BTC 平均约 4.18%、≥4% 日波动约 40.15%；ETH 约 6.05% / 60.98%；SOL 约 8.76% / 84.54%；BNB 约 6.47% / 57.90%。这四组数据作为参数尺度的主要锚点。

- Binance 当前市场页面显示 BTC、ETH、BNB、XRP、SOL 等属于高成交量主流资产；Binance USDⓈ-M 参数页也列出了 BTC、ETH、XRP、LTC、LINK、ADA、XMR 等合约的最小名义金额和订单约束，因此本文件默认先按“可交易性”筛选，再按波动率调参。citeturn1search4turn1search7

- Passivbot 官方文档明确：`double_down_factor` 决定后续加仓数量相对当前仓位的比例；`threshold_base_pct` 是再入场距离；波动率权重会随 1H/1M 波动率放宽入场阈值；`initial_qty_pct` 决定初始仓位成本比例。citeturn0search0

- 官方推荐工作流是：从 canonical v8 配置复制 → backtest → optimize → live；因此本文件定位为“回测参数研究包”，不是未经验证的生产配置。citeturn0search1


## 2. 统一执行约束

| 项目 | 本研究默认 |
|---|---|
| Passivbot schema | `v8.4.0` |
| strategy | `trailing_martingale` |
| K线 | 1m 原始数据，内部计算 1H 波动率 |
| leverage | 1x |
| market order | `false` |
| entry retracement | 0（纯被动限价递归加仓） |
| close retracement | 0（纯限价平仓） |
| entry EMA gate | `all` |
| n_positions | 1 / side |
| maker fee | **回测请改成你实际 Binance USDC 合约 maker=0**；不要继续使用研究文件中的 0.0004 作为最终结论 |
| slippage | maker-only 研究阶段建议 0；另做 1–5 bps 敏感性测试 |
| collateral | USDC U-margined perpetual 优先 |


## 3. 为什么做多、做空参数不能完全镜像

做空候选参数统一比做多更保守：初始仓位更小、初始等待距离更大、加仓阈值更宽、unstuck 更宽松。原因不是判断市场方向，而是为了降低短线急速 squeeze 对递归加仓模型的冲击。Long+Short 模式再将单侧最大钱包暴露压到 0.50，避免把“双向启用”误当成“双倍风险预算”。


## 4. 13币种参数总览

| Coin | 波动/流动性定位 | Long 初始仓位 | Long 加仓阈值 | Short 初始仓位 | Short 加仓阈值 | Both 单侧 WE |
|---|---|---:|---:|---:|---:|---:|

| BTC | 低波动/最高流动性 | 0.0180 | 0.0200 | 0.0153 | 0.0216 | 0.50 |
| ETH | 中波动/最高流动性 | 0.0170 | 0.0240 | 0.0144 | 0.0259 | 0.50 |
| SOL | 高波动/高流动性 | 0.0120 | 0.0320 | 0.0102 | 0.0346 | 0.50 |
| BNB | 中波动/高流动性 | 0.0160 | 0.0250 | 0.0136 | 0.0270 | 0.50 |
| XRP | 中高波动/高流动性 | 0.0140 | 0.0280 | 0.0119 | 0.0302 | 0.50 |
| DOGE | 高波动/高流动性 | 0.0100 | 0.0360 | 0.0085 | 0.0389 | 0.50 |
| ADA | 高波动/中高流动性 | 0.0110 | 0.0340 | 0.0094 | 0.0367 | 0.50 |
| AVAX | 高波动/中高流动性 | 0.0100 | 0.0380 | 0.0085 | 0.0410 | 0.50 |
| LINK | 中高波动/高流动性 | 0.0130 | 0.0300 | 0.0111 | 0.0324 | 0.50 |
| DOT | 中高波动/中流动性 | 0.0120 | 0.0320 | 0.0102 | 0.0346 | 0.50 |
| UNI | 中高波动/中高流动性 | 0.0110 | 0.0350 | 0.0094 | 0.0378 | 0.50 |
| LTC | 中波动/高流动性 | 0.0160 | 0.0240 | 0.0136 | 0.0259 | 0.50 |
| XMR | 中高波动/中流动性 | 0.0130 | 0.0290 | 0.0111 | 0.0313 | 0.50 |

## 5. 完整候选参数（39 个 profile）


### BTC

- 波动锚点：4.18%（部分币无统一实测数字，见第1节说明）


#### LONG


**LONG**

```yaml
coin: BTC
mode: long
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 120
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.68
entry.initial_ema_dist: -0.008
entry.initial_qty_pct: 0.018
entry.threshold_base_pct: 0.02
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.005
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.006
unstuck_ema_dist: -0.07
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.007
unstuck_threshold: 0.78
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### SHORT


**SHORT**

```yaml
coin: BTC
mode: short
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 120
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.66
entry.initial_ema_dist: -0.0088
entry.initial_qty_pct: 0.0153
entry.threshold_base_pct: 0.0216
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.005
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.0063
unstuck_ema_dist: -0.0756
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0077
unstuck_threshold: 0.8
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### BOTH


**LONG**

```yaml
coin: BTC
mode: both
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 120
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.68
entry.initial_ema_dist: -0.008
entry.initial_qty_pct: 0.0153
entry.threshold_base_pct: 0.02
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.005
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.006
unstuck_ema_dist: -0.07
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.007
unstuck_threshold: 0.78
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

**SHORT**

```yaml
coin: BTC
mode: both
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 120
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.66
entry.initial_ema_dist: -0.0088
entry.initial_qty_pct: 0.013
entry.threshold_base_pct: 0.0216
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.005
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.0063
unstuck_ema_dist: -0.0756
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0077
unstuck_threshold: 0.8
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

### ETH

- 波动锚点：6.05%（部分币无统一实测数字，见第1节说明）


#### LONG


**LONG**

```yaml
coin: ETH
mode: long
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 100
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.7
entry.initial_ema_dist: -0.0115
entry.initial_qty_pct: 0.017
entry.threshold_base_pct: 0.024
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0056
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.007
unstuck_ema_dist: -0.075
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.008
unstuck_threshold: 0.8
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### SHORT


**SHORT**

```yaml
coin: ETH
mode: short
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 100
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.68
entry.initial_ema_dist: -0.01265
entry.initial_qty_pct: 0.01445
entry.threshold_base_pct: 0.02592
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0056
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.00735
unstuck_ema_dist: -0.081
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0088
unstuck_threshold: 0.82
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### BOTH


**LONG**

```yaml
coin: ETH
mode: both
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 100
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.7
entry.initial_ema_dist: -0.0115
entry.initial_qty_pct: 0.01445
entry.threshold_base_pct: 0.024
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0056
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.007
unstuck_ema_dist: -0.075
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.008
unstuck_threshold: 0.8
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

**SHORT**

```yaml
coin: ETH
mode: both
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 100
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.68
entry.initial_ema_dist: -0.01265
entry.initial_qty_pct: 0.01228
entry.threshold_base_pct: 0.02592
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0056
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.00735
unstuck_ema_dist: -0.081
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0088
unstuck_threshold: 0.82
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

### SOL

- 波动锚点：8.76%（部分币无统一实测数字，见第1节说明）


#### LONG


**LONG**

```yaml
coin: SOL
mode: long
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 80
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.66
entry.initial_ema_dist: -0.016
entry.initial_qty_pct: 0.012
entry.threshold_base_pct: 0.032
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0072
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.009
unstuck_ema_dist: -0.085
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.012
unstuck_threshold: 0.82
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### SHORT


**SHORT**

```yaml
coin: SOL
mode: short
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 80
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.64
entry.initial_ema_dist: -0.0176
entry.initial_qty_pct: 0.0102
entry.threshold_base_pct: 0.03456
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0072
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.00945
unstuck_ema_dist: -0.0918
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0132
unstuck_threshold: 0.84
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### BOTH


**LONG**

```yaml
coin: SOL
mode: both
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 80
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.66
entry.initial_ema_dist: -0.016
entry.initial_qty_pct: 0.0102
entry.threshold_base_pct: 0.032
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0072
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.009
unstuck_ema_dist: -0.085
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.012
unstuck_threshold: 0.82
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

**SHORT**

```yaml
coin: SOL
mode: both
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 80
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.64
entry.initial_ema_dist: -0.0176
entry.initial_qty_pct: 0.00867
entry.threshold_base_pct: 0.03456
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0072
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.00945
unstuck_ema_dist: -0.0918
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0132
unstuck_threshold: 0.84
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

### BNB

- 波动锚点：6.47%（部分币无统一实测数字，见第1节说明）


#### LONG


**LONG**

```yaml
coin: BNB
mode: long
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 105
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.69
entry.initial_ema_dist: -0.012
entry.initial_qty_pct: 0.016
entry.threshold_base_pct: 0.025
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0056
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.007
unstuck_ema_dist: -0.075
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.009
unstuck_threshold: 0.8
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### SHORT


**SHORT**

```yaml
coin: BNB
mode: short
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 105
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.67
entry.initial_ema_dist: -0.0132
entry.initial_qty_pct: 0.0136
entry.threshold_base_pct: 0.027
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0056
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.00735
unstuck_ema_dist: -0.081
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0099
unstuck_threshold: 0.82
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### BOTH


**LONG**

```yaml
coin: BNB
mode: both
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 105
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.69
entry.initial_ema_dist: -0.012
entry.initial_qty_pct: 0.0136
entry.threshold_base_pct: 0.025
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0056
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.007
unstuck_ema_dist: -0.075
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.009
unstuck_threshold: 0.8
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

**SHORT**

```yaml
coin: BNB
mode: both
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 105
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.67
entry.initial_ema_dist: -0.0132
entry.initial_qty_pct: 0.01156
entry.threshold_base_pct: 0.027
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0056
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.00735
unstuck_ema_dist: -0.081
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0099
unstuck_threshold: 0.82
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

### XRP

- 波动锚点：6.8%（部分币无统一实测数字，见第1节说明）


#### LONG


**LONG**

```yaml
coin: XRP
mode: long
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 90
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.67
entry.initial_ema_dist: -0.014
entry.initial_qty_pct: 0.014
entry.threshold_base_pct: 0.028
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0064
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.008
unstuck_ema_dist: -0.08
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.01
unstuck_threshold: 0.81
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### SHORT


**SHORT**

```yaml
coin: XRP
mode: short
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 90
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.65
entry.initial_ema_dist: -0.0154
entry.initial_qty_pct: 0.0119
entry.threshold_base_pct: 0.03024
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0064
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.0084
unstuck_ema_dist: -0.0864
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.011
unstuck_threshold: 0.83
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### BOTH


**LONG**

```yaml
coin: XRP
mode: both
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 90
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.67
entry.initial_ema_dist: -0.014
entry.initial_qty_pct: 0.0119
entry.threshold_base_pct: 0.028
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0064
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.008
unstuck_ema_dist: -0.08
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.01
unstuck_threshold: 0.81
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

**SHORT**

```yaml
coin: XRP
mode: both
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 90
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.65
entry.initial_ema_dist: -0.0154
entry.initial_qty_pct: 0.01011
entry.threshold_base_pct: 0.03024
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0064
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.0084
unstuck_ema_dist: -0.0864
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.011
unstuck_threshold: 0.83
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

### DOGE

- 波动锚点：9.0%（部分币无统一实测数字，见第1节说明）


#### LONG


**LONG**

```yaml
coin: DOGE
mode: long
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 70
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.64
entry.initial_ema_dist: -0.019
entry.initial_qty_pct: 0.01
entry.threshold_base_pct: 0.036
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.008
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.01
unstuck_ema_dist: -0.09
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.014
unstuck_threshold: 0.83
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### SHORT


**SHORT**

```yaml
coin: DOGE
mode: short
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 70
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.62
entry.initial_ema_dist: -0.0209
entry.initial_qty_pct: 0.0085
entry.threshold_base_pct: 0.03888
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.008
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.0105
unstuck_ema_dist: -0.0972
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0154
unstuck_threshold: 0.85
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### BOTH


**LONG**

```yaml
coin: DOGE
mode: both
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 70
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.64
entry.initial_ema_dist: -0.019
entry.initial_qty_pct: 0.0085
entry.threshold_base_pct: 0.036
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.008
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.01
unstuck_ema_dist: -0.09
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.014
unstuck_threshold: 0.83
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

**SHORT**

```yaml
coin: DOGE
mode: both
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 70
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.62
entry.initial_ema_dist: -0.0209
entry.initial_qty_pct: 0.00723
entry.threshold_base_pct: 0.03888
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.008
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.0105
unstuck_ema_dist: -0.0972
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0154
unstuck_threshold: 0.85
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

### ADA

- 波动锚点：8.0%（部分币无统一实测数字，见第1节说明）


#### LONG


**LONG**

```yaml
coin: ADA
mode: long
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 75
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.65
entry.initial_ema_dist: -0.018
entry.initial_qty_pct: 0.011
entry.threshold_base_pct: 0.034
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.008
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.01
unstuck_ema_dist: -0.09
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.013
unstuck_threshold: 0.83
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### SHORT


**SHORT**

```yaml
coin: ADA
mode: short
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 75
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.63
entry.initial_ema_dist: -0.0198
entry.initial_qty_pct: 0.00935
entry.threshold_base_pct: 0.03672
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.008
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.0105
unstuck_ema_dist: -0.0972
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0143
unstuck_threshold: 0.85
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### BOTH


**LONG**

```yaml
coin: ADA
mode: both
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 75
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.65
entry.initial_ema_dist: -0.018
entry.initial_qty_pct: 0.00935
entry.threshold_base_pct: 0.034
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.008
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.01
unstuck_ema_dist: -0.09
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.013
unstuck_threshold: 0.83
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

**SHORT**

```yaml
coin: ADA
mode: both
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 75
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.63
entry.initial_ema_dist: -0.0198
entry.initial_qty_pct: 0.00795
entry.threshold_base_pct: 0.03672
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.008
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.0105
unstuck_ema_dist: -0.0972
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0143
unstuck_threshold: 0.85
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

### AVAX

- 波动锚点：9.0%（部分币无统一实测数字，见第1节说明）


#### LONG


**LONG**

```yaml
coin: AVAX
mode: long
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 70
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.64
entry.initial_ema_dist: -0.02
entry.initial_qty_pct: 0.01
entry.threshold_base_pct: 0.038
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0088
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.011
unstuck_ema_dist: -0.095
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.015
unstuck_threshold: 0.84
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### SHORT


**SHORT**

```yaml
coin: AVAX
mode: short
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 70
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.62
entry.initial_ema_dist: -0.022
entry.initial_qty_pct: 0.0085
entry.threshold_base_pct: 0.04104
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0088
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.01155
unstuck_ema_dist: -0.1026
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0165
unstuck_threshold: 0.86
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### BOTH


**LONG**

```yaml
coin: AVAX
mode: both
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 70
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.64
entry.initial_ema_dist: -0.02
entry.initial_qty_pct: 0.0085
entry.threshold_base_pct: 0.038
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0088
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.011
unstuck_ema_dist: -0.095
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.015
unstuck_threshold: 0.84
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

**SHORT**

```yaml
coin: AVAX
mode: both
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 70
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.62
entry.initial_ema_dist: -0.022
entry.initial_qty_pct: 0.00723
entry.threshold_base_pct: 0.04104
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0088
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.01155
unstuck_ema_dist: -0.1026
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0165
unstuck_threshold: 0.86
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

### LINK

- 波动锚点：7.5%（部分币无统一实测数字，见第1节说明）


#### LONG


**LONG**

```yaml
coin: LINK
mode: long
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 85
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.67
entry.initial_ema_dist: -0.015
entry.initial_qty_pct: 0.013
entry.threshold_base_pct: 0.03
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0068
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.0085
unstuck_ema_dist: -0.083
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.011
unstuck_threshold: 0.81
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### SHORT


**SHORT**

```yaml
coin: LINK
mode: short
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 85
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.65
entry.initial_ema_dist: -0.0165
entry.initial_qty_pct: 0.01105
entry.threshold_base_pct: 0.0324
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0068
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.00893
unstuck_ema_dist: -0.08964
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0121
unstuck_threshold: 0.83
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### BOTH


**LONG**

```yaml
coin: LINK
mode: both
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 85
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.67
entry.initial_ema_dist: -0.015
entry.initial_qty_pct: 0.01105
entry.threshold_base_pct: 0.03
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0068
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.0085
unstuck_ema_dist: -0.083
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.011
unstuck_threshold: 0.81
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

**SHORT**

```yaml
coin: LINK
mode: both
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 85
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.65
entry.initial_ema_dist: -0.0165
entry.initial_qty_pct: 0.00939
entry.threshold_base_pct: 0.0324
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0068
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.00893
unstuck_ema_dist: -0.08964
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0121
unstuck_threshold: 0.83
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

### DOT

- 波动锚点：7.2%（部分币无统一实测数字，见第1节说明）


#### LONG


**LONG**

```yaml
coin: DOT
mode: long
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 85
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.66
entry.initial_ema_dist: -0.0165
entry.initial_qty_pct: 0.012
entry.threshold_base_pct: 0.032
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0072
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.009
unstuck_ema_dist: -0.086
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.012
unstuck_threshold: 0.82
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### SHORT


**SHORT**

```yaml
coin: DOT
mode: short
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 85
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.64
entry.initial_ema_dist: -0.01815
entry.initial_qty_pct: 0.0102
entry.threshold_base_pct: 0.03456
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0072
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.00945
unstuck_ema_dist: -0.09288
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0132
unstuck_threshold: 0.84
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### BOTH


**LONG**

```yaml
coin: DOT
mode: both
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 85
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.66
entry.initial_ema_dist: -0.0165
entry.initial_qty_pct: 0.0102
entry.threshold_base_pct: 0.032
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0072
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.009
unstuck_ema_dist: -0.086
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.012
unstuck_threshold: 0.82
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

**SHORT**

```yaml
coin: DOT
mode: both
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 85
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.64
entry.initial_ema_dist: -0.01815
entry.initial_qty_pct: 0.00867
entry.threshold_base_pct: 0.03456
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0072
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.00945
unstuck_ema_dist: -0.09288
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0132
unstuck_threshold: 0.84
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

### UNI

- 波动锚点：8.0%（部分币无统一实测数字，见第1节说明）


#### LONG


**LONG**

```yaml
coin: UNI
mode: long
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 75
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.65
entry.initial_ema_dist: -0.018
entry.initial_qty_pct: 0.011
entry.threshold_base_pct: 0.035
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.008
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.01
unstuck_ema_dist: -0.092
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.014
unstuck_threshold: 0.83
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### SHORT


**SHORT**

```yaml
coin: UNI
mode: short
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 75
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.63
entry.initial_ema_dist: -0.0198
entry.initial_qty_pct: 0.00935
entry.threshold_base_pct: 0.0378
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.008
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.0105
unstuck_ema_dist: -0.09936
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0154
unstuck_threshold: 0.85
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### BOTH


**LONG**

```yaml
coin: UNI
mode: both
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 75
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.65
entry.initial_ema_dist: -0.018
entry.initial_qty_pct: 0.00935
entry.threshold_base_pct: 0.035
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.008
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.01
unstuck_ema_dist: -0.092
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.014
unstuck_threshold: 0.83
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

**SHORT**

```yaml
coin: UNI
mode: both
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 75
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.63
entry.initial_ema_dist: -0.0198
entry.initial_qty_pct: 0.00795
entry.threshold_base_pct: 0.0378
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.008
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.0105
unstuck_ema_dist: -0.09936
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0154
unstuck_threshold: 0.85
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

### LTC

- 波动锚点：5.8%（部分币无统一实测数字，见第1节说明）


#### LONG


**LONG**

```yaml
coin: LTC
mode: long
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 110
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.69
entry.initial_ema_dist: -0.011
entry.initial_qty_pct: 0.016
entry.threshold_base_pct: 0.024
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0056
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.007
unstuck_ema_dist: -0.075
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.009
unstuck_threshold: 0.8
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### SHORT


**SHORT**

```yaml
coin: LTC
mode: short
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 110
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.67
entry.initial_ema_dist: -0.0121
entry.initial_qty_pct: 0.0136
entry.threshold_base_pct: 0.02592
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0056
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.00735
unstuck_ema_dist: -0.081
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0099
unstuck_threshold: 0.82
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### BOTH


**LONG**

```yaml
coin: LTC
mode: both
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 110
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.69
entry.initial_ema_dist: -0.011
entry.initial_qty_pct: 0.0136
entry.threshold_base_pct: 0.024
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0056
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.007
unstuck_ema_dist: -0.075
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.009
unstuck_threshold: 0.8
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

**SHORT**

```yaml
coin: LTC
mode: both
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 110
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.67
entry.initial_ema_dist: -0.0121
entry.initial_qty_pct: 0.01156
entry.threshold_base_pct: 0.02592
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0056
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.00735
unstuck_ema_dist: -0.081
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0099
unstuck_threshold: 0.82
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

### XMR

- 波动锚点：6.5%（部分币无统一实测数字，见第1节说明）


#### LONG


**LONG**

```yaml
coin: XMR
mode: long
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 90
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.67
entry.initial_ema_dist: -0.0145
entry.initial_qty_pct: 0.013
entry.threshold_base_pct: 0.029
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0068
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.0085
unstuck_ema_dist: -0.083
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.011
unstuck_threshold: 0.81
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### SHORT


**SHORT**

```yaml
coin: XMR
mode: short
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 90
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.65
entry.initial_ema_dist: -0.01595
entry.initial_qty_pct: 0.01105
entry.threshold_base_pct: 0.03132
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0068
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.00893
unstuck_ema_dist: -0.08964
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0121
unstuck_threshold: 0.83
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 1.0
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

#### BOTH


**LONG**

```yaml
coin: XMR
mode: both
side: long
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 90
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.67
entry.initial_ema_dist: -0.0145
entry.initial_qty_pct: 0.01105
entry.threshold_base_pct: 0.029
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0068
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.0085
unstuck_ema_dist: -0.083
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.011
unstuck_threshold: 0.81
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

**SHORT**

```yaml
coin: XMR
mode: both
side: short
strategy_kind: trailing_martingale
volatility_ema_span_1h: 1690
volatility_ema_span_1m: 90
entry.ema_span_0: 770
entry.ema_span_1: 210
entry.ema_gate_mode: all
entry.double_down_factor: 0.65
entry.initial_ema_dist: -0.01595
entry.initial_qty_pct: 0.00939
entry.threshold_base_pct: 0.03132
entry.threshold_we_weight: 0.135
entry.threshold_volatility_1h_weight: 2.4
entry.threshold_volatility_1m_weight: 0
entry.retracement_base_pct: 0
entry.retracement_we_weight: 0
entry.retracement_volatility_1h_weight: 0
entry.retracement_volatility_1m_weight: 0
close.close_qty_pct: 0.1
close.close_threshold_base_pct: 0.0068
close.close_threshold_we_weight: -0.004
close.close_threshold_volatility_1h_weight: 1
close.close_threshold_volatility_1m_weight: 0
close.close_retracement_base_pct: 0
close.close_retracement_volatility_1h_weight: 0
close.close_retracement_volatility_1m_weight: 0
unstuck.ema_span_0: 770
unstuck.ema_span_1: 210
unstuck_close_pct: 0.00893
unstuck_ema_dist: -0.08964
unstuck_enabled: True
unstuck_loss_allowance_pct: 0.0121
unstuck_threshold: 0.83
risk.entry_cooldown_minutes: 0
risk.n_positions: 1
risk.total_wallet_exposure_limit: 0.5
risk.total_exposure_enforcer_enabled: True
risk.total_exposure_enforcer_threshold: 0.95
risk.position_exposure_enforcer_enabled: True
risk.position_exposure_enforcer_threshold: 0.95
risk.we_excess_allowance_pct: 0
live.leverage: 1
live.market_orders_allowed: false
live.time_in_force: good_till_cancelled
```

## 6. 推荐回测顺序：不要 39 套同时暴力优化

### Round 0：成交模型校准
1. Binance USDC perpetual；maker fee = 0。
2. `market_orders_allowed=false`。
3. 先使用 limit fill model；再做 0 / 1 / 3 / 5 bps 的滑点敏感性测试。
4. 先不优化 HSL，避免 HSL 把基础策略差异掩盖。


### Round 1：每个币每个方向只优化 4 个核心变量

固定其它参数，只扫描：`initial_qty_pct`、`double_down_factor`、`initial_ema_dist`、`threshold_base_pct`。建议每个变量 3–5 个点，采用 walk-forward / 时间切片，而不是整段历史一次性拟合。


### Round 2：优化波动适应与解套

只优化：`threshold_volatility_1h_weight`、`close.threshold_base_pct`、`unstuck.close_pct`、`unstuck.loss_allowance_pct`、`unstuck.threshold`。


### Round 3：Long / Short / Both 独立验证

同一时间区间分别测试：Long-only、Short-only、Long+Short。不要因为 Both 的总收益更高就直接选用；必须同时看回撤、持仓时间、最坏连续亏损和资金利用率。


## 7. 每个币的第一轮搜索范围

| Coin | initial_qty_pct | double_down_factor | initial_ema_dist（绝对值） | threshold_base_pct |
|---|---|---|---|---|

| BTC | 0.0135 / 0.0180 / 0.0225 | 0.62 / 0.68 / 0.74 | 0.0060 / 0.0080 / 0.0100 | 0.0170 / 0.0200 / 0.0230 |
| ETH | 0.0128 / 0.0170 / 0.0213 | 0.64 / 0.70 / 0.76 | 0.0086 / 0.0115 / 0.0144 | 0.0204 / 0.0240 / 0.0276 |
| SOL | 0.0090 / 0.0120 / 0.0150 | 0.60 / 0.66 / 0.72 | 0.0120 / 0.0160 / 0.0200 | 0.0272 / 0.0320 / 0.0368 |
| BNB | 0.0120 / 0.0160 / 0.0200 | 0.63 / 0.69 / 0.75 | 0.0090 / 0.0120 / 0.0150 | 0.0213 / 0.0250 / 0.0287 |
| XRP | 0.0105 / 0.0140 / 0.0175 | 0.61 / 0.67 / 0.73 | 0.0105 / 0.0140 / 0.0175 | 0.0238 / 0.0280 / 0.0322 |
| DOGE | 0.0075 / 0.0100 / 0.0125 | 0.58 / 0.64 / 0.70 | 0.0142 / 0.0190 / 0.0238 | 0.0306 / 0.0360 / 0.0414 |
| ADA | 0.0083 / 0.0110 / 0.0137 | 0.59 / 0.65 / 0.71 | 0.0135 / 0.0180 / 0.0225 | 0.0289 / 0.0340 / 0.0391 |
| AVAX | 0.0075 / 0.0100 / 0.0125 | 0.58 / 0.64 / 0.70 | 0.0150 / 0.0200 / 0.0250 | 0.0323 / 0.0380 / 0.0437 |
| LINK | 0.0097 / 0.0130 / 0.0163 | 0.61 / 0.67 / 0.73 | 0.0112 / 0.0150 / 0.0187 | 0.0255 / 0.0300 / 0.0345 |
| DOT | 0.0090 / 0.0120 / 0.0150 | 0.60 / 0.66 / 0.72 | 0.0124 / 0.0165 / 0.0206 | 0.0272 / 0.0320 / 0.0368 |
| UNI | 0.0083 / 0.0110 / 0.0137 | 0.59 / 0.65 / 0.71 | 0.0135 / 0.0180 / 0.0225 | 0.0298 / 0.0350 / 0.0403 |
| LTC | 0.0120 / 0.0160 / 0.0200 | 0.63 / 0.69 / 0.75 | 0.0083 / 0.0110 / 0.0137 | 0.0204 / 0.0240 / 0.0276 |
| XMR | 0.0097 / 0.0130 / 0.0163 | 0.61 / 0.67 / 0.73 | 0.0109 / 0.0145 / 0.0181 | 0.0247 / 0.0290 / 0.0333 |

> Short 搜索时：`initial_qty_pct` 上限建议不超过 Long 中值的 1.0 倍；`threshold_base_pct` 从 Long 中值的 1.0–1.25 倍开始，先验证是否因 squeeze 风险而需要进一步放宽。


## 8. 市场状态过滤：机器人不是 24/7 无条件运行

| 状态 | 4H ADX | 1H ADX | ATR% | 操作 |
|---|---:|---:|---|---|
| 震荡优先 | <22 | <25 | 20–80/90 percentile | 允许启动 |
| 过渡 | 22–25 | 25–30 | 中等 | 降低 WE 或等待 |
| 趋势增强 | >28 | >30 | 上升 | 停止新增风险 |
| 极端趋势/清算 | >30 | >32 | >90 percentile | 不启动/Graceful Stop |


币种具体建议：BTC/ETH/BNB/LTC 使用较宽松的趋势阈值；SOL/DOGE/ADA/AVAX/UNI 对 ATR 和 ADX 更敏感；XRP/LINK/DOT/XMR 采用中间档。这里的阈值是启动门槛，不是预测价格方向。


## 9. 回测必须输出的指标

1. `adg_strategy_eq` / `adg_strategy_eq_w`
2. `sortino_ratio_strategy_eq`
3. `sharpe_ratio_strategy_eq`
4. `drawdown_worst_strategy_eq`
5. `strategy_eq_recovery_days_max`
6. `position_held_days_max`
7. `volume_pct_per_day_avg`
8. `loss_profit_ratio`
9. 最大单仓位 WE
10. 最大连续加仓次数
11. 最长未解套时间
12. unstuck 触发次数、亏损金额
13. maker fill rate
14. 每日成交次数
15. 参数在不同时间切片的稳定性


## 10. 淘汰规则

- 任何参数如果只在单一牛市/熊市年份表现好，不进入候选生产集。
- 最大回撤明显改善但依赖极少数大行情贡献的参数，进入观察组而不是直接采用。
- Long/Short 只要一侧在多个时间切片出现明显尾部风险，就不要为了“多空都做”强行镜像。
- 优先选择参数稳定区间（plateau），而不是单个最优点。
- 如果 maker fill rate 太低，不能仅看理论收益；需要把未成交机会成本纳入评价。


## 11. Passivbot v8.4.0 兼容性说明

本文件故意采用官方 `trailing_martingale` 的字段命名。官方文档说明 v8.4.0 中 entry/close/unstuck 参数位于对应 side 下，并且 `coin_overrides` 可以覆盖每个币种的策略参数；因此后续建议以一个 canonical base config + 每币 `coin_overrides` 的方式落地，而不是维护 39 份完全重复的巨大 JSON。citeturn0search0turn0search2


## 12. 给下一 AI 的直接执行指令

```text
请严格使用本 Markdown 中的 13 个币种 × Long/Short/Both 候选参数进行 Passivbot v8.4.0 trailing_martingale 回测。

要求：
1. 不修改 strategy_kind；
2. 不把未经回测的参数称为最优参数；
3. Binance USDC U-margined perpetual；maker fee = 0；market orders disabled；
4. 1m 数据；按时间切片做 walk-forward；
5. 第一轮只优化 initial_qty_pct / double_down_factor / initial_ema_dist / threshold_base_pct；
6. 第二轮再优化 volatility weight / close / unstuck；
7. Long、Short、Both 分开评分；
8. 评分不能只看 ADG/收益，必须同时约束最大回撤、恢复时间、最长持仓、unstuck 损失和成交率；
9. 输出每个币的 Pareto 前沿、稳定参数区间、推荐候选中心点和 OOS 结果；
10. 如果参数最优点贴着搜索边界，自动扩大该参数搜索区间重新跑。
```

## 13. 外部依据

- Passivbot configuration reference：urlPassivbot 官方 configuration.mdhttps://github.com/enarjord/passivbot/blob/master/docs/configuration.md

- Passivbot config workflow：urlPassivbot 官方 config_workflow.mdhttps://github.com/enarjord/passivbot/blob/master/docs/config_workflow.md

- Binance market overview：urlBinance Marketshttps://www.binance.com/en/markets/overview

- Binance Futures trading parameters：urlBinance Futures Trading Parametershttps://www.binance.com/en-IA/futures/trading-parameters


---
**文件定位：研究/回测候选参数集，不是实盘授权文件。最终生产参数必须通过 OOS、walk-forward 和 maker 成交率验证。**
