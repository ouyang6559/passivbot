# Passivbot BTC / ETH / SOL 手动启动规则与优化参数
> 版本：2026-10-02  
> 策略：`trailing_martingale`  仅做多  
> 目标：稳定性优先、Maker/Limit 优先、避免在单边趋势中启动。
## 1. 先说结论
这份文档把你提供的三套 AI 研究参数作为**基线**，然后做了一轮“保守化 + 币种差异化”的参数调整。

需要特别区分：

- **原研究参数**：来自你上传的 BTC / ETH / SOL 配置。
- **本文件优化参数**：根据原参数结构、BTC/ETH/SOL 相对波动差异，以及你要求的稳定性优先/纯挂单约束提出的**回测候选参数**。
- **不是最终最优参数**：没有直接运行你本地历史数据回测，因此不能把它称为统计意义上的最优解。
- 三个配置均保留 `strategy_kind = trailing_martingale`、`leverage = 1`、`market_orders_allowed = false` 和 GTC 限价单框架。你的原始配置本身就是这样设置的。
## 2. 为什么不能“24小时开着”
`trailing_martingale` 更适合**有足够双向波动、回撤后有较大概率均值回归**的环境。

最危险的不是普通震荡，而是：

1. 4H/1H 同方向强趋势；
2. ATR/真实波动率快速扩张；
3. ADX 从低位快速升到强趋势区；
4. 价格持续远离中长期 EMA；
5. 下跌伴随成交量/OI 同步扩张；
6. 新闻/清算导致单边瀑布。

因此，**手动启动机器人本身就是策略的一部分**。建议先判断“市场环境”，再让 Passivbot 负责执行网格/补仓/止盈。
## 3. 手动启动总规则
### A. 允许启动：满足下面大部分条件

| 指标 | 启动区间/条件 | 作用 |
|---|---|---|
| 4H ADX | `< 22` 优先；22–25 谨慎 | 判断是否进入明显趋势 |
| 1H ADX | `< 25` 优先 | 判断短周期是否正在趋势化 |
| 4H EMA55/EMA200 | 不出现明显空头发散 | 避免在大级别单边下跌中接刀 |
| 1H EMA55 | 价格围绕 EMA55 上下反复 | 典型震荡环境 |
| ATR% / 波动率 | 中等，不处于极端分位 | 需要波动，但不能进入失控状态 |
| Bollinger Band Width | 中等或扩张后重新收窄 | 有来回空间 |
| 15M RSI | 多次在 30–45 / 55–70 间往返 | 适合均值回归 |
| 成交量 | 没有连续放量单边 | 避免趋势启动 |
| OI | 不出现价格下跌+OI暴增的组合 | 避免杠杆清算趋势 |
| 盘口 | 买卖盘仍有双向成交 | 保证限价单有成交环境 |

### B. 不启动：出现任意一个强制条件

- **4H ADX > 30 且 EMA55/200 同向发散**；
- 1H ADX > 30 且价格持续位于 EMA55 同一侧；
- 价格连续突破/跌破 4H 前高/前低并伴随明显放量；
- ATR% 进入过去 90 天极端高分位（建议 > 90% 分位）；
- 下跌时出现 `价格↓ + OI↑ + 成交量↑`；
- 15M/1H 连续多根大实体 K 线，没有正常回撤；
- 重大宏观数据、交易所异常、清算潮期间；
- 已经出现明显的 HSL/unstuck 压力，却仍然想“加仓摊平”。

### C. 已经运行时，什么时候暂停新开仓

建议不要第一时间强平已有仓位，而是：

**停止机器人继续扩大仓位 → 观察 → 根据 unstuck/HSL 处理已有仓位。**

触发条件：

- 4H ADX 从 `<22` 上升到 `>28`；
- 1H ADX > 30；
- ATR% 从中位区间突然跃升到 >90% 分位；
- 价格连续 2–3 个 1H K 线远离 EMA55；
- 价格跌破 4H EMA200 且成交量/OI 同时恶化。

这比“看到跌了马上关机器人”更适合 trailing-martingale。
## 4. 三个币的启动门槛差异
### BTC

BTC 的主要特点是流动性最好、相对波动较低，因此可以接受**更小的价格偏离、更小的初始仓位**。

**建议启动：**

- 4H ADX `< 23`
- 1H ADX `< 26`
- ATR% 不在 >90% 分位
- 价格没有明显跌破 4H EMA200
- 1H EMA55 附近反复
- 15M 有明显回撤/反弹，而不是连续单边 K

**强制暂停：**

- 4H ADX `>30`
- 1H ADX `>32`
- ATR% `>90%`
- 价格 + OI + 成交量同步向下扩张

### ETH

ETH 比 BTC 更容易出现较大的日内扩张，因此入场距离和 unstuck 空间需要略大。

**建议启动：**

- 4H ADX `< 23`
- 1H ADX `< 25`
- ATR% 20–80 分位优先
- 4H EMA200 不出现快速下弯
- 1H EMA55 附近来回
- 15M RSI/价格出现回撤后重新收回短周期均线

**强制暂停：**

- 4H ADX `>29`
- 1H ADX `>30`
- ATR% `>90%`
- ETH 相对 BTC 明显走弱，同时 OI 快速增加

### SOL

SOL 波动明显更高，所以不能直接套 BTC/ETH 参数。

**建议启动：**

- 4H ADX `<21`
- 1H ADX `<24`
- ATR% 25–75 分位优先
- 15M/1H 必须有明确的双向回撤
- 不能刚经历一根/几根异常大阳线或大阴线
- 价格距离 4H EMA200 不能处于极端扩张状态

**强制暂停：**

- 4H ADX `>27`
- 1H ADX `>29`
- ATR% `>85–90%`
- 连续放量单边行情
- OI 快速增长同时价格单边突破

SOL 的暂停门槛比 BTC 更严格，因为 trailing-martingale 在高波动单边行情下更容易快速累积仓位。
## 5. 本次优化后的核心参数
| 币种 | initial_qty_pct | initial_ema_dist | double_down_factor | 入场 threshold | 平仓 threshold | unstuck close | unstuck ema_dist | loss_allowance | unstuck threshold |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| BTC | 0.018 | -0.80% | 0.68 | 2.00% + 2.2×1H波动 | 0.50% + 1×1H波动 | 0.60% | -7.0% | 0.70% | 0.78 |
| ETH | 0.017 | -1.15% | 0.70 | 2.40% + 2.2×1H波动 | 0.55% + 1×1H波动 | 0.70% | -7.5% | 0.80% | 0.80 |
| SOL | 0.012 | -1.60% | 0.66 | 3.20% + 2.4×1H波动 | 0.65% + 1×1H波动 | 0.90% | -8.5% | 1.20% | 0.82 |

### 参数调整逻辑

| 参数 | BTC | ETH | SOL | 调整目的 |
|---|---|---|---|---|
| `initial_qty_pct` | 1.8% | 1.7% | 1.2% | SOL 波动更高，初始仓位更小 |
| `double_down_factor` | 0.68 | 0.70 | 0.66 | 降低连续补仓后的仓位膨胀 |
| `initial_ema_dist` | -0.80% | -1.15% | -1.60% | SOL 需要更深回撤才开始第一笔 |
| `threshold_base_pct` | 2.0% | 2.4% | 3.2% | 波动越高，要求更大的有效空间 |
| `threshold_volatility_1h_weight` | 2.2 | 2.2 | 2.4 | 动态适应波动率 |
| `unstuck.loss_allowance_pct` | 0.70% | 0.80% | 1.20% | 给高波动币更多缓冲 |
| `unstuck.threshold` | 0.78 | 0.80 | 0.82 | 避免过早触发 unstuck |

原始研究中的 BTC/ETH/SOL 都采用 `ema_span_0=770`、`ema_span_1=210`，并以 1H 波动率动态参与入场阈值；本次没有随意改变这套 EMA 骨架，而是主要降低初始仓位、降低加仓倍率，并拉开 SOL 的入场距离。fileciteturn0file0L90-L129 fileciteturn0file1L90-L129 fileciteturn0file2L90-L129

## 6. 推荐的人工操作流程
```text
每天/每4小时检查一次
        ↓
① 先看 4H ADX + EMA55/200
        ↓
强趋势？ ── 是 ──→ 不启动 / 暂停新增仓位
        │
        否
        ↓
② 看 ATR% / Bollinger Width
        ↓
极端波动？ ── 是 ──→ 不启动
        │
        否
        ↓
③ 看 1H ADX + EMA55
        ↓
是否属于来回震荡？
        │
       是
        ↓
④ 看 15M RSI + 价格位置 + 成交量
        ↓
是否存在回撤/反弹，而不是突破追涨杀跌？
        │
       是
        ↓
⑤ 检查 OI / 资金费率 / 盘口
        ↓
没有明显清算/单边杠杆堆积？
        │
       是
        ↓
⑥ 启动对应币种 Passivbot
        ↓
运行期间每 1H 检查一次
        ↓
趋势化 / ATR 极端 / OI异常
        ↓
停止继续扩大风险
```

## 7. 什么时候重新启动

暂停以后不要只看“价格跌回来了”。

建议至少满足：

1. 4H ADX 从强趋势区重新回到 `<23`；
2. 1H ADX `<25`；
3. ATR% 从极端分位下降；
4. 价格重新回到 EMA55 附近形成双向波动；
5. 连续至少 3–6 个 1H K 线没有继续单边扩张；
6. OI/成交量恢复正常。

SOL 建议比 BTC/ETH 多等待一段确认时间。

## 8. 回测时不要只看收益率

建议最终筛选参数时按下面顺序：

1. **最大回撤**
2. **最坏 HSL / unstuck 事件**
3. **Peak Recovery Hours**
4. **Position Held Hours Max**
5. **平均收益**
6. **收益波动**
7. **交易次数**
8. **挂单成交率**
9. **平均持仓时间**
10. **极端行情下最大仓位**

你提供的原配置已经把 `drawdown_worst_hsl`、`drawdown_worst_mean_1pct_hsl`、`peak_recovery_hours_hsl` 和 `position_held_hours_max` 作为重点风险指标，这个方向应该保留。fileciteturn0file0L35-L40

## 9. 重要的回测注意事项

你上传的原始回测配置使用 1 分钟 K 线、Binance 数据，并且研究配置中的 `maker_fee_override` 是 `0.0004`。fileciteturn0file0L3-L23

如果你的真实交易环境是“USDC U 本位合约 + Maker 0 手续费”，正式比较参数时必须把回测手续费改成与你真实账户一致的 Maker 费率，否则参数排序可能产生偏差。

另外，`market_orders_allowed=false` 应继续保持；你当前的目标是尽可能使用 Limit/Maker，而不是为了 unstuck 方便而允许机器人用市价单。

---

# 10. BTC 配置

下面是本次优化后的完整配置。其他运行参数尽量沿用你上传的 BTC 基线，核心只修改策略、风险和手动启动逻辑相关参数。

```json
{
    "backtest": {
        "balance_sample_divider": 60,
        "base_dir": "backtests",
        "btc_collateral_cap": 0.0,
        "btc_collateral_ltv_cap": null,
        "candle_interval_minutes": 1,
        "coin_sources": {},
        "compress_cache": true,
        "dynamic_wel_by_tradability": true,
        "end_date": "2026-10-01",
        "exchanges": [
            "binance"
        ],
        "filter_by_min_effective_cost": false,
        "gap_tolerance_ohlcvs_minutes": 120,
        "liquidation_threshold": 0.05,
        "maker_fee_override": 0.0004,
        "market_order_slippage_pct": 0.0005,
        "limit_order_fill_buffer_pct": 0,
        "market_settings_sources": {},
        "ohlcv_source_dir": "/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/caches/ft_source",
        "scenarios": [
            {
                "label": "BTC_recommended_long"
            }
        ],
        "start_date": "2019-09-09",
        "starting_balance": 100000,
        "suite_enabled": false,
        "taker_fee_override": null,
        "visible_metrics": null,
        "volume_normalization": true,
        "reducer": {
            "default": "mean",
            "drawdown_worst_hsl": "max",
            "drawdown_worst_mean_1pct_hsl": "max",
            "peak_recovery_hours_hsl": "max",
            "position_held_hours_max": "max"
        },
        "hsl_detailed_report": false,
        "hlcvs_data_dir": null,
        "hlcvs_data_override_mode": "intersection",
        "market_settings": {
            "overrides": {},
            "overrides_by_exchange": {}
        },
        "offline": false
    },
    "bot": {
        "long": {
            "forager": {
                "score_weights": {
                    "ema_readiness": 0.0,
                    "volatility": 1.0,
                    "volume": 0.0
                },
                "volatility_ema_span_1m": 120,
                "volume_drop_pct": 0.884,
                "volume_ema_span_1m": 1660
            },
            "hsl": {
                "cooldown_minutes_after_red": 2160,
                "ema_span_minutes": 720,
                "enabled": false,
                "no_restart_drawdown_threshold": 1,
                "orange_tier_mode": "tp_only_with_active_entry_cancellation",
                "panic_close_order_type": "limit",
                "red_threshold": 0.15,
                "restart_after_red_policy": "threshold",
                "tier_ratios": {
                    "orange": 0.75,
                    "yellow": 0.5
                }
            },
            "risk": {
                "entry_cooldown_minutes": 0,
                "n_positions": 1,
                "position_exposure_enforcer_enabled": true,
                "position_exposure_enforcer_threshold": 0.98,
                "total_exposure_enforcer_enabled": true,
                "total_exposure_enforcer_policy": "reduce_overweight",
                "total_exposure_enforcer_threshold": 0.98,
                "total_exposure_entry_gate_enabled": true,
                "total_wallet_exposure_limit": 1,
                "we_excess_allowance_mode": "bounded",
                "we_excess_allowance_pct": 0
            },
            "strategy": {
                "trailing_martingale": {
                    "close": {
                        "qty_pct": 0.1,
                        "retracement_base_pct": 0,
                        "retracement_volatility_1h_weight": 0,
                        "retracement_volatility_1m_weight": 0,
                        "threshold_base_pct": 0.005,
                        "threshold_volatility_1h_weight": 1.0,
                        "threshold_volatility_1m_weight": 0,
                        "threshold_we_weight": -0.004
                    },
                    "entry": {
                        "double_down_factor": 0.68,
                        "ema_gate_mode": "all",
                        "ema_span_0": 770,
                        "ema_span_1": 210,
                        "initial_ema_dist": -0.008,
                        "initial_qty_pct": 0.018,
                        "retracement_base_pct": 0,
                        "retracement_volatility_1h_weight": 0,
                        "retracement_volatility_1m_weight": 0,
                        "retracement_we_weight": 0,
                        "threshold_base_pct": 0.02,
                        "threshold_volatility_1h_weight": 2.2,
                        "threshold_volatility_1m_weight": 0,
                        "threshold_we_weight": 0.0
                    },
                    "volatility_ema_span_1h": 1690,
                    "volatility_ema_span_1m": 60
                }
            },
            "unstuck": {
                "close_pct": 0.006,
                "ema_dist": -0.07,
                "ema_gating_enabled": true,
                "ema_span_0": 770,
                "ema_span_1": 210,
                "enabled": true,
                "loss_allowance_pct": 0.007,
                "threshold": 0.78
            }
        },
        "short": {
            "forager": {
                "score_weights": {
                    "ema_readiness": 0.0,
                    "volatility": 1.0,
                    "volume": 0.0
                },
                "volatility_ema_span_1m": 10,
                "volume_drop_pct": 0.5,
                "volume_ema_span_1m": 360
            },
            "hsl": {
                "cooldown_minutes_after_red": 1440.0,
                "ema_span_minutes": 60.0,
                "enabled": true,
                "no_restart_drawdown_threshold": 1,
                "orange_tier_mode": "tp_only_with_active_entry_cancellation",
                "panic_close_order_type": "market",
                "red_threshold": 0.15,
                "restart_after_red_policy": "threshold",
                "tier_ratios": {
                    "orange": 0.75,
                    "yellow": 0.5
                }
            },
            "risk": {
                "entry_cooldown_minutes": 0,
                "n_positions": 1,
                "position_exposure_enforcer_enabled": true,
                "position_exposure_enforcer_threshold": 0.95,
                "total_exposure_enforcer_enabled": true,
                "total_exposure_enforcer_policy": "reduce_overweight",
                "total_exposure_enforcer_threshold": 0.95,
                "total_exposure_entry_gate_enabled": true,
                "total_wallet_exposure_limit": 0,
                "we_excess_allowance_mode": "bounded",
                "we_excess_allowance_pct": 0
            },
            "strategy": {
                "trailing_martingale": {
                    "close": {
                        "qty_pct": 0.1,
                        "retracement_base_pct": 0,
                        "retracement_volatility_1h_weight": 0,
                        "retracement_volatility_1m_weight": 0,
                        "threshold_base_pct": 0.006,
                        "threshold_volatility_1h_weight": 1,
                        "threshold_volatility_1m_weight": 0,
                        "threshold_we_weight": -0.004
                    },
                    "entry": {
                        "double_down_factor": 0.5,
                        "ema_gate_mode": "all",
                        "ema_span_0": 100,
                        "ema_span_1": 100,
                        "initial_ema_dist": -0.01,
                        "initial_qty_pct": 0.01,
                        "retracement_base_pct": 0,
                        "retracement_volatility_1h_weight": 0,
                        "retracement_volatility_1m_weight": 0,
                        "retracement_we_weight": 0,
                        "threshold_base_pct": 0.025,
                        "threshold_volatility_1h_weight": 1,
                        "threshold_volatility_1m_weight": 0,
                        "threshold_we_weight": 0
                    },
                    "volatility_ema_span_1h": 672,
                    "volatility_ema_span_1m": 60
                }
            },
            "unstuck": {
                "close_pct": 0.001,
                "ema_dist": -0.1,
                "ema_gating_enabled": true,
                "ema_span_0": 100.0,
                "ema_span_1": 100.0,
                "enabled": true,
                "loss_allowance_pct": 0.001,
                "threshold": 0.4
            }
        }
    },
    "coin_overrides": {},
    "config_version": "v8.4.0",
    "live": {
        "approved_coins": {
            "long": [
                "BTC"
            ],
            "short": []
        },
        "auto_gs": true,
        "balance_hysteresis_snap_pct": 0.02,
        "balance_override": null,
        "candle_lock_timeout_seconds": 10,
        "enable_archive_candle_fetch": false,
        "execution_delay_seconds": 2,
        "filter_by_min_effective_cost": true,
        "forced_mode_long": "",
        "forced_mode_short": "",
        "hedge_mode": false,
        "hsl_position_during_cooldown_policy": "panic",
        "hsl_signal_mode": "unified",
        "ignored_coins": {
            "long": [],
            "short": []
        },
        "inactive_coin_candle_ttl_minutes": 10,
        "leverage": 1,
        "margin_mode_preference": "cross",
        "market_order_near_touch_threshold": 0.001,
        "market_orders_allowed": false,
        "max_concurrent_api_requests": null,
        "max_disk_candles_per_symbol_per_tf": 2000000,
        "max_memory_candles_per_symbol": 200000,
        "max_n_cancellations_per_batch": 5,
        "max_n_creations_per_batch": 3,
        "max_n_restarts_per_day": 10,
        "max_ohlcv_fetches_per_minute": 30,
        "max_realized_loss_pct": 1,
        "max_warmup_minutes": 0,
        "minimum_coin_age_days": 0,
        "forager_score_hysteresis_pct": 0.005,
        "order_match_tolerance_pct": 0.0002,
        "pnls_max_lookback_days": 30.0,
        "recv_window_ms": 5000,
        "strategy_kind": "trailing_martingale",
        "time_in_force": "good_till_cancelled",
        "user": "bybit_01",
        "warmup_concurrency": 0,
        "warmup_jitter_seconds": 30,
        "warmup_ratio": 0.3,
        "hsl_engine": "legacy",
        "custom_endpoints_path": null,
        "defer_broad_candle_warmup": true,
        "enable_forager_ws_candles": true,
        "exchange_symbol_unavailable_cooldown_hours": 6.0,
        "fee_conversion_max_age_ms": 86400000,
        "fee_pct_fallback": 0.0002,
        "fee_pct_sanity_abs_max": 0.001,
        "fills_confirmation_overlap_minutes": 60,
        "fills_recent_overlap_minutes": 10,
        "forager_ws_candle_rest_audit_minutes": 30,
        "force_cold_startup": false,
        "hsl_accept_incomplete_history": false,
        "hsl_unavailable_grace_seconds": 120.0,
        "limit_order_create_max_market_dist_pct": 0.8,
        "market_snapshot_ticker_strategy": "auto",
        "max_active_candle_tail_gap_minutes": 10,
        "max_forager_candle_refresh_seconds": 45,
        "max_forager_candle_staleness_minutes": null,
        "order_replacement_churn_gate_activation_count": 10,
        "order_replacement_churn_gate_market_dist_pct": 0.005,
        "order_replacement_churn_gate_stability_minutes": 2.0,
        "order_replacement_churn_gate_window_minutes": 10.0,
        "risk_input_max_attempts": 10,
        "startup_phase_budgets": {},
        "base_config_path": ""
    },
    "logging": {
        "backup_count": 5,
        "dir": "logs",
        "level": 1,
        "max_bytes_mb": 10.0,
        "memory_snapshot_interval_minutes": 30,
        "persist_to_file": true,
        "rotation": false,
        "volume_refresh_info_threshold_seconds": 30,
        "live_event_debug_profiles": []
    },
    "monitor": {
        "checkpoint_interval_minutes": 10.0,
        "compress_rotated_segments": true,
        "emit_completed_candles": true,
        "enabled": true,
        "event_rotation_mb": 128.0,
        "event_rotation_minutes": 60.0,
        "include_raw_fill_payloads": false,
        "max_total_bytes": 1073741824,
        "price_tick_min_interval_ms": 500,
        "retain_candles": true,
        "retain_days": 7.0,
        "retain_fills": true,
        "retain_price_ticks": true,
        "root_dir": "monitor",
        "snapshot_interval_seconds": 1.0
    },
    "optimize": {
        "backend": "pymoo",
        "bounds": {
            "long": {
                "forager": {
                    "score_weights_ema_readiness": [
                        0,
                        1,
                        0.01
                    ],
                    "score_weights_volatility": [
                        0,
                        1,
                        0.01
                    ],
                    "score_weights_volume": [
                        0,
                        1,
                        0.01
                    ],
                    "volatility_ema_span_1m": [
                        10,
                        720,
                        1
                    ],
                    "volume_drop_pct": [
                        0.4,
                        1,
                        0.01
                    ],
                    "volume_ema_span_1m": [
                        360,
                        2880,
                        10
                    ]
                },
                "hsl": {
                    "cooldown_minutes_after_red": [
                        1,
                        2880,
                        10
                    ],
                    "ema_span_minutes": [
                        1,
                        2880,
                        10
                    ],
                    "red_threshold": [
                        0.01,
                        0.12,
                        0.001
                    ]
                },
                "risk": {
                    "entry_cooldown_minutes": [
                        0,
                        60,
                        0.1
                    ],
                    "n_positions": [
                        10,
                        10,
                        1
                    ],
                    "position_exposure_enforcer_threshold": [
                        0.95,
                        1.01,
                        0.001
                    ],
                    "total_exposure_enforcer_threshold": [
                        0.95,
                        1.01,
                        0.001
                    ],
                    "total_wallet_exposure_limit": [
                        1.25,
                        1.25
                    ],
                    "we_excess_allowance_pct": [
                        0,
                        0.3,
                        0.01
                    ]
                },
                "unstuck": {
                    "close_pct": [
                        0.05,
                        0.12,
                        0.001
                    ],
                    "ema_dist": [
                        -0.2,
                        -0.07,
                        0.0001
                    ],
                    "ema_span_0": [
                        770,
                        770
                    ],
                    "ema_span_1": [
                        210,
                        210
                    ],
                    "loss_allowance_pct": [
                        0.005,
                        0.025,
                        0.0001
                    ],
                    "threshold": [
                        0.4,
                        0.9,
                        0.001
                    ]
                },
                "strategy": {
                    "trailing_martingale": {
                        "entry": {
                            "ema_span_0": [
                                200,
                                1440,
                                10
                            ],
                            "ema_span_1": [
                                200,
                                1440,
                                10
                            ],
                            "double_down_factor": [
                                0.5,
                                1,
                                0.01
                            ],
                            "initial_qty_pct": [
                                0.01,
                                0.03,
                                0.0001
                            ],
                            "initial_ema_dist": [
                                -0.01,
                                0.01,
                                0.0001
                            ],
                            "threshold_base_pct": [
                                0,
                                0.04,
                                1e-05
                            ],
                            "threshold_we_weight": [
                                0,
                                5,
                                0.001
                            ],
                            "threshold_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "threshold_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_base_pct": [
                                0,
                                0.015,
                                1e-05
                            ],
                            "retracement_we_weight": [
                                0,
                                5,
                                0.001
                            ],
                            "retracement_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ]
                        },
                        "volatility_ema_span_1h": [
                            672,
                            2016,
                            1
                        ],
                        "volatility_ema_span_1m": [
                            5,
                            720,
                            1
                        ],
                        "close": {
                            "qty_pct": [
                                0.05,
                                1,
                                0.01
                            ],
                            "threshold_base_pct": [
                                -0.02,
                                0.02,
                                1e-05
                            ],
                            "threshold_we_weight": [
                                -0.05,
                                0.05,
                                0.0001
                            ],
                            "threshold_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "threshold_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_base_pct": [
                                0,
                                0.015,
                                1e-05
                            ],
                            "retracement_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ]
                        }
                    }
                }
            },
            "short": {
                "forager": {
                    "score_weights_ema_readiness": [
                        0,
                        1,
                        0.01
                    ],
                    "score_weights_volatility": [
                        0,
                        1,
                        0.01
                    ],
                    "score_weights_volume": [
                        0,
                        1,
                        0.01
                    ],
                    "volatility_ema_span_1m": [
                        10,
                        720,
                        1
                    ],
                    "volume_drop_pct": [
                        0.4,
                        1,
                        0.01
                    ],
                    "volume_ema_span_1m": [
                        360,
                        2880,
                        10
                    ]
                },
                "hsl": {
                    "cooldown_minutes_after_red": [
                        1,
                        2880,
                        10
                    ],
                    "ema_span_minutes": [
                        1,
                        2880,
                        10
                    ],
                    "red_threshold": [
                        0.01,
                        0.12,
                        0.001
                    ]
                },
                "risk": {
                    "entry_cooldown_minutes": [
                        0,
                        60,
                        0.1
                    ],
                    "n_positions": [
                        10,
                        10,
                        1
                    ],
                    "position_exposure_enforcer_threshold": [
                        0.95,
                        1.01,
                        0.001
                    ],
                    "total_exposure_enforcer_threshold": [
                        0.95,
                        1.01,
                        0.001
                    ],
                    "total_wallet_exposure_limit": [
                        0,
                        0
                    ],
                    "we_excess_allowance_pct": [
                        0,
                        0.3,
                        0.01
                    ]
                },
                "unstuck": {
                    "close_pct": [
                        0.05,
                        0.12,
                        0.001
                    ],
                    "ema_dist": [
                        -0.2,
                        -0.07,
                        0.0001
                    ],
                    "ema_span_0": [
                        100,
                        100
                    ],
                    "ema_span_1": [
                        100,
                        100
                    ],
                    "loss_allowance_pct": [
                        0.005,
                        0.025,
                        0.0001
                    ],
                    "threshold": [
                        0.4,
                        0.9,
                        0.001
                    ]
                },
                "strategy": {
                    "trailing_martingale": {
                        "entry": {
                            "ema_span_0": [
                                200,
                                1440,
                                10
                            ],
                            "ema_span_1": [
                                200,
                                1440,
                                10
                            ],
                            "double_down_factor": [
                                0.5,
                                1,
                                0.01
                            ],
                            "initial_qty_pct": [
                                0.01,
                                0.03,
                                0.0001
                            ],
                            "initial_ema_dist": [
                                -0.01,
                                0.01,
                                0.0001
                            ],
                            "threshold_base_pct": [
                                0,
                                0.04,
                                1e-05
                            ],
                            "threshold_we_weight": [
                                0,
                                5,
                                0.001
                            ],
                            "threshold_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "threshold_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_base_pct": [
                                0,
                                0.015,
                                1e-05
                            ],
                            "retracement_we_weight": [
                                0,
                                5,
                                0.001
                            ],
                            "retracement_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ]
                        },
                        "volatility_ema_span_1h": [
                            672,
                            2016,
                            1
                        ],
                        "volatility_ema_span_1m": [
                            5,
                            720,
                            1
                        ],
                        "close": {
                            "qty_pct": [
                                0.05,
                                1,
                                0.01
                            ],
                            "threshold_base_pct": [
                                -0.02,
                                0.02,
                                1e-05
                            ],
                            "threshold_we_weight": [
                                -0.05,
                                0.05,
                                0.0001
                            ],
                            "threshold_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "threshold_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_base_pct": [
                                0,
                                0.015,
                                1e-05
                            ],
                            "retracement_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ]
                        }
                    }
                }
            }
        },
        "compress_results_file": true,
        "crossover_eta": 20,
        "crossover_probability": 0.64,
        "enable_overrides": [],
        "fixed_params": [],
        "fixed_runtime_overrides": {
            "bot.long.hsl.no_restart_drawdown_threshold": 1,
            "bot.short.hsl.no_restart_drawdown_threshold": 1
        },
        "iters": 500000,
        "limits": [
            {
                "metric": "drawdown_worst_btc",
                "penalize_if": "greater_than",
                "value": 0.9
            },
            {
                "metric": "drawdown_worst_usd",
                "penalize_if": "greater_than",
                "value": 0.9
            },
            {
                "metric": "loss_profit_ratio",
                "penalize_if": "greater_than",
                "value": 0.6
            },
            {
                "metric": "adg_pnl",
                "penalize_if": "less_than",
                "reducer": "mean",
                "value": 0.0009
            },
            {
                "metric": "peak_recovery_hours_pnl",
                "penalize_if": "greater_than",
                "value": 1344
            },
            {
                "metric": "position_held_hours_max",
                "penalize_if": "greater_than",
                "value": 1344
            },
            {
                "metric": "position_unchanged_hours_max",
                "penalize_if": "greater_than",
                "value": 840
            }
        ],
        "mutation_eta": 20,
        "mutation_indpb": 0.05,
        "mutation_probability": 0.34,
        "n_cpus": 16,
        "offspring_multiplier": 1,
        "pareto_max_size": 250,
        "population_size": 250,
        "pymoo": {
            "algorithm": "auto",
            "shared": {
                "crossover_eta": 20.0,
                "crossover_prob_var": 0.64,
                "mutation_eta": 20.0,
                "mutation_prob": 0.05,
                "mutation_prob_per_variable": "auto",
                "eliminate_duplicates": true
            },
            "algorithms": {
                "nsga2": {},
                "nsga3": {
                    "ref_dirs": {
                        "method": "das_dennis",
                        "n_partitions": "auto"
                    }
                }
            }
        },
        "round_to_n_significant_digits": 3,
        "scoring": [
            {
                "metric": "adg_pnl",
                "goal": "max"
            },
            {
                "metric": "mdg_pnl",
                "goal": "max"
            },
            {
                "metric": "loss_profit_ratio",
                "goal": "min"
            },
            {
                "metric": "peak_recovery_hours_pnl",
                "goal": "min"
            },
            {
                "metric": "position_held_hours_max",
                "goal": "min"
            },
            {
                "metric": "position_unchanged_hours_max",
                "goal": "min"
            },
            {
                "metric": "volume_pct_per_day_avg_w",
                "goal": "max"
            },
            {
                "metric": "entry_initial_balance_pct_long",
                "goal": "max"
            }
        ],
        "write_all_results": true,
        "objective_scenario": null,
        "seed": null,
        "gpu": {
            "auto_lean_parallelism": true,
            "batch_size": null,
            "max_dispatch_candidate_bars": null,
            "checkpoint_interval_seconds": 5.0,
            "drift_halt": 0.6,
            "drift_rank_halt": null,
            "drift_objective_tolerance": 1e-06,
            "drift_min_samples": 32,
            "drift_probes": 4,
            "drift_window": 128,
            "exact_workers": 0,
            "max_pending_exact": 0,
            "population_size": null,
            "seed_bootstrap": {
                "max_exact": 128,
                "mode": "auto"
            },
            "screening": {
                "scenarios": [],
                "survival_fraction": 0.1,
                "min_survivors": 64
            },
            "validate_per_generation": 8
        }
    },
    "_raw": {
        "backtest": {
            "reducer": {
                "default": "mean",
                "drawdown_worst_hsl": "max",
                "drawdown_worst_mean_1pct_hsl": "max",
                "peak_recovery_hours_hsl": "max",
                "position_held_hours_max": "max"
            },
            "balance_sample_divider": 60,
            "base_dir": "backtests",
            "btc_collateral_cap": 0,
            "btc_collateral_ltv_cap": null,
            "candle_interval_minutes": 1,
            "coin_sources": {},
            "compress_cache": true,
            "dynamic_wel_by_tradability": true,
            "end_date": "now",
            "exchanges": [
                "binance"
            ],
            "filter_by_min_effective_cost": false,
            "gap_tolerance_ohlcvs_minutes": 120,
            "liquidation_threshold": 0.05,
            "maker_fee_override": 0.0004,
            "market_order_slippage_pct": 0.0005,
            "limit_order_fill_buffer_pct": 0,
            "market_settings_sources": {},
            "max_warmup_minutes": 0,
            "ohlcv_source_dir": null,
            "scenarios": [
                {
                    "label": "BTC_normal_osc_long"
                }
            ],
            "start_date": "2019-01-01",
            "starting_balance": 100000,
            "suite_enabled": false,
            "taker_fee_override": null,
            "visible_metrics": null,
            "volume_normalization": true
        },
        "bot": {
            "long": {
                "forager": {
                    "score_weights": {
                        "ema_readiness": 0,
                        "volatility": 1,
                        "volume": 0
                    },
                    "volatility_ema_span_1m": 101,
                    "volume_drop_pct": 0.884,
                    "volume_ema_span_1m": 1660
                },
                "risk": {
                    "entry_cooldown_minutes": 0,
                    "n_positions": 1,
                    "total_wallet_exposure_limit": 1,
                    "total_exposure_enforcer_enabled": true,
                    "total_exposure_enforcer_threshold": 0.99,
                    "we_excess_allowance_pct": 1.64,
                    "position_exposure_enforcer_enabled": true,
                    "position_exposure_enforcer_threshold": 0.99
                },
                "strategy": {
                    "trailing_martingale": {
                        "volatility_ema_span_1h": 1690,
                        "volatility_ema_span_1m": 60,
                        "entry": {
                            "ema_span_0": 770,
                            "ema_span_1": 210,
                            "double_down_factor": 0.74,
                            "initial_ema_dist": -0.0067,
                            "initial_qty_pct": 0.0359,
                            "threshold_base_pct": 0.0195,
                            "threshold_we_weight": 0.135,
                            "threshold_volatility_1h_weight": 2.4,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_we_weight": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        },
                        "close": {
                            "qty_pct": 0.1,
                            "threshold_base_pct": 0.0036,
                            "threshold_we_weight": -0.004,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        }
                    }
                },
                "unstuck": {
                    "ema_span_0": 770,
                    "ema_span_1": 210,
                    "close_pct": 0.00936,
                    "ema_dist": -0.064,
                    "enabled": true,
                    "loss_allowance_pct": 0.00523,
                    "threshold": 0.833
                }
            },
            "short": {
                "forager": {
                    "score_weights": {
                        "ema_readiness": 0,
                        "volatility": 1,
                        "volume": 0
                    },
                    "volatility_ema_span_1m": 10,
                    "volume_drop_pct": 0.5,
                    "volume_ema_span_1m": 360
                },
                "hsl": {
                    "cooldown_minutes_after_red": 0,
                    "ema_span_minutes": 60,
                    "enabled": false,
                    "no_restart_drawdown_threshold": 1,
                    "orange_tier_mode": "tp_only_with_active_entry_cancellation",
                    "panic_close_order_type": "limit",
                    "red_threshold": 0.2,
                    "tier_ratios": {
                        "orange": 0.75,
                        "yellow": 0.5
                    }
                },
                "risk": {
                    "entry_cooldown_minutes": 0,
                    "n_positions": 1,
                    "total_wallet_exposure_limit": 0,
                    "total_exposure_enforcer_enabled": true,
                    "total_exposure_enforcer_threshold": 0.95,
                    "we_excess_allowance_pct": 0,
                    "position_exposure_enforcer_enabled": true,
                    "position_exposure_enforcer_threshold": 0.95
                },
                "strategy": {
                    "trailing_martingale": {
                        "volatility_ema_span_1h": 672,
                        "volatility_ema_span_1m": 60,
                        "entry": {
                            "ema_span_0": 100,
                            "ema_span_1": 100,
                            "double_down_factor": 0.5,
                            "initial_ema_dist": -0.01,
                            "initial_qty_pct": 0.01,
                            "threshold_base_pct": 0.025,
                            "threshold_we_weight": 0,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_we_weight": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        },
                        "close": {
                            "qty_pct": 0.1,
                            "threshold_base_pct": 0.006,
                            "threshold_we_weight": -0.004,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        }
                    }
                },
                "unstuck": {
                    "ema_span_0": 100,
                    "ema_span_1": 100,
                    "close_pct": 0.001,
                    "ema_dist": -0.1,
                    "enabled": true,
                    "loss_allowance_pct": 0.001,
                    "threshold": 0.4
                }
            }
        },
        "coin_overrides": {},
        "config_version": "v8.4.0",
        "live": {
            "approved_coins": {
                "long": [
                    "BTC"
                ],
                "short": []
            },
            "auto_gs": true,
            "balance_hysteresis_snap_pct": 0.02,
            "balance_override": null,
            "candle_lock_timeout_seconds": 10,
            "enable_archive_candle_fetch": false,
            "execution_delay_seconds": 2,
            "filter_by_min_effective_cost": true,
            "forced_mode_long": "",
            "forced_mode_short": "",
            "hedge_mode": false,
            "hsl_position_during_cooldown_policy": "panic",
            "hsl_signal_mode": "unified",
            "ignored_coins": {
                "long": [],
                "short": []
            },
            "inactive_coin_candle_ttl_minutes": 10,
            "leverage": 1,
            "margin_mode_preference": "cross",
            "market_order_near_touch_threshold": 0.001,
            "market_orders_allowed": false,
            "max_concurrent_api_requests": null,
            "max_disk_candles_per_symbol_per_tf": 2000000,
            "max_memory_candles_per_symbol": 200000,
            "max_n_cancellations_per_batch": 5,
            "max_n_creations_per_batch": 3,
            "max_n_restarts_per_day": 10,
            "max_ohlcv_fetches_per_minute": 30,
            "max_realized_loss_pct": 1,
            "max_warmup_minutes": 0,
            "minimum_coin_age_days": 0,
            "forager_score_hysteresis_pct": 0.005,
            "order_match_tolerance_pct": 0.0002,
            "pnls_max_lookback_days": 30,
            "recv_window_ms": 5000,
            "strategy_kind": "trailing_martingale",
            "time_in_force": "good_till_cancelled",
            "user": "bybit_01",
            "warmup_concurrency": 0,
            "warmup_jitter_seconds": 30,
            "warmup_ratio": 0.3
        },
        "logging": {
            "backup_count": 5,
            "dir": "logs",
            "level": 1,
            "max_bytes_mb": 10,
            "memory_snapshot_interval_minutes": 30,
            "persist_to_file": true,
            "rotation": false,
            "volume_refresh_info_threshold_seconds": 30
        },
        "monitor": {
            "checkpoint_interval_minutes": 10,
            "compress_rotated_segments": true,
            "emit_completed_candles": true,
            "enabled": true,
            "event_rotation_mb": 128,
            "event_rotation_minutes": 60,
            "include_raw_fill_payloads": false,
            "max_total_bytes": 1073741824,
            "price_tick_min_interval_ms": 500,
            "retain_candles": true,
            "retain_days": 7,
            "retain_fills": true,
            "retain_price_ticks": true,
            "root_dir": "monitor",
            "snapshot_interval_seconds": 1
        },
        "optimize": {
            "backend": "pymoo",
            "bounds": {
                "long": {
                    "forager": {
                        "score_weights_ema_readiness": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volatility": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volume": [
                            0,
                            1,
                            0.01
                        ],
                        "volatility_ema_span_1m": [
                            10,
                            720,
                            1
                        ],
                        "volume_drop_pct": [
                            0.4,
                            1,
                            0.01
                        ],
                        "volume_ema_span_1m": [
                            360,
                            2880,
                            10
                        ]
                    },
                    "hsl": {
                        "cooldown_minutes_after_red": [
                            1,
                            2880,
                            10
                        ],
                        "ema_span_minutes": [
                            1,
                            2880,
                            10
                        ],
                        "red_threshold": [
                            0.01,
                            0.12,
                            0.001
                        ]
                    },
                    "risk": {
                        "entry_cooldown_minutes": [
                            0,
                            60,
                            0.1
                        ],
                        "n_positions": [
                            10,
                            10,
                            1
                        ],
                        "total_wallet_exposure_limit": [
                            1.25,
                            1.25
                        ],
                        "total_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ],
                        "we_excess_allowance_pct": [
                            0,
                            0.3,
                            0.01
                        ],
                        "position_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ]
                    },
                    "strategy": {
                        "trailing_martingale": {
                            "volatility_ema_span_1h": [
                                672,
                                2016,
                                1
                            ],
                            "volatility_ema_span_1m": [
                                5,
                                720,
                                1
                            ],
                            "entry": {
                                "ema_span_0": [
                                    200,
                                    1440,
                                    10
                                ],
                                "ema_span_1": [
                                    200,
                                    1440,
                                    10
                                ],
                                "double_down_factor": [
                                    0.5,
                                    1,
                                    0.01
                                ],
                                "initial_ema_dist": [
                                    -0.01,
                                    0.01,
                                    0.0001
                                ],
                                "initial_qty_pct": [
                                    0.01,
                                    0.03,
                                    0.0001
                                ],
                                "threshold_base_pct": [
                                    0,
                                    0.04,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            },
                            "close": {
                                "qty_pct": [
                                    0.05,
                                    1,
                                    0.01
                                ],
                                "threshold_base_pct": [
                                    -0.02,
                                    0.02,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    -0.05,
                                    0.05,
                                    0.0001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            }
                        }
                    },
                    "unstuck": {
                        "ema_span_0": [
                            770,
                            770
                        ],
                        "ema_span_1": [
                            210,
                            210
                        ],
                        "close_pct": [
                            0.05,
                            0.12,
                            0.001
                        ],
                        "ema_dist": [
                            -0.2,
                            -0.07,
                            0.0001
                        ],
                        "loss_allowance_pct": [
                            0.005,
                            0.025,
                            0.0001
                        ],
                        "threshold": [
                            0.4,
                            0.9,
                            0.001
                        ]
                    }
                },
                "short": {
                    "forager": {
                        "score_weights_ema_readiness": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volatility": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volume": [
                            0,
                            1,
                            0.01
                        ],
                        "volatility_ema_span_1m": [
                            10,
                            720,
                            1
                        ],
                        "volume_drop_pct": [
                            0.4,
                            1,
                            0.01
                        ],
                        "volume_ema_span_1m": [
                            360,
                            2880,
                            10
                        ]
                    },
                    "hsl": {
                        "cooldown_minutes_after_red": [
                            1,
                            2880,
                            10
                        ],
                        "ema_span_minutes": [
                            1,
                            2880,
                            10
                        ],
                        "red_threshold": [
                            0.01,
                            0.12,
                            0.001
                        ]
                    },
                    "risk": {
                        "entry_cooldown_minutes": [
                            0,
                            60,
                            0.1
                        ],
                        "n_positions": [
                            10,
                            10,
                            1
                        ],
                        "total_wallet_exposure_limit": [
                            0,
                            0
                        ],
                        "total_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ],
                        "we_excess_allowance_pct": [
                            0,
                            0.3,
                            0.01
                        ],
                        "position_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ]
                    },
                    "strategy": {
                        "trailing_martingale": {
                            "volatility_ema_span_1h": [
                                672,
                                2016,
                                1
                            ],
                            "volatility_ema_span_1m": [
                                5,
                                720,
                                1
                            ],
                            "entry": {
                                "ema_span_0": [
                                    200,
                                    1440,
                                    10
                                ],
                                "ema_span_1": [
                                    200,
                                    1440,
                                    10
                                ],
                                "double_down_factor": [
                                    0.5,
                                    1,
                                    0.01
                                ],
                                "initial_ema_dist": [
                                    -0.01,
                                    0.01,
                                    0.0001
                                ],
                                "initial_qty_pct": [
                                    0.01,
                                    0.03,
                                    0.0001
                                ],
                                "threshold_base_pct": [
                                    0,
                                    0.04,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            },
                            "close": {
                                "qty_pct": [
                                    0.05,
                                    1,
                                    0.01
                                ],
                                "threshold_base_pct": [
                                    -0.02,
                                    0.02,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    -0.05,
                                    0.05,
                                    0.0001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            }
                        }
                    },
                    "unstuck": {
                        "ema_span_0": [
                            100,
                            100
                        ],
                        "ema_span_1": [
                            100,
                            100
                        ],
                        "close_pct": [
                            0.05,
                            0.12,
                            0.001
                        ],
                        "ema_dist": [
                            -0.2,
                            -0.07,
                            0.0001
                        ],
                        "loss_allowance_pct": [
                            0.005,
                            0.025,
                            0.0001
                        ],
                        "threshold": [
                            0.4,
                            0.9,
                            0.001
                        ]
                    }
                }
            },
            "compress_results_file": true,
            "crossover_eta": 20,
            "crossover_probability": 0.64,
            "enable_overrides": [],
            "fixed_params": [],
            "fixed_runtime_overrides": {
                "bot.long.hsl.no_restart_drawdown_threshold": 1,
                "bot.short.hsl.no_restart_drawdown_threshold": 1
            },
            "iters": 500000,
            "limits": [
                {
                    "metric": "drawdown_worst_btc",
                    "penalize_if": "greater_than",
                    "value": 0.9
                },
                {
                    "metric": "drawdown_worst_usd",
                    "penalize_if": "greater_than",
                    "value": 0.9
                },
                {
                    "metric": "loss_profit_ratio",
                    "penalize_if": "greater_than",
                    "value": 0.6
                },
                {
                    "metric": "adg_pnl",
                    "penalize_if": "less_than",
                    "reducer": "mean",
                    "value": 0.0009
                },
                {
                    "metric": "peak_recovery_hours_pnl",
                    "penalize_if": "greater_than",
                    "value": 1344
                },
                {
                    "metric": "position_held_hours_max",
                    "penalize_if": "greater_than",
                    "value": 1344
                },
                {
                    "metric": "position_unchanged_hours_max",
                    "penalize_if": "greater_than",
                    "value": 840
                }
            ],
            "mutation_eta": 20,
            "mutation_indpb": 0.05,
            "mutation_probability": 0.34,
            "n_cpus": 16,
            "offspring_multiplier": 1,
            "pareto_max_size": 250,
            "population_size": 250,
            "pymoo": {
                "algorithm": "auto",
                "algorithms": {
                    "nsga2": {},
                    "nsga3": {
                        "ref_dirs": {
                            "method": "das_dennis",
                            "n_partitions": "auto"
                        }
                    }
                },
                "shared": {
                    "crossover_eta": 20,
                    "crossover_prob_var": 0.64,
                    "eliminate_duplicates": true,
                    "mutation_eta": 20,
                    "mutation_prob": 0.05,
                    "mutation_prob_per_variable": "auto"
                }
            },
            "round_to_n_significant_digits": 3,
            "scoring": [
                {
                    "goal": "max",
                    "metric": "adg_pnl"
                },
                {
                    "goal": "max",
                    "metric": "mdg_pnl"
                },
                {
                    "goal": "min",
                    "metric": "loss_profit_ratio"
                },
                {
                    "goal": "min",
                    "metric": "peak_recovery_hours_pnl"
                },
                {
                    "goal": "min",
                    "metric": "position_held_hours_max"
                },
                {
                    "goal": "min",
                    "metric": "position_unchanged_hours_max"
                },
                {
                    "goal": "max",
                    "metric": "volume_pct_per_day_avg_w"
                },
                {
                    "goal": "max",
                    "metric": "entry_initial_balance_pct_long"
                }
            ],
            "write_all_results": true
        }
    },
    "_raw_effective": {
        "backtest": {
            "reducer": {
                "default": "mean",
                "drawdown_worst_hsl": "max",
                "drawdown_worst_mean_1pct_hsl": "max",
                "peak_recovery_hours_hsl": "max",
                "position_held_hours_max": "max"
            },
            "balance_sample_divider": 60,
            "base_dir": "backtests",
            "btc_collateral_cap": 0,
            "btc_collateral_ltv_cap": null,
            "candle_interval_minutes": 1,
            "coin_sources": {},
            "compress_cache": true,
            "dynamic_wel_by_tradability": true,
            "end_date": "now",
            "exchanges": [
                "binance"
            ],
            "filter_by_min_effective_cost": false,
            "gap_tolerance_ohlcvs_minutes": 120,
            "liquidation_threshold": 0.05,
            "maker_fee_override": 0.0004,
            "market_order_slippage_pct": 0.0005,
            "limit_order_fill_buffer_pct": 0,
            "market_settings_sources": {},
            "max_warmup_minutes": 0,
            "ohlcv_source_dir": null,
            "scenarios": [
                {
                    "label": "BTC_normal_osc_long"
                }
            ],
            "start_date": "2019-01-01",
            "starting_balance": 100000,
            "suite_enabled": false,
            "taker_fee_override": null,
            "visible_metrics": null,
            "volume_normalization": true
        },
        "bot": {
            "long": {
                "forager": {
                    "score_weights": {
                        "ema_readiness": 0,
                        "volatility": 1,
                        "volume": 0
                    },
                    "volatility_ema_span_1m": 101,
                    "volume_drop_pct": 0.884,
                    "volume_ema_span_1m": 1660
                },
                "risk": {
                    "entry_cooldown_minutes": 0,
                    "n_positions": 1,
                    "total_wallet_exposure_limit": 1,
                    "total_exposure_enforcer_enabled": true,
                    "total_exposure_enforcer_threshold": 0.99,
                    "we_excess_allowance_pct": 1.64,
                    "position_exposure_enforcer_enabled": true,
                    "position_exposure_enforcer_threshold": 0.99
                },
                "strategy": {
                    "trailing_martingale": {
                        "volatility_ema_span_1h": 1690,
                        "volatility_ema_span_1m": 60,
                        "entry": {
                            "ema_span_0": 770,
                            "ema_span_1": 210,
                            "double_down_factor": 0.74,
                            "initial_ema_dist": -0.0067,
                            "initial_qty_pct": 0.0359,
                            "threshold_base_pct": 0.0195,
                            "threshold_we_weight": 0.135,
                            "threshold_volatility_1h_weight": 2.4,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_we_weight": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        },
                        "close": {
                            "qty_pct": 0.1,
                            "threshold_base_pct": 0.0036,
                            "threshold_we_weight": -0.004,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        }
                    }
                },
                "unstuck": {
                    "ema_span_0": 770,
                    "ema_span_1": 210,
                    "close_pct": 0.00936,
                    "ema_dist": -0.064,
                    "enabled": true,
                    "loss_allowance_pct": 0.00523,
                    "threshold": 0.833
                }
            },
            "short": {
                "forager": {
                    "score_weights": {
                        "ema_readiness": 0,
                        "volatility": 1,
                        "volume": 0
                    },
                    "volatility_ema_span_1m": 10,
                    "volume_drop_pct": 0.5,
                    "volume_ema_span_1m": 360
                },
                "hsl": {
                    "cooldown_minutes_after_red": 0,
                    "ema_span_minutes": 60,
                    "enabled": false,
                    "no_restart_drawdown_threshold": 1,
                    "orange_tier_mode": "tp_only_with_active_entry_cancellation",
                    "panic_close_order_type": "limit",
                    "red_threshold": 0.2,
                    "tier_ratios": {
                        "orange": 0.75,
                        "yellow": 0.5
                    }
                },
                "risk": {
                    "entry_cooldown_minutes": 0,
                    "n_positions": 1,
                    "total_wallet_exposure_limit": 0,
                    "total_exposure_enforcer_enabled": true,
                    "total_exposure_enforcer_threshold": 0.95,
                    "we_excess_allowance_pct": 0,
                    "position_exposure_enforcer_enabled": true,
                    "position_exposure_enforcer_threshold": 0.95
                },
                "strategy": {
                    "trailing_martingale": {
                        "volatility_ema_span_1h": 672,
                        "volatility_ema_span_1m": 60,
                        "entry": {
                            "ema_span_0": 100,
                            "ema_span_1": 100,
                            "double_down_factor": 0.5,
                            "initial_ema_dist": -0.01,
                            "initial_qty_pct": 0.01,
                            "threshold_base_pct": 0.025,
                            "threshold_we_weight": 0,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_we_weight": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        },
                        "close": {
                            "qty_pct": 0.1,
                            "threshold_base_pct": 0.006,
                            "threshold_we_weight": -0.004,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        }
                    }
                },
                "unstuck": {
                    "ema_span_0": 100,
                    "ema_span_1": 100,
                    "close_pct": 0.001,
                    "ema_dist": -0.1,
                    "enabled": true,
                    "loss_allowance_pct": 0.001,
                    "threshold": 0.4
                }
            }
        },
        "coin_overrides": {},
        "config_version": "v8.4.0",
        "live": {
            "approved_coins": {
                "long": [
                    "BTC"
                ],
                "short": []
            },
            "auto_gs": true,
            "balance_hysteresis_snap_pct": 0.02,
            "balance_override": null,
            "candle_lock_timeout_seconds": 10,
            "enable_archive_candle_fetch": false,
            "execution_delay_seconds": 2,
            "filter_by_min_effective_cost": true,
            "forced_mode_long": "",
            "forced_mode_short": "",
            "hedge_mode": false,
            "hsl_position_during_cooldown_policy": "panic",
            "hsl_signal_mode": "unified",
            "ignored_coins": {
                "long": [],
                "short": []
            },
            "inactive_coin_candle_ttl_minutes": 10,
            "leverage": 1,
            "margin_mode_preference": "cross",
            "market_order_near_touch_threshold": 0.001,
            "market_orders_allowed": false,
            "max_concurrent_api_requests": null,
            "max_disk_candles_per_symbol_per_tf": 2000000,
            "max_memory_candles_per_symbol": 200000,
            "max_n_cancellations_per_batch": 5,
            "max_n_creations_per_batch": 3,
            "max_n_restarts_per_day": 10,
            "max_ohlcv_fetches_per_minute": 30,
            "max_realized_loss_pct": 1,
            "max_warmup_minutes": 0,
            "minimum_coin_age_days": 0,
            "forager_score_hysteresis_pct": 0.005,
            "order_match_tolerance_pct": 0.0002,
            "pnls_max_lookback_days": 30,
            "recv_window_ms": 5000,
            "strategy_kind": "trailing_martingale",
            "time_in_force": "good_till_cancelled",
            "user": "bybit_01",
            "warmup_concurrency": 0,
            "warmup_jitter_seconds": 30,
            "warmup_ratio": 0.3
        },
        "logging": {
            "backup_count": 5,
            "dir": "logs",
            "level": 1,
            "max_bytes_mb": 10,
            "memory_snapshot_interval_minutes": 30,
            "persist_to_file": true,
            "rotation": false,
            "volume_refresh_info_threshold_seconds": 30
        },
        "monitor": {
            "checkpoint_interval_minutes": 10,
            "compress_rotated_segments": true,
            "emit_completed_candles": true,
            "enabled": true,
            "event_rotation_mb": 128,
            "event_rotation_minutes": 60,
            "include_raw_fill_payloads": false,
            "max_total_bytes": 1073741824,
            "price_tick_min_interval_ms": 500,
            "retain_candles": true,
            "retain_days": 7,
            "retain_fills": true,
            "retain_price_ticks": true,
            "root_dir": "monitor",
            "snapshot_interval_seconds": 1
        },
        "optimize": {
            "backend": "pymoo",
            "bounds": {
                "long": {
                    "forager": {
                        "score_weights_ema_readiness": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volatility": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volume": [
                            0,
                            1,
                            0.01
                        ],
                        "volatility_ema_span_1m": [
                            10,
                            720,
                            1
                        ],
                        "volume_drop_pct": [
                            0.4,
                            1,
                            0.01
                        ],
                        "volume_ema_span_1m": [
                            360,
                            2880,
                            10
                        ]
                    },
                    "hsl": {
                        "cooldown_minutes_after_red": [
                            1,
                            2880,
                            10
                        ],
                        "ema_span_minutes": [
                            1,
                            2880,
                            10
                        ],
                        "red_threshold": [
                            0.01,
                            0.12,
                            0.001
                        ]
                    },
                    "risk": {
                        "entry_cooldown_minutes": [
                            0,
                            60,
                            0.1
                        ],
                        "n_positions": [
                            10,
                            10,
                            1
                        ],
                        "total_wallet_exposure_limit": [
                            1.25,
                            1.25
                        ],
                        "total_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ],
                        "we_excess_allowance_pct": [
                            0,
                            0.3,
                            0.01
                        ],
                        "position_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ]
                    },
                    "strategy": {
                        "trailing_martingale": {
                            "volatility_ema_span_1h": [
                                672,
                                2016,
                                1
                            ],
                            "volatility_ema_span_1m": [
                                5,
                                720,
                                1
                            ],
                            "entry": {
                                "ema_span_0": [
                                    200,
                                    1440,
                                    10
                                ],
                                "ema_span_1": [
                                    200,
                                    1440,
                                    10
                                ],
                                "double_down_factor": [
                                    0.5,
                                    1,
                                    0.01
                                ],
                                "initial_ema_dist": [
                                    -0.01,
                                    0.01,
                                    0.0001
                                ],
                                "initial_qty_pct": [
                                    0.01,
                                    0.03,
                                    0.0001
                                ],
                                "threshold_base_pct": [
                                    0,
                                    0.04,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            },
                            "close": {
                                "qty_pct": [
                                    0.05,
                                    1,
                                    0.01
                                ],
                                "threshold_base_pct": [
                                    -0.02,
                                    0.02,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    -0.05,
                                    0.05,
                                    0.0001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            }
                        }
                    },
                    "unstuck": {
                        "ema_span_0": [
                            770,
                            770
                        ],
                        "ema_span_1": [
                            210,
                            210
                        ],
                        "close_pct": [
                            0.05,
                            0.12,
                            0.001
                        ],
                        "ema_dist": [
                            -0.2,
                            -0.07,
                            0.0001
                        ],
                        "loss_allowance_pct": [
                            0.005,
                            0.025,
                            0.0001
                        ],
                        "threshold": [
                            0.4,
                            0.9,
                            0.001
                        ]
                    }
                },
                "short": {
                    "forager": {
                        "score_weights_ema_readiness": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volatility": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volume": [
                            0,
                            1,
                            0.01
                        ],
                        "volatility_ema_span_1m": [
                            10,
                            720,
                            1
                        ],
                        "volume_drop_pct": [
                            0.4,
                            1,
                            0.01
                        ],
                        "volume_ema_span_1m": [
                            360,
                            2880,
                            10
                        ]
                    },
                    "hsl": {
                        "cooldown_minutes_after_red": [
                            1,
                            2880,
                            10
                        ],
                        "ema_span_minutes": [
                            1,
                            2880,
                            10
                        ],
                        "red_threshold": [
                            0.01,
                            0.12,
                            0.001
                        ]
                    },
                    "risk": {
                        "entry_cooldown_minutes": [
                            0,
                            60,
                            0.1
                        ],
                        "n_positions": [
                            10,
                            10,
                            1
                        ],
                        "total_wallet_exposure_limit": [
                            0,
                            0
                        ],
                        "total_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ],
                        "we_excess_allowance_pct": [
                            0,
                            0.3,
                            0.01
                        ],
                        "position_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ]
                    },
                    "strategy": {
                        "trailing_martingale": {
                            "volatility_ema_span_1h": [
                                672,
                                2016,
                                1
                            ],
                            "volatility_ema_span_1m": [
                                5,
                                720,
                                1
                            ],
                            "entry": {
                                "ema_span_0": [
                                    200,
                                    1440,
                                    10
                                ],
                                "ema_span_1": [
                                    200,
                                    1440,
                                    10
                                ],
                                "double_down_factor": [
                                    0.5,
                                    1,
                                    0.01
                                ],
                                "initial_ema_dist": [
                                    -0.01,
                                    0.01,
                                    0.0001
                                ],
                                "initial_qty_pct": [
                                    0.01,
                                    0.03,
                                    0.0001
                                ],
                                "threshold_base_pct": [
                                    0,
                                    0.04,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            },
                            "close": {
                                "qty_pct": [
                                    0.05,
                                    1,
                                    0.01
                                ],
                                "threshold_base_pct": [
                                    -0.02,
                                    0.02,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    -0.05,
                                    0.05,
                                    0.0001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            }
                        }
                    },
                    "unstuck": {
                        "ema_span_0": [
                            100,
                            100
                        ],
                        "ema_span_1": [
                            100,
                            100
                        ],
                        "close_pct": [
                            0.05,
                            0.12,
                            0.001
                        ],
                        "ema_dist": [
                            -0.2,
                            -0.07,
                            0.0001
                        ],
                        "loss_allowance_pct": [
                            0.005,
                            0.025,
                            0.0001
                        ],
                        "threshold": [
                            0.4,
                            0.9,
                            0.001
                        ]
                    }
                }
            },
            "compress_results_file": true,
            "crossover_eta": 20,
            "crossover_probability": 0.64,
            "enable_overrides": [],
            "fixed_params": [],
            "fixed_runtime_overrides": {
                "bot.long.hsl.no_restart_drawdown_threshold": 1,
                "bot.short.hsl.no_restart_drawdown_threshold": 1
            },
            "iters": 500000,
            "limits": [
                {
                    "metric": "drawdown_worst_btc",
                    "penalize_if": "greater_than",
                    "value": 0.9
                },
                {
                    "metric": "drawdown_worst_usd",
                    "penalize_if": "greater_than",
                    "value": 0.9
                },
                {
                    "metric": "loss_profit_ratio",
                    "penalize_if": "greater_than",
                    "value": 0.6
                },
                {
                    "metric": "adg_pnl",
                    "penalize_if": "less_than",
                    "reducer": "mean",
                    "value": 0.0009
                },
                {
                    "metric": "peak_recovery_hours_pnl",
                    "penalize_if": "greater_than",
                    "value": 1344
                },
                {
                    "metric": "position_held_hours_max",
                    "penalize_if": "greater_than",
                    "value": 1344
                },
                {
                    "metric": "position_unchanged_hours_max",
                    "penalize_if": "greater_than",
                    "value": 840
                }
            ],
            "mutation_eta": 20,
            "mutation_indpb": 0.05,
            "mutation_probability": 0.34,
            "n_cpus": 16,
            "offspring_multiplier": 1,
            "pareto_max_size": 250,
            "population_size": 250,
            "pymoo": {
                "algorithm": "auto",
                "algorithms": {
                    "nsga2": {},
                    "nsga3": {
                        "ref_dirs": {
                            "method": "das_dennis",
                            "n_partitions": "auto"
                        }
                    }
                },
                "shared": {
                    "crossover_eta": 20,
                    "crossover_prob_var": 0.64,
                    "eliminate_duplicates": true,
                    "mutation_eta": 20,
                    "mutation_prob": 0.05,
                    "mutation_prob_per_variable": "auto"
                }
            },
            "round_to_n_significant_digits": 3,
            "scoring": [
                {
                    "goal": "max",
                    "metric": "adg_pnl"
                },
                {
                    "goal": "max",
                    "metric": "mdg_pnl"
                },
                {
                    "goal": "min",
                    "metric": "loss_profit_ratio"
                },
                {
                    "goal": "min",
                    "metric": "peak_recovery_hours_pnl"
                },
                {
                    "goal": "min",
                    "metric": "position_held_hours_max"
                },
                {
                    "goal": "min",
                    "metric": "position_unchanged_hours_max"
                },
                {
                    "goal": "max",
                    "metric": "volume_pct_per_day_avg_w"
                },
                {
                    "goal": "max",
                    "metric": "entry_initial_balance_pct_long"
                }
            ],
            "write_all_results": true
        }
    },
    "_coins_sources": {
        "approved_coins": {
            "long": [
                "BTC"
            ],
            "short": []
        },
        "ignored_coins": {
            "long": [],
            "short": []
        }
    },
    "_transform_log": [
        {
            "step": "normalize_config",
            "ts_ms": 1790895979139,
            "details": {
                "live_only": false,
                "base_config_path": "",
                "flavor": "current",
                "changes": [
                    {
                        "action": "add",
                        "path": "bot.long.hsl",
                        "value": {
                            "__dict__": {}
                        }
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.cooldown_minutes_after_red",
                        "value": 2160.0
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.ema_span_minutes",
                        "value": 720.0
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.enabled",
                        "value": false
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.no_restart_drawdown_threshold",
                        "value": 1
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.orange_tier_mode",
                        "value": "tp_only_with_active_entry_cancellation"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.panic_close_order_type",
                        "value": "limit"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.red_threshold",
                        "value": 0.15
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.restart_after_red_policy",
                        "value": "threshold"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.tier_ratios",
                        "value": {
                            "__dict__": {
                                "orange": 0.75,
                                "yellow": 0.5
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "bot.long.risk.total_exposure_enforcer_policy",
                        "value": "reduce_overweight"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.risk.total_exposure_entry_gate_enabled",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "bot.long.risk.we_excess_allowance_mode",
                        "value": "bounded"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.unstuck.ema_gating_enabled",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "bot.long.strategy.trailing_martingale.entry.ema_gate_mode",
                        "value": "all"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": 0.01,
                                "ema_span_0": 200.0,
                                "ema_span_1": 800.0,
                                "entry_double_down_factor": 0.0,
                                "offset": 0.002,
                                "offset_volatility_ema_span_1m": 60.0,
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "bot.long.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": 385.0,
                                "ema_span_1": 620.0,
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": 1.39,
                                        "grid_spacing_pct": 0.02312,
                                        "grid_spacing_we_weight": 0.6766,
                                        "grid_spacing_volatility_weight": 17.8,
                                        "initial_ema_dist": 0.0078,
                                        "initial_qty_pct": 0.0122,
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": 0.01041,
                                        "grid_markup_end": 0.00241,
                                        "grid_qty_pct": 0.88,
                                        "trailing_grid_ratio": -0.07,
                                        "trailing_qty_pct": 0.89,
                                        "trailing_retracement_pct": 0.00413,
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "bot.short.hsl.restart_after_red_policy",
                        "value": "threshold"
                    },
                    {
                        "action": "add",
                        "path": "bot.short.risk.total_exposure_enforcer_policy",
                        "value": "reduce_overweight"
                    },
                    {
                        "action": "add",
                        "path": "bot.short.risk.total_exposure_entry_gate_enabled",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "bot.short.risk.we_excess_allowance_mode",
                        "value": "bounded"
                    },
                    {
                        "action": "add",
                        "path": "bot.short.unstuck.ema_gating_enabled",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "bot.short.strategy.trailing_martingale.entry.ema_gate_mode",
                        "value": "all"
                    },
                    {
                        "action": "add",
                        "path": "bot.short.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": 0.01,
                                "ema_span_0": 200.0,
                                "ema_span_1": 800.0,
                                "entry_double_down_factor": 0.0,
                                "offset": 0.002,
                                "offset_volatility_ema_span_1m": 60.0,
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "bot.short.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": 300.0,
                                "ema_span_1": 700.0,
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": 1.0,
                                        "grid_spacing_pct": 0.02,
                                        "grid_spacing_we_weight": 1.0,
                                        "grid_spacing_volatility_weight": 10.0,
                                        "initial_ema_dist": 0.01,
                                        "initial_qty_pct": 0.01,
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": 0.00402,
                                        "grid_markup_end": 0.00223,
                                        "grid_qty_pct": 0.5,
                                        "trailing_grid_ratio": -0.03,
                                        "trailing_qty_pct": 0.5,
                                        "trailing_retracement_pct": 0.005,
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "optimize.bounds.long.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": [
                                    0.001,
                                    0.05,
                                    0.0001
                                ],
                                "ema_span_0": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry_double_down_factor": [
                                    0.0,
                                    2.0,
                                    0.01
                                ],
                                "offset": [
                                    0.0,
                                    0.05,
                                    0.0001
                                ],
                                "offset_volatility_ema_span_1m": [
                                    5.0,
                                    720.0,
                                    1.0
                                ],
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "optimize.bounds.long.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": [
                                            0.0,
                                            2.0,
                                            0.01
                                        ],
                                        "grid_spacing_pct": [
                                            0.001,
                                            0.03,
                                            0.0001
                                        ],
                                        "grid_spacing_we_weight": [
                                            0.0,
                                            10.0,
                                            0.001
                                        ],
                                        "grid_spacing_volatility_weight": [
                                            0.0,
                                            50.0,
                                            0.01
                                        ],
                                        "initial_ema_dist": [
                                            -0.1,
                                            0.02,
                                            0.0001
                                        ],
                                        "initial_qty_pct": [
                                            0.005,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": [
                                            0.0015,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_markup_end": [
                                            -0.1,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_grid_ratio": [
                                            -1.0,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_retracement_pct": [
                                            0.0,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "optimize.bounds.short.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": [
                                    0.001,
                                    0.05,
                                    0.0001
                                ],
                                "ema_span_0": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry_double_down_factor": [
                                    0.0,
                                    2.0,
                                    0.01
                                ],
                                "offset": [
                                    0.0,
                                    0.05,
                                    0.0001
                                ],
                                "offset_volatility_ema_span_1m": [
                                    5.0,
                                    720.0,
                                    1.0
                                ],
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "optimize.bounds.short.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": [
                                            0.0,
                                            2.0,
                                            0.01
                                        ],
                                        "grid_spacing_pct": [
                                            0.001,
                                            0.03,
                                            0.0001
                                        ],
                                        "grid_spacing_we_weight": [
                                            0.0,
                                            10.0,
                                            0.001
                                        ],
                                        "grid_spacing_volatility_weight": [
                                            0.0,
                                            50.0,
                                            0.01
                                        ],
                                        "initial_ema_dist": [
                                            -0.1,
                                            0.02,
                                            0.0001
                                        ],
                                        "initial_qty_pct": [
                                            0.005,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": [
                                            0.0015,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_markup_end": [
                                            -0.1,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_grid_ratio": [
                                            -1.0,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_retracement_pct": [
                                            0.0,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "backtest.hsl_detailed_report",
                        "value": false
                    },
                    {
                        "action": "add",
                        "path": "backtest.hlcvs_data_dir",
                        "value": null
                    },
                    {
                        "action": "add",
                        "path": "backtest.hlcvs_data_override_mode",
                        "value": "intersection"
                    },
                    {
                        "action": "add",
                        "path": "backtest.market_settings",
                        "value": {
                            "__dict__": {
                                "overrides": {
                                    "__dict__": {}
                                },
                                "overrides_by_exchange": {
                                    "__dict__": {}
                                }
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "backtest.offline",
                        "value": false
                    },
                    {
                        "action": "add",
                        "path": "live.custom_endpoints_path",
                        "value": null
                    },
                    {
                        "action": "add",
                        "path": "live.defer_broad_candle_warmup",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "live.enable_forager_ws_candles",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "live.exchange_symbol_unavailable_cooldown_hours",
                        "value": 6.0
                    },
                    {
                        "action": "add",
                        "path": "live.fee_conversion_max_age_ms",
                        "value": 86400000
                    },
                    {
                        "action": "add",
                        "path": "live.fee_pct_fallback",
                        "value": 0.0002
                    },
                    {
                        "action": "add",
                        "path": "live.fee_pct_sanity_abs_max",
                        "value": 0.001
                    },
                    {
                        "action": "add",
                        "path": "live.fills_confirmation_overlap_minutes",
                        "value": 60
                    },
                    {
                        "action": "add",
                        "path": "live.fills_recent_overlap_minutes",
                        "value": 10
                    },
                    {
                        "action": "add",
                        "path": "live.forager_ws_candle_rest_audit_minutes",
                        "value": 30
                    },
                    {
                        "action": "add",
                        "path": "live.force_cold_startup",
                        "value": false
                    },
                    {
                        "action": "add",
                        "path": "live.hsl_accept_incomplete_history",
                        "value": false
                    },
                    {
                        "action": "add",
                        "path": "live.hsl_unavailable_grace_seconds",
                        "value": 120.0
                    },
                    {
                        "action": "add",
                        "path": "live.limit_order_create_max_market_dist_pct",
                        "value": 0.8
                    },
                    {
                        "action": "add",
                        "path": "live.market_snapshot_ticker_strategy",
                        "value": "auto"
                    },
                    {
                        "action": "add",
                        "path": "live.max_active_candle_tail_gap_minutes",
                        "value": 10
                    },
                    {
                        "action": "add",
                        "path": "live.max_forager_candle_refresh_seconds",
                        "value": 45
                    },
                    {
                        "action": "add",
                        "path": "live.max_forager_candle_staleness_minutes",
                        "value": null
                    },
                    {
                        "action": "add",
                        "path": "live.order_replacement_churn_gate_activation_count",
                        "value": 10
                    },
                    {
                        "action": "add",
                        "path": "live.order_replacement_churn_gate_market_dist_pct",
                        "value": 0.005
                    },
                    {
                        "action": "add",
                        "path": "live.order_replacement_churn_gate_stability_minutes",
                        "value": 2.0
                    },
                    {
                        "action": "add",
                        "path": "live.order_replacement_churn_gate_window_minutes",
                        "value": 10.0
                    },
                    {
                        "action": "add",
                        "path": "live.risk_input_max_attempts",
                        "value": 10
                    },
                    {
                        "action": "add",
                        "path": "live.startup_phase_budgets",
                        "value": {
                            "__dict__": {}
                        }
                    },
                    {
                        "action": "add",
                        "path": "logging.live_event_debug_profiles",
                        "value": []
                    },
                    {
                        "action": "add",
                        "path": "optimize.objective_scenario",
                        "value": null
                    },
                    {
                        "action": "add",
                        "path": "optimize.seed",
                        "value": null
                    },
                    {
                        "action": "add",
                        "path": "optimize.gpu",
                        "value": {
                            "__dict__": {
                                "auto_lean_parallelism": true,
                                "batch_size": null,
                                "max_dispatch_candidate_bars": null,
                                "checkpoint_interval_seconds": 5.0,
                                "drift_halt": 0.6,
                                "drift_rank_halt": null,
                                "...": "10 more keys"
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "live.base_config_path",
                        "value": ""
                    },
                    {
                        "action": "remove",
                        "path": "backtest.max_warmup_minutes",
                        "value": 0
                    },
                    {
                        "action": "remove",
                        "path": "bot.long.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": 0.01,
                                "ema_span_0": 200.0,
                                "ema_span_1": 800.0,
                                "entry_double_down_factor": 0.0,
                                "offset": 0.002,
                                "offset_psize_weight": 0.1,
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "bot.long.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "close": {
                                    "__dict__": {
                                        "grid_markup_end": 0.00241,
                                        "grid_markup_start": 0.01041,
                                        "grid_qty_pct": 0.88,
                                        "trailing_grid_ratio": -0.07,
                                        "trailing_qty_pct": 0.89,
                                        "trailing_retracement_pct": 0.00413,
                                        "...": "1 more keys"
                                    }
                                },
                                "ema_span_0": 385.0,
                                "ema_span_1": 620.0,
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": 1.39,
                                        "grid_spacing_pct": 0.02312,
                                        "grid_spacing_volatility_weight": 17.8,
                                        "grid_spacing_we_weight": 0.6766,
                                        "initial_ema_dist": 0.0078,
                                        "initial_qty_pct": 0.0122,
                                        "...": "9 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "bot.short.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": 0.01,
                                "ema_span_0": 200.0,
                                "ema_span_1": 800.0,
                                "entry_double_down_factor": 0.0,
                                "offset": 0.002,
                                "offset_psize_weight": 0.1,
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "bot.short.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "close": {
                                    "__dict__": {
                                        "grid_markup_end": 0.00223,
                                        "grid_markup_start": 0.00402,
                                        "grid_qty_pct": 0.5,
                                        "trailing_grid_ratio": -0.03,
                                        "trailing_qty_pct": 0.5,
                                        "trailing_retracement_pct": 0.005,
                                        "...": "1 more keys"
                                    }
                                },
                                "ema_span_0": 300.0,
                                "ema_span_1": 700.0,
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": 1.0,
                                        "grid_spacing_pct": 0.02,
                                        "grid_spacing_volatility_weight": 10.0,
                                        "grid_spacing_we_weight": 1.0,
                                        "initial_ema_dist": 0.01,
                                        "initial_qty_pct": 0.01,
                                        "...": "9 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "optimize.bounds.long.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": [
                                    0.001,
                                    0.05,
                                    0.0001
                                ],
                                "ema_span_0": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry_double_down_factor": [
                                    0.0,
                                    2.0,
                                    0.01
                                ],
                                "offset": [
                                    0.0,
                                    0.05,
                                    0.0001
                                ],
                                "offset_volatility_ema_span_1m": [
                                    5.0,
                                    720.0,
                                    1.0
                                ],
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "optimize.bounds.long.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": [
                                            0.0,
                                            2.0,
                                            0.01
                                        ],
                                        "grid_spacing_pct": [
                                            0.001,
                                            0.03,
                                            0.0001
                                        ],
                                        "grid_spacing_we_weight": [
                                            0.0,
                                            10.0,
                                            0.001
                                        ],
                                        "grid_spacing_volatility_weight": [
                                            0.0,
                                            50.0,
                                            0.01
                                        ],
                                        "initial_ema_dist": [
                                            -0.1,
                                            0.02,
                                            0.0001
                                        ],
                                        "initial_qty_pct": [
                                            0.005,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": [
                                            0.0015,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_markup_end": [
                                            -0.1,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_grid_ratio": [
                                            -1.0,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_retracement_pct": [
                                            0.0,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "optimize.bounds.short.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": [
                                    0.001,
                                    0.05,
                                    0.0001
                                ],
                                "ema_span_0": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry_double_down_factor": [
                                    0.0,
                                    2.0,
                                    0.01
                                ],
                                "offset": [
                                    0.0,
                                    0.05,
                                    0.0001
                                ],
                                "offset_volatility_ema_span_1m": [
                                    5.0,
                                    720.0,
                                    1.0
                                ],
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "optimize.bounds.short.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": [
                                            0.0,
                                            2.0,
                                            0.01
                                        ],
                                        "grid_spacing_pct": [
                                            0.001,
                                            0.03,
                                            0.0001
                                        ],
                                        "grid_spacing_we_weight": [
                                            0.0,
                                            10.0,
                                            0.001
                                        ],
                                        "grid_spacing_volatility_weight": [
                                            0.0,
                                            50.0,
                                            0.01
                                        ],
                                        "initial_ema_dist": [
                                            -0.1,
                                            0.02,
                                            0.0001
                                        ],
                                        "initial_qty_pct": [
                                            0.005,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": [
                                            0.0015,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_markup_end": [
                                            -0.1,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_grid_ratio": [
                                            -1.0,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_retracement_pct": [
                                            0.0,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }
    ]
}```

# 11. ETH 配置
```json
{
    "backtest": {
        "balance_sample_divider": 60,
        "base_dir": "backtests",
        "btc_collateral_cap": 0.0,
        "btc_collateral_ltv_cap": null,
        "candle_interval_minutes": 1,
        "coin_sources": {},
        "compress_cache": true,
        "dynamic_wel_by_tradability": true,
        "end_date": "2026-10-01",
        "exchanges": [
            "binance"
        ],
        "filter_by_min_effective_cost": false,
        "gap_tolerance_ohlcvs_minutes": 120,
        "liquidation_threshold": 0.05,
        "maker_fee_override": 0.0004,
        "market_order_slippage_pct": 0.0005,
        "limit_order_fill_buffer_pct": 0,
        "market_settings_sources": {},
        "ohlcv_source_dir": "/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/caches/ft_source",
        "scenarios": [
            {
                "label": "ETH_recommended_long"
            }
        ],
        "start_date": "2019-11-28",
        "starting_balance": 100000,
        "suite_enabled": false,
        "taker_fee_override": null,
        "visible_metrics": null,
        "volume_normalization": true,
        "reducer": {
            "default": "mean",
            "drawdown_worst_hsl": "max",
            "drawdown_worst_mean_1pct_hsl": "max",
            "peak_recovery_hours_hsl": "max",
            "position_held_hours_max": "max"
        },
        "hsl_detailed_report": false,
        "hlcvs_data_dir": null,
        "hlcvs_data_override_mode": "intersection",
        "market_settings": {
            "overrides": {},
            "overrides_by_exchange": {}
        },
        "offline": false
    },
    "bot": {
        "long": {
            "forager": {
                "score_weights": {
                    "ema_readiness": 0.0,
                    "volatility": 1.0,
                    "volume": 0.0
                },
                "volatility_ema_span_1m": 100,
                "volume_drop_pct": 0.884,
                "volume_ema_span_1m": 1660
            },
            "hsl": {
                "cooldown_minutes_after_red": 2160,
                "ema_span_minutes": 720,
                "enabled": false,
                "no_restart_drawdown_threshold": 1,
                "orange_tier_mode": "tp_only_with_active_entry_cancellation",
                "panic_close_order_type": "limit",
                "red_threshold": 0.15,
                "restart_after_red_policy": "threshold",
                "tier_ratios": {
                    "orange": 0.75,
                    "yellow": 0.5
                }
            },
            "risk": {
                "entry_cooldown_minutes": 0,
                "n_positions": 1,
                "position_exposure_enforcer_enabled": true,
                "position_exposure_enforcer_threshold": 0.98,
                "total_exposure_enforcer_enabled": true,
                "total_exposure_enforcer_policy": "reduce_overweight",
                "total_exposure_enforcer_threshold": 0.98,
                "total_exposure_entry_gate_enabled": true,
                "total_wallet_exposure_limit": 1,
                "we_excess_allowance_mode": "bounded",
                "we_excess_allowance_pct": 0
            },
            "strategy": {
                "trailing_martingale": {
                    "close": {
                        "qty_pct": 0.1,
                        "retracement_base_pct": 0,
                        "retracement_volatility_1h_weight": 0,
                        "retracement_volatility_1m_weight": 0,
                        "threshold_base_pct": 0.0055,
                        "threshold_volatility_1h_weight": 1.0,
                        "threshold_volatility_1m_weight": 0,
                        "threshold_we_weight": -0.004
                    },
                    "entry": {
                        "double_down_factor": 0.7,
                        "ema_gate_mode": "all",
                        "ema_span_0": 770,
                        "ema_span_1": 210,
                        "initial_ema_dist": -0.0115,
                        "initial_qty_pct": 0.017,
                        "retracement_base_pct": 0,
                        "retracement_volatility_1h_weight": 0,
                        "retracement_volatility_1m_weight": 0,
                        "retracement_we_weight": 0,
                        "threshold_base_pct": 0.024,
                        "threshold_volatility_1h_weight": 2.2,
                        "threshold_volatility_1m_weight": 0,
                        "threshold_we_weight": 0.0
                    },
                    "volatility_ema_span_1h": 1690,
                    "volatility_ema_span_1m": 60
                }
            },
            "unstuck": {
                "close_pct": 0.007,
                "ema_dist": -0.075,
                "ema_gating_enabled": true,
                "ema_span_0": 770,
                "ema_span_1": 210,
                "enabled": true,
                "loss_allowance_pct": 0.008,
                "threshold": 0.8
            }
        },
        "short": {
            "forager": {
                "score_weights": {
                    "ema_readiness": 0.0,
                    "volatility": 1.0,
                    "volume": 0.0
                },
                "volatility_ema_span_1m": 10,
                "volume_drop_pct": 0.5,
                "volume_ema_span_1m": 360
            },
            "hsl": {
                "cooldown_minutes_after_red": 1440.0,
                "ema_span_minutes": 60.0,
                "enabled": true,
                "no_restart_drawdown_threshold": 1,
                "orange_tier_mode": "tp_only_with_active_entry_cancellation",
                "panic_close_order_type": "market",
                "red_threshold": 0.15,
                "restart_after_red_policy": "threshold",
                "tier_ratios": {
                    "orange": 0.75,
                    "yellow": 0.5
                }
            },
            "risk": {
                "entry_cooldown_minutes": 0,
                "n_positions": 1,
                "position_exposure_enforcer_enabled": true,
                "position_exposure_enforcer_threshold": 0.95,
                "total_exposure_enforcer_enabled": true,
                "total_exposure_enforcer_policy": "reduce_overweight",
                "total_exposure_enforcer_threshold": 0.95,
                "total_exposure_entry_gate_enabled": true,
                "total_wallet_exposure_limit": 0,
                "we_excess_allowance_mode": "bounded",
                "we_excess_allowance_pct": 0
            },
            "strategy": {
                "trailing_martingale": {
                    "close": {
                        "qty_pct": 0.1,
                        "retracement_base_pct": 0,
                        "retracement_volatility_1h_weight": 0,
                        "retracement_volatility_1m_weight": 0,
                        "threshold_base_pct": 0.006,
                        "threshold_volatility_1h_weight": 1,
                        "threshold_volatility_1m_weight": 0,
                        "threshold_we_weight": -0.004
                    },
                    "entry": {
                        "double_down_factor": 0.5,
                        "ema_gate_mode": "all",
                        "ema_span_0": 100,
                        "ema_span_1": 100,
                        "initial_ema_dist": -0.01,
                        "initial_qty_pct": 0.01,
                        "retracement_base_pct": 0,
                        "retracement_volatility_1h_weight": 0,
                        "retracement_volatility_1m_weight": 0,
                        "retracement_we_weight": 0,
                        "threshold_base_pct": 0.025,
                        "threshold_volatility_1h_weight": 1,
                        "threshold_volatility_1m_weight": 0,
                        "threshold_we_weight": 0
                    },
                    "volatility_ema_span_1h": 672,
                    "volatility_ema_span_1m": 60
                }
            },
            "unstuck": {
                "close_pct": 0.001,
                "ema_dist": -0.1,
                "ema_gating_enabled": true,
                "ema_span_0": 100.0,
                "ema_span_1": 100.0,
                "enabled": true,
                "loss_allowance_pct": 0.001,
                "threshold": 0.4
            }
        }
    },
    "coin_overrides": {},
    "config_version": "v8.4.0",
    "live": {
        "approved_coins": {
            "long": [
                "ETH"
            ],
            "short": []
        },
        "auto_gs": true,
        "balance_hysteresis_snap_pct": 0.02,
        "balance_override": null,
        "candle_lock_timeout_seconds": 10,
        "enable_archive_candle_fetch": false,
        "execution_delay_seconds": 2,
        "filter_by_min_effective_cost": true,
        "forced_mode_long": "",
        "forced_mode_short": "",
        "hedge_mode": false,
        "hsl_position_during_cooldown_policy": "panic",
        "hsl_signal_mode": "unified",
        "ignored_coins": {
            "long": [],
            "short": []
        },
        "inactive_coin_candle_ttl_minutes": 10,
        "leverage": 1,
        "margin_mode_preference": "cross",
        "market_order_near_touch_threshold": 0.001,
        "market_orders_allowed": false,
        "max_concurrent_api_requests": null,
        "max_disk_candles_per_symbol_per_tf": 2000000,
        "max_memory_candles_per_symbol": 200000,
        "max_n_cancellations_per_batch": 5,
        "max_n_creations_per_batch": 3,
        "max_n_restarts_per_day": 10,
        "max_ohlcv_fetches_per_minute": 30,
        "max_realized_loss_pct": 1,
        "max_warmup_minutes": 0,
        "minimum_coin_age_days": 0,
        "forager_score_hysteresis_pct": 0.005,
        "order_match_tolerance_pct": 0.0002,
        "pnls_max_lookback_days": 30.0,
        "recv_window_ms": 5000,
        "strategy_kind": "trailing_martingale",
        "time_in_force": "good_till_cancelled",
        "user": "bybit_01",
        "warmup_concurrency": 0,
        "warmup_jitter_seconds": 30,
        "warmup_ratio": 0.3,
        "hsl_engine": "legacy",
        "custom_endpoints_path": null,
        "defer_broad_candle_warmup": true,
        "enable_forager_ws_candles": true,
        "exchange_symbol_unavailable_cooldown_hours": 6.0,
        "fee_conversion_max_age_ms": 86400000,
        "fee_pct_fallback": 0.0002,
        "fee_pct_sanity_abs_max": 0.001,
        "fills_confirmation_overlap_minutes": 60,
        "fills_recent_overlap_minutes": 10,
        "forager_ws_candle_rest_audit_minutes": 30,
        "force_cold_startup": false,
        "hsl_accept_incomplete_history": false,
        "hsl_unavailable_grace_seconds": 120.0,
        "limit_order_create_max_market_dist_pct": 0.8,
        "market_snapshot_ticker_strategy": "auto",
        "max_active_candle_tail_gap_minutes": 10,
        "max_forager_candle_refresh_seconds": 45,
        "max_forager_candle_staleness_minutes": null,
        "order_replacement_churn_gate_activation_count": 10,
        "order_replacement_churn_gate_market_dist_pct": 0.005,
        "order_replacement_churn_gate_stability_minutes": 2.0,
        "order_replacement_churn_gate_window_minutes": 10.0,
        "risk_input_max_attempts": 10,
        "startup_phase_budgets": {},
        "base_config_path": ""
    },
    "logging": {
        "backup_count": 5,
        "dir": "logs",
        "level": 1,
        "max_bytes_mb": 10.0,
        "memory_snapshot_interval_minutes": 30,
        "persist_to_file": true,
        "rotation": false,
        "volume_refresh_info_threshold_seconds": 30,
        "live_event_debug_profiles": []
    },
    "monitor": {
        "checkpoint_interval_minutes": 10.0,
        "compress_rotated_segments": true,
        "emit_completed_candles": true,
        "enabled": true,
        "event_rotation_mb": 128.0,
        "event_rotation_minutes": 60.0,
        "include_raw_fill_payloads": false,
        "max_total_bytes": 1073741824,
        "price_tick_min_interval_ms": 500,
        "retain_candles": true,
        "retain_days": 7.0,
        "retain_fills": true,
        "retain_price_ticks": true,
        "root_dir": "monitor",
        "snapshot_interval_seconds": 1.0
    },
    "optimize": {
        "backend": "pymoo",
        "bounds": {
            "long": {
                "forager": {
                    "score_weights_ema_readiness": [
                        0,
                        1,
                        0.01
                    ],
                    "score_weights_volatility": [
                        0,
                        1,
                        0.01
                    ],
                    "score_weights_volume": [
                        0,
                        1,
                        0.01
                    ],
                    "volatility_ema_span_1m": [
                        10,
                        720,
                        1
                    ],
                    "volume_drop_pct": [
                        0.4,
                        1,
                        0.01
                    ],
                    "volume_ema_span_1m": [
                        360,
                        2880,
                        10
                    ]
                },
                "hsl": {
                    "cooldown_minutes_after_red": [
                        1,
                        2880,
                        10
                    ],
                    "ema_span_minutes": [
                        1,
                        2880,
                        10
                    ],
                    "red_threshold": [
                        0.01,
                        0.12,
                        0.001
                    ]
                },
                "risk": {
                    "entry_cooldown_minutes": [
                        0,
                        60,
                        0.1
                    ],
                    "n_positions": [
                        10,
                        10,
                        1
                    ],
                    "position_exposure_enforcer_threshold": [
                        0.95,
                        1.01,
                        0.001
                    ],
                    "total_exposure_enforcer_threshold": [
                        0.95,
                        1.01,
                        0.001
                    ],
                    "total_wallet_exposure_limit": [
                        1.25,
                        1.25
                    ],
                    "we_excess_allowance_pct": [
                        0,
                        0.3,
                        0.01
                    ]
                },
                "unstuck": {
                    "close_pct": [
                        0.05,
                        0.12,
                        0.001
                    ],
                    "ema_dist": [
                        -0.2,
                        -0.07,
                        0.0001
                    ],
                    "ema_span_0": [
                        770,
                        770
                    ],
                    "ema_span_1": [
                        210,
                        210
                    ],
                    "loss_allowance_pct": [
                        0.005,
                        0.025,
                        0.0001
                    ],
                    "threshold": [
                        0.4,
                        0.9,
                        0.001
                    ]
                },
                "strategy": {
                    "trailing_martingale": {
                        "entry": {
                            "ema_span_0": [
                                200,
                                1440,
                                10
                            ],
                            "ema_span_1": [
                                200,
                                1440,
                                10
                            ],
                            "double_down_factor": [
                                0.5,
                                1,
                                0.01
                            ],
                            "initial_qty_pct": [
                                0.01,
                                0.03,
                                0.0001
                            ],
                            "initial_ema_dist": [
                                -0.01,
                                0.01,
                                0.0001
                            ],
                            "threshold_base_pct": [
                                0,
                                0.04,
                                1e-05
                            ],
                            "threshold_we_weight": [
                                0,
                                5,
                                0.001
                            ],
                            "threshold_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "threshold_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_base_pct": [
                                0,
                                0.015,
                                1e-05
                            ],
                            "retracement_we_weight": [
                                0,
                                5,
                                0.001
                            ],
                            "retracement_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ]
                        },
                        "volatility_ema_span_1h": [
                            672,
                            2016,
                            1
                        ],
                        "volatility_ema_span_1m": [
                            5,
                            720,
                            1
                        ],
                        "close": {
                            "qty_pct": [
                                0.05,
                                1,
                                0.01
                            ],
                            "threshold_base_pct": [
                                -0.02,
                                0.02,
                                1e-05
                            ],
                            "threshold_we_weight": [
                                -0.05,
                                0.05,
                                0.0001
                            ],
                            "threshold_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "threshold_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_base_pct": [
                                0,
                                0.015,
                                1e-05
                            ],
                            "retracement_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ]
                        }
                    }
                }
            },
            "short": {
                "forager": {
                    "score_weights_ema_readiness": [
                        0,
                        1,
                        0.01
                    ],
                    "score_weights_volatility": [
                        0,
                        1,
                        0.01
                    ],
                    "score_weights_volume": [
                        0,
                        1,
                        0.01
                    ],
                    "volatility_ema_span_1m": [
                        10,
                        720,
                        1
                    ],
                    "volume_drop_pct": [
                        0.4,
                        1,
                        0.01
                    ],
                    "volume_ema_span_1m": [
                        360,
                        2880,
                        10
                    ]
                },
                "hsl": {
                    "cooldown_minutes_after_red": [
                        1,
                        2880,
                        10
                    ],
                    "ema_span_minutes": [
                        1,
                        2880,
                        10
                    ],
                    "red_threshold": [
                        0.01,
                        0.12,
                        0.001
                    ]
                },
                "risk": {
                    "entry_cooldown_minutes": [
                        0,
                        60,
                        0.1
                    ],
                    "n_positions": [
                        10,
                        10,
                        1
                    ],
                    "position_exposure_enforcer_threshold": [
                        0.95,
                        1.01,
                        0.001
                    ],
                    "total_exposure_enforcer_threshold": [
                        0.95,
                        1.01,
                        0.001
                    ],
                    "total_wallet_exposure_limit": [
                        0,
                        0
                    ],
                    "we_excess_allowance_pct": [
                        0,
                        0.3,
                        0.01
                    ]
                },
                "unstuck": {
                    "close_pct": [
                        0.05,
                        0.12,
                        0.001
                    ],
                    "ema_dist": [
                        -0.2,
                        -0.07,
                        0.0001
                    ],
                    "ema_span_0": [
                        100,
                        100
                    ],
                    "ema_span_1": [
                        100,
                        100
                    ],
                    "loss_allowance_pct": [
                        0.005,
                        0.025,
                        0.0001
                    ],
                    "threshold": [
                        0.4,
                        0.9,
                        0.001
                    ]
                },
                "strategy": {
                    "trailing_martingale": {
                        "entry": {
                            "ema_span_0": [
                                200,
                                1440,
                                10
                            ],
                            "ema_span_1": [
                                200,
                                1440,
                                10
                            ],
                            "double_down_factor": [
                                0.5,
                                1,
                                0.01
                            ],
                            "initial_qty_pct": [
                                0.01,
                                0.03,
                                0.0001
                            ],
                            "initial_ema_dist": [
                                -0.01,
                                0.01,
                                0.0001
                            ],
                            "threshold_base_pct": [
                                0,
                                0.04,
                                1e-05
                            ],
                            "threshold_we_weight": [
                                0,
                                5,
                                0.001
                            ],
                            "threshold_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "threshold_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_base_pct": [
                                0,
                                0.015,
                                1e-05
                            ],
                            "retracement_we_weight": [
                                0,
                                5,
                                0.001
                            ],
                            "retracement_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ]
                        },
                        "volatility_ema_span_1h": [
                            672,
                            2016,
                            1
                        ],
                        "volatility_ema_span_1m": [
                            5,
                            720,
                            1
                        ],
                        "close": {
                            "qty_pct": [
                                0.05,
                                1,
                                0.01
                            ],
                            "threshold_base_pct": [
                                -0.02,
                                0.02,
                                1e-05
                            ],
                            "threshold_we_weight": [
                                -0.05,
                                0.05,
                                0.0001
                            ],
                            "threshold_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "threshold_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_base_pct": [
                                0,
                                0.015,
                                1e-05
                            ],
                            "retracement_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ]
                        }
                    }
                }
            }
        },
        "compress_results_file": true,
        "crossover_eta": 20,
        "crossover_probability": 0.64,
        "enable_overrides": [],
        "fixed_params": [],
        "fixed_runtime_overrides": {
            "bot.long.hsl.no_restart_drawdown_threshold": 1,
            "bot.short.hsl.no_restart_drawdown_threshold": 1
        },
        "iters": 500000,
        "limits": [
            {
                "metric": "drawdown_worst_btc",
                "penalize_if": "greater_than",
                "value": 0.9
            },
            {
                "metric": "drawdown_worst_usd",
                "penalize_if": "greater_than",
                "value": 0.9
            },
            {
                "metric": "loss_profit_ratio",
                "penalize_if": "greater_than",
                "value": 0.6
            },
            {
                "metric": "adg_pnl",
                "penalize_if": "less_than",
                "reducer": "mean",
                "value": 0.0009
            },
            {
                "metric": "peak_recovery_hours_pnl",
                "penalize_if": "greater_than",
                "value": 1344
            },
            {
                "metric": "position_held_hours_max",
                "penalize_if": "greater_than",
                "value": 1344
            },
            {
                "metric": "position_unchanged_hours_max",
                "penalize_if": "greater_than",
                "value": 840
            }
        ],
        "mutation_eta": 20,
        "mutation_indpb": 0.05,
        "mutation_probability": 0.34,
        "n_cpus": 16,
        "offspring_multiplier": 1,
        "pareto_max_size": 250,
        "population_size": 250,
        "pymoo": {
            "algorithm": "auto",
            "shared": {
                "crossover_eta": 20.0,
                "crossover_prob_var": 0.64,
                "mutation_eta": 20.0,
                "mutation_prob": 0.05,
                "mutation_prob_per_variable": "auto",
                "eliminate_duplicates": true
            },
            "algorithms": {
                "nsga2": {},
                "nsga3": {
                    "ref_dirs": {
                        "method": "das_dennis",
                        "n_partitions": "auto"
                    }
                }
            }
        },
        "round_to_n_significant_digits": 3,
        "scoring": [
            {
                "metric": "adg_pnl",
                "goal": "max"
            },
            {
                "metric": "mdg_pnl",
                "goal": "max"
            },
            {
                "metric": "loss_profit_ratio",
                "goal": "min"
            },
            {
                "metric": "peak_recovery_hours_pnl",
                "goal": "min"
            },
            {
                "metric": "position_held_hours_max",
                "goal": "min"
            },
            {
                "metric": "position_unchanged_hours_max",
                "goal": "min"
            },
            {
                "metric": "volume_pct_per_day_avg_w",
                "goal": "max"
            },
            {
                "metric": "entry_initial_balance_pct_long",
                "goal": "max"
            }
        ],
        "write_all_results": true,
        "objective_scenario": null,
        "seed": null,
        "gpu": {
            "auto_lean_parallelism": true,
            "batch_size": null,
            "max_dispatch_candidate_bars": null,
            "checkpoint_interval_seconds": 5.0,
            "drift_halt": 0.6,
            "drift_rank_halt": null,
            "drift_objective_tolerance": 1e-06,
            "drift_min_samples": 32,
            "drift_probes": 4,
            "drift_window": 128,
            "exact_workers": 0,
            "max_pending_exact": 0,
            "population_size": null,
            "seed_bootstrap": {
                "max_exact": 128,
                "mode": "auto"
            },
            "screening": {
                "scenarios": [],
                "survival_fraction": 0.1,
                "min_survivors": 64
            },
            "validate_per_generation": 8
        }
    },
    "_raw": {
        "backtest": {
            "reducer": {
                "default": "mean",
                "drawdown_worst_hsl": "max",
                "drawdown_worst_mean_1pct_hsl": "max",
                "peak_recovery_hours_hsl": "max",
                "position_held_hours_max": "max"
            },
            "balance_sample_divider": 60,
            "base_dir": "backtests",
            "btc_collateral_cap": 0,
            "btc_collateral_ltv_cap": null,
            "candle_interval_minutes": 1,
            "coin_sources": {},
            "compress_cache": true,
            "dynamic_wel_by_tradability": true,
            "end_date": "now",
            "exchanges": [
                "binance"
            ],
            "filter_by_min_effective_cost": false,
            "gap_tolerance_ohlcvs_minutes": 120,
            "liquidation_threshold": 0.05,
            "maker_fee_override": 0.0004,
            "market_order_slippage_pct": 0.0005,
            "limit_order_fill_buffer_pct": 0,
            "market_settings_sources": {},
            "max_warmup_minutes": 0,
            "ohlcv_source_dir": null,
            "scenarios": [
                {
                    "label": "ETH_normal_osc_long"
                }
            ],
            "start_date": "2019-01-01",
            "starting_balance": 100000,
            "suite_enabled": false,
            "taker_fee_override": null,
            "visible_metrics": null,
            "volume_normalization": true
        },
        "bot": {
            "long": {
                "forager": {
                    "score_weights": {
                        "ema_readiness": 0,
                        "volatility": 1,
                        "volume": 0
                    },
                    "volatility_ema_span_1m": 101,
                    "volume_drop_pct": 0.884,
                    "volume_ema_span_1m": 1660
                },
                "risk": {
                    "entry_cooldown_minutes": 0,
                    "n_positions": 1,
                    "total_wallet_exposure_limit": 1,
                    "total_exposure_enforcer_enabled": true,
                    "total_exposure_enforcer_threshold": 0.99,
                    "we_excess_allowance_pct": 1.64,
                    "position_exposure_enforcer_enabled": true,
                    "position_exposure_enforcer_threshold": 0.99
                },
                "strategy": {
                    "trailing_martingale": {
                        "volatility_ema_span_1h": 1690,
                        "volatility_ema_span_1m": 60,
                        "entry": {
                            "ema_span_0": 770,
                            "ema_span_1": 210,
                            "double_down_factor": 0.74,
                            "initial_ema_dist": -0.0081,
                            "initial_qty_pct": 0.0313,
                            "threshold_base_pct": 0.0256,
                            "threshold_we_weight": 0.135,
                            "threshold_volatility_1h_weight": 2.4,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_we_weight": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        },
                        "close": {
                            "qty_pct": 0.1,
                            "threshold_base_pct": 0.0047,
                            "threshold_we_weight": -0.004,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        }
                    }
                },
                "unstuck": {
                    "ema_span_0": 770,
                    "ema_span_1": 210,
                    "close_pct": 0.00936,
                    "ema_dist": -0.064,
                    "enabled": true,
                    "loss_allowance_pct": 0.00523,
                    "threshold": 0.833
                }
            },
            "short": {
                "forager": {
                    "score_weights": {
                        "ema_readiness": 0,
                        "volatility": 1,
                        "volume": 0
                    },
                    "volatility_ema_span_1m": 10,
                    "volume_drop_pct": 0.5,
                    "volume_ema_span_1m": 360
                },
                "hsl": {
                    "cooldown_minutes_after_red": 0,
                    "ema_span_minutes": 60,
                    "enabled": false,
                    "no_restart_drawdown_threshold": 1,
                    "orange_tier_mode": "tp_only_with_active_entry_cancellation",
                    "panic_close_order_type": "limit",
                    "red_threshold": 0.2,
                    "tier_ratios": {
                        "orange": 0.75,
                        "yellow": 0.5
                    }
                },
                "risk": {
                    "entry_cooldown_minutes": 0,
                    "n_positions": 1,
                    "total_wallet_exposure_limit": 0,
                    "total_exposure_enforcer_enabled": true,
                    "total_exposure_enforcer_threshold": 0.95,
                    "we_excess_allowance_pct": 0,
                    "position_exposure_enforcer_enabled": true,
                    "position_exposure_enforcer_threshold": 0.95
                },
                "strategy": {
                    "trailing_martingale": {
                        "volatility_ema_span_1h": 672,
                        "volatility_ema_span_1m": 60,
                        "entry": {
                            "ema_span_0": 100,
                            "ema_span_1": 100,
                            "double_down_factor": 0.5,
                            "initial_ema_dist": -0.01,
                            "initial_qty_pct": 0.01,
                            "threshold_base_pct": 0.025,
                            "threshold_we_weight": 0,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_we_weight": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        },
                        "close": {
                            "qty_pct": 0.1,
                            "threshold_base_pct": 0.006,
                            "threshold_we_weight": -0.004,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        }
                    }
                },
                "unstuck": {
                    "ema_span_0": 100,
                    "ema_span_1": 100,
                    "close_pct": 0.001,
                    "ema_dist": -0.1,
                    "enabled": true,
                    "loss_allowance_pct": 0.001,
                    "threshold": 0.4
                }
            }
        },
        "coin_overrides": {},
        "config_version": "v8.4.0",
        "live": {
            "approved_coins": {
                "long": [
                    "ETH"
                ],
                "short": []
            },
            "auto_gs": true,
            "balance_hysteresis_snap_pct": 0.02,
            "balance_override": null,
            "candle_lock_timeout_seconds": 10,
            "enable_archive_candle_fetch": false,
            "execution_delay_seconds": 2,
            "filter_by_min_effective_cost": true,
            "forced_mode_long": "",
            "forced_mode_short": "",
            "hedge_mode": false,
            "hsl_position_during_cooldown_policy": "panic",
            "hsl_signal_mode": "unified",
            "ignored_coins": {
                "long": [],
                "short": []
            },
            "inactive_coin_candle_ttl_minutes": 10,
            "leverage": 1,
            "margin_mode_preference": "cross",
            "market_order_near_touch_threshold": 0.001,
            "market_orders_allowed": false,
            "max_concurrent_api_requests": null,
            "max_disk_candles_per_symbol_per_tf": 2000000,
            "max_memory_candles_per_symbol": 200000,
            "max_n_cancellations_per_batch": 5,
            "max_n_creations_per_batch": 3,
            "max_n_restarts_per_day": 10,
            "max_ohlcv_fetches_per_minute": 30,
            "max_realized_loss_pct": 1,
            "max_warmup_minutes": 0,
            "minimum_coin_age_days": 0,
            "forager_score_hysteresis_pct": 0.005,
            "order_match_tolerance_pct": 0.0002,
            "pnls_max_lookback_days": 30,
            "recv_window_ms": 5000,
            "strategy_kind": "trailing_martingale",
            "time_in_force": "good_till_cancelled",
            "user": "bybit_01",
            "warmup_concurrency": 0,
            "warmup_jitter_seconds": 30,
            "warmup_ratio": 0.3
        },
        "logging": {
            "backup_count": 5,
            "dir": "logs",
            "level": 1,
            "max_bytes_mb": 10,
            "memory_snapshot_interval_minutes": 30,
            "persist_to_file": true,
            "rotation": false,
            "volume_refresh_info_threshold_seconds": 30
        },
        "monitor": {
            "checkpoint_interval_minutes": 10,
            "compress_rotated_segments": true,
            "emit_completed_candles": true,
            "enabled": true,
            "event_rotation_mb": 128,
            "event_rotation_minutes": 60,
            "include_raw_fill_payloads": false,
            "max_total_bytes": 1073741824,
            "price_tick_min_interval_ms": 500,
            "retain_candles": true,
            "retain_days": 7,
            "retain_fills": true,
            "retain_price_ticks": true,
            "root_dir": "monitor",
            "snapshot_interval_seconds": 1
        },
        "optimize": {
            "backend": "pymoo",
            "bounds": {
                "long": {
                    "forager": {
                        "score_weights_ema_readiness": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volatility": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volume": [
                            0,
                            1,
                            0.01
                        ],
                        "volatility_ema_span_1m": [
                            10,
                            720,
                            1
                        ],
                        "volume_drop_pct": [
                            0.4,
                            1,
                            0.01
                        ],
                        "volume_ema_span_1m": [
                            360,
                            2880,
                            10
                        ]
                    },
                    "hsl": {
                        "cooldown_minutes_after_red": [
                            1,
                            2880,
                            10
                        ],
                        "ema_span_minutes": [
                            1,
                            2880,
                            10
                        ],
                        "red_threshold": [
                            0.01,
                            0.12,
                            0.001
                        ]
                    },
                    "risk": {
                        "entry_cooldown_minutes": [
                            0,
                            60,
                            0.1
                        ],
                        "n_positions": [
                            10,
                            10,
                            1
                        ],
                        "total_wallet_exposure_limit": [
                            1.25,
                            1.25
                        ],
                        "total_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ],
                        "we_excess_allowance_pct": [
                            0,
                            0.3,
                            0.01
                        ],
                        "position_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ]
                    },
                    "strategy": {
                        "trailing_martingale": {
                            "volatility_ema_span_1h": [
                                672,
                                2016,
                                1
                            ],
                            "volatility_ema_span_1m": [
                                5,
                                720,
                                1
                            ],
                            "entry": {
                                "ema_span_0": [
                                    200,
                                    1440,
                                    10
                                ],
                                "ema_span_1": [
                                    200,
                                    1440,
                                    10
                                ],
                                "double_down_factor": [
                                    0.5,
                                    1,
                                    0.01
                                ],
                                "initial_ema_dist": [
                                    -0.01,
                                    0.01,
                                    0.0001
                                ],
                                "initial_qty_pct": [
                                    0.01,
                                    0.03,
                                    0.0001
                                ],
                                "threshold_base_pct": [
                                    0,
                                    0.04,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            },
                            "close": {
                                "qty_pct": [
                                    0.05,
                                    1,
                                    0.01
                                ],
                                "threshold_base_pct": [
                                    -0.02,
                                    0.02,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    -0.05,
                                    0.05,
                                    0.0001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            }
                        }
                    },
                    "unstuck": {
                        "ema_span_0": [
                            770,
                            770
                        ],
                        "ema_span_1": [
                            210,
                            210
                        ],
                        "close_pct": [
                            0.05,
                            0.12,
                            0.001
                        ],
                        "ema_dist": [
                            -0.2,
                            -0.07,
                            0.0001
                        ],
                        "loss_allowance_pct": [
                            0.005,
                            0.025,
                            0.0001
                        ],
                        "threshold": [
                            0.4,
                            0.9,
                            0.001
                        ]
                    }
                },
                "short": {
                    "forager": {
                        "score_weights_ema_readiness": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volatility": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volume": [
                            0,
                            1,
                            0.01
                        ],
                        "volatility_ema_span_1m": [
                            10,
                            720,
                            1
                        ],
                        "volume_drop_pct": [
                            0.4,
                            1,
                            0.01
                        ],
                        "volume_ema_span_1m": [
                            360,
                            2880,
                            10
                        ]
                    },
                    "hsl": {
                        "cooldown_minutes_after_red": [
                            1,
                            2880,
                            10
                        ],
                        "ema_span_minutes": [
                            1,
                            2880,
                            10
                        ],
                        "red_threshold": [
                            0.01,
                            0.12,
                            0.001
                        ]
                    },
                    "risk": {
                        "entry_cooldown_minutes": [
                            0,
                            60,
                            0.1
                        ],
                        "n_positions": [
                            10,
                            10,
                            1
                        ],
                        "total_wallet_exposure_limit": [
                            0,
                            0
                        ],
                        "total_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ],
                        "we_excess_allowance_pct": [
                            0,
                            0.3,
                            0.01
                        ],
                        "position_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ]
                    },
                    "strategy": {
                        "trailing_martingale": {
                            "volatility_ema_span_1h": [
                                672,
                                2016,
                                1
                            ],
                            "volatility_ema_span_1m": [
                                5,
                                720,
                                1
                            ],
                            "entry": {
                                "ema_span_0": [
                                    200,
                                    1440,
                                    10
                                ],
                                "ema_span_1": [
                                    200,
                                    1440,
                                    10
                                ],
                                "double_down_factor": [
                                    0.5,
                                    1,
                                    0.01
                                ],
                                "initial_ema_dist": [
                                    -0.01,
                                    0.01,
                                    0.0001
                                ],
                                "initial_qty_pct": [
                                    0.01,
                                    0.03,
                                    0.0001
                                ],
                                "threshold_base_pct": [
                                    0,
                                    0.04,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            },
                            "close": {
                                "qty_pct": [
                                    0.05,
                                    1,
                                    0.01
                                ],
                                "threshold_base_pct": [
                                    -0.02,
                                    0.02,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    -0.05,
                                    0.05,
                                    0.0001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            }
                        }
                    },
                    "unstuck": {
                        "ema_span_0": [
                            100,
                            100
                        ],
                        "ema_span_1": [
                            100,
                            100
                        ],
                        "close_pct": [
                            0.05,
                            0.12,
                            0.001
                        ],
                        "ema_dist": [
                            -0.2,
                            -0.07,
                            0.0001
                        ],
                        "loss_allowance_pct": [
                            0.005,
                            0.025,
                            0.0001
                        ],
                        "threshold": [
                            0.4,
                            0.9,
                            0.001
                        ]
                    }
                }
            },
            "compress_results_file": true,
            "crossover_eta": 20,
            "crossover_probability": 0.64,
            "enable_overrides": [],
            "fixed_params": [],
            "fixed_runtime_overrides": {
                "bot.long.hsl.no_restart_drawdown_threshold": 1,
                "bot.short.hsl.no_restart_drawdown_threshold": 1
            },
            "iters": 500000,
            "limits": [
                {
                    "metric": "drawdown_worst_btc",
                    "penalize_if": "greater_than",
                    "value": 0.9
                },
                {
                    "metric": "drawdown_worst_usd",
                    "penalize_if": "greater_than",
                    "value": 0.9
                },
                {
                    "metric": "loss_profit_ratio",
                    "penalize_if": "greater_than",
                    "value": 0.6
                },
                {
                    "metric": "adg_pnl",
                    "penalize_if": "less_than",
                    "reducer": "mean",
                    "value": 0.0009
                },
                {
                    "metric": "peak_recovery_hours_pnl",
                    "penalize_if": "greater_than",
                    "value": 1344
                },
                {
                    "metric": "position_held_hours_max",
                    "penalize_if": "greater_than",
                    "value": 1344
                },
                {
                    "metric": "position_unchanged_hours_max",
                    "penalize_if": "greater_than",
                    "value": 840
                }
            ],
            "mutation_eta": 20,
            "mutation_indpb": 0.05,
            "mutation_probability": 0.34,
            "n_cpus": 16,
            "offspring_multiplier": 1,
            "pareto_max_size": 250,
            "population_size": 250,
            "pymoo": {
                "algorithm": "auto",
                "algorithms": {
                    "nsga2": {},
                    "nsga3": {
                        "ref_dirs": {
                            "method": "das_dennis",
                            "n_partitions": "auto"
                        }
                    }
                },
                "shared": {
                    "crossover_eta": 20,
                    "crossover_prob_var": 0.64,
                    "eliminate_duplicates": true,
                    "mutation_eta": 20,
                    "mutation_prob": 0.05,
                    "mutation_prob_per_variable": "auto"
                }
            },
            "round_to_n_significant_digits": 3,
            "scoring": [
                {
                    "goal": "max",
                    "metric": "adg_pnl"
                },
                {
                    "goal": "max",
                    "metric": "mdg_pnl"
                },
                {
                    "goal": "min",
                    "metric": "loss_profit_ratio"
                },
                {
                    "goal": "min",
                    "metric": "peak_recovery_hours_pnl"
                },
                {
                    "goal": "min",
                    "metric": "position_held_hours_max"
                },
                {
                    "goal": "min",
                    "metric": "position_unchanged_hours_max"
                },
                {
                    "goal": "max",
                    "metric": "volume_pct_per_day_avg_w"
                },
                {
                    "goal": "max",
                    "metric": "entry_initial_balance_pct_long"
                }
            ],
            "write_all_results": true
        }
    },
    "_raw_effective": {
        "backtest": {
            "reducer": {
                "default": "mean",
                "drawdown_worst_hsl": "max",
                "drawdown_worst_mean_1pct_hsl": "max",
                "peak_recovery_hours_hsl": "max",
                "position_held_hours_max": "max"
            },
            "balance_sample_divider": 60,
            "base_dir": "backtests",
            "btc_collateral_cap": 0,
            "btc_collateral_ltv_cap": null,
            "candle_interval_minutes": 1,
            "coin_sources": {},
            "compress_cache": true,
            "dynamic_wel_by_tradability": true,
            "end_date": "now",
            "exchanges": [
                "binance"
            ],
            "filter_by_min_effective_cost": false,
            "gap_tolerance_ohlcvs_minutes": 120,
            "liquidation_threshold": 0.05,
            "maker_fee_override": 0.0004,
            "market_order_slippage_pct": 0.0005,
            "limit_order_fill_buffer_pct": 0,
            "market_settings_sources": {},
            "max_warmup_minutes": 0,
            "ohlcv_source_dir": null,
            "scenarios": [
                {
                    "label": "ETH_normal_osc_long"
                }
            ],
            "start_date": "2019-01-01",
            "starting_balance": 100000,
            "suite_enabled": false,
            "taker_fee_override": null,
            "visible_metrics": null,
            "volume_normalization": true
        },
        "bot": {
            "long": {
                "forager": {
                    "score_weights": {
                        "ema_readiness": 0,
                        "volatility": 1,
                        "volume": 0
                    },
                    "volatility_ema_span_1m": 101,
                    "volume_drop_pct": 0.884,
                    "volume_ema_span_1m": 1660
                },
                "risk": {
                    "entry_cooldown_minutes": 0,
                    "n_positions": 1,
                    "total_wallet_exposure_limit": 1,
                    "total_exposure_enforcer_enabled": true,
                    "total_exposure_enforcer_threshold": 0.99,
                    "we_excess_allowance_pct": 1.64,
                    "position_exposure_enforcer_enabled": true,
                    "position_exposure_enforcer_threshold": 0.99
                },
                "strategy": {
                    "trailing_martingale": {
                        "volatility_ema_span_1h": 1690,
                        "volatility_ema_span_1m": 60,
                        "entry": {
                            "ema_span_0": 770,
                            "ema_span_1": 210,
                            "double_down_factor": 0.74,
                            "initial_ema_dist": -0.0081,
                            "initial_qty_pct": 0.0313,
                            "threshold_base_pct": 0.0256,
                            "threshold_we_weight": 0.135,
                            "threshold_volatility_1h_weight": 2.4,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_we_weight": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        },
                        "close": {
                            "qty_pct": 0.1,
                            "threshold_base_pct": 0.0047,
                            "threshold_we_weight": -0.004,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        }
                    }
                },
                "unstuck": {
                    "ema_span_0": 770,
                    "ema_span_1": 210,
                    "close_pct": 0.00936,
                    "ema_dist": -0.064,
                    "enabled": true,
                    "loss_allowance_pct": 0.00523,
                    "threshold": 0.833
                }
            },
            "short": {
                "forager": {
                    "score_weights": {
                        "ema_readiness": 0,
                        "volatility": 1,
                        "volume": 0
                    },
                    "volatility_ema_span_1m": 10,
                    "volume_drop_pct": 0.5,
                    "volume_ema_span_1m": 360
                },
                "hsl": {
                    "cooldown_minutes_after_red": 0,
                    "ema_span_minutes": 60,
                    "enabled": false,
                    "no_restart_drawdown_threshold": 1,
                    "orange_tier_mode": "tp_only_with_active_entry_cancellation",
                    "panic_close_order_type": "limit",
                    "red_threshold": 0.2,
                    "tier_ratios": {
                        "orange": 0.75,
                        "yellow": 0.5
                    }
                },
                "risk": {
                    "entry_cooldown_minutes": 0,
                    "n_positions": 1,
                    "total_wallet_exposure_limit": 0,
                    "total_exposure_enforcer_enabled": true,
                    "total_exposure_enforcer_threshold": 0.95,
                    "we_excess_allowance_pct": 0,
                    "position_exposure_enforcer_enabled": true,
                    "position_exposure_enforcer_threshold": 0.95
                },
                "strategy": {
                    "trailing_martingale": {
                        "volatility_ema_span_1h": 672,
                        "volatility_ema_span_1m": 60,
                        "entry": {
                            "ema_span_0": 100,
                            "ema_span_1": 100,
                            "double_down_factor": 0.5,
                            "initial_ema_dist": -0.01,
                            "initial_qty_pct": 0.01,
                            "threshold_base_pct": 0.025,
                            "threshold_we_weight": 0,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_we_weight": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        },
                        "close": {
                            "qty_pct": 0.1,
                            "threshold_base_pct": 0.006,
                            "threshold_we_weight": -0.004,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        }
                    }
                },
                "unstuck": {
                    "ema_span_0": 100,
                    "ema_span_1": 100,
                    "close_pct": 0.001,
                    "ema_dist": -0.1,
                    "enabled": true,
                    "loss_allowance_pct": 0.001,
                    "threshold": 0.4
                }
            }
        },
        "coin_overrides": {},
        "config_version": "v8.4.0",
        "live": {
            "approved_coins": {
                "long": [
                    "ETH"
                ],
                "short": []
            },
            "auto_gs": true,
            "balance_hysteresis_snap_pct": 0.02,
            "balance_override": null,
            "candle_lock_timeout_seconds": 10,
            "enable_archive_candle_fetch": false,
            "execution_delay_seconds": 2,
            "filter_by_min_effective_cost": true,
            "forced_mode_long": "",
            "forced_mode_short": "",
            "hedge_mode": false,
            "hsl_position_during_cooldown_policy": "panic",
            "hsl_signal_mode": "unified",
            "ignored_coins": {
                "long": [],
                "short": []
            },
            "inactive_coin_candle_ttl_minutes": 10,
            "leverage": 1,
            "margin_mode_preference": "cross",
            "market_order_near_touch_threshold": 0.001,
            "market_orders_allowed": false,
            "max_concurrent_api_requests": null,
            "max_disk_candles_per_symbol_per_tf": 2000000,
            "max_memory_candles_per_symbol": 200000,
            "max_n_cancellations_per_batch": 5,
            "max_n_creations_per_batch": 3,
            "max_n_restarts_per_day": 10,
            "max_ohlcv_fetches_per_minute": 30,
            "max_realized_loss_pct": 1,
            "max_warmup_minutes": 0,
            "minimum_coin_age_days": 0,
            "forager_score_hysteresis_pct": 0.005,
            "order_match_tolerance_pct": 0.0002,
            "pnls_max_lookback_days": 30,
            "recv_window_ms": 5000,
            "strategy_kind": "trailing_martingale",
            "time_in_force": "good_till_cancelled",
            "user": "bybit_01",
            "warmup_concurrency": 0,
            "warmup_jitter_seconds": 30,
            "warmup_ratio": 0.3
        },
        "logging": {
            "backup_count": 5,
            "dir": "logs",
            "level": 1,
            "max_bytes_mb": 10,
            "memory_snapshot_interval_minutes": 30,
            "persist_to_file": true,
            "rotation": false,
            "volume_refresh_info_threshold_seconds": 30
        },
        "monitor": {
            "checkpoint_interval_minutes": 10,
            "compress_rotated_segments": true,
            "emit_completed_candles": true,
            "enabled": true,
            "event_rotation_mb": 128,
            "event_rotation_minutes": 60,
            "include_raw_fill_payloads": false,
            "max_total_bytes": 1073741824,
            "price_tick_min_interval_ms": 500,
            "retain_candles": true,
            "retain_days": 7,
            "retain_fills": true,
            "retain_price_ticks": true,
            "root_dir": "monitor",
            "snapshot_interval_seconds": 1
        },
        "optimize": {
            "backend": "pymoo",
            "bounds": {
                "long": {
                    "forager": {
                        "score_weights_ema_readiness": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volatility": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volume": [
                            0,
                            1,
                            0.01
                        ],
                        "volatility_ema_span_1m": [
                            10,
                            720,
                            1
                        ],
                        "volume_drop_pct": [
                            0.4,
                            1,
                            0.01
                        ],
                        "volume_ema_span_1m": [
                            360,
                            2880,
                            10
                        ]
                    },
                    "hsl": {
                        "cooldown_minutes_after_red": [
                            1,
                            2880,
                            10
                        ],
                        "ema_span_minutes": [
                            1,
                            2880,
                            10
                        ],
                        "red_threshold": [
                            0.01,
                            0.12,
                            0.001
                        ]
                    },
                    "risk": {
                        "entry_cooldown_minutes": [
                            0,
                            60,
                            0.1
                        ],
                        "n_positions": [
                            10,
                            10,
                            1
                        ],
                        "total_wallet_exposure_limit": [
                            1.25,
                            1.25
                        ],
                        "total_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ],
                        "we_excess_allowance_pct": [
                            0,
                            0.3,
                            0.01
                        ],
                        "position_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ]
                    },
                    "strategy": {
                        "trailing_martingale": {
                            "volatility_ema_span_1h": [
                                672,
                                2016,
                                1
                            ],
                            "volatility_ema_span_1m": [
                                5,
                                720,
                                1
                            ],
                            "entry": {
                                "ema_span_0": [
                                    200,
                                    1440,
                                    10
                                ],
                                "ema_span_1": [
                                    200,
                                    1440,
                                    10
                                ],
                                "double_down_factor": [
                                    0.5,
                                    1,
                                    0.01
                                ],
                                "initial_ema_dist": [
                                    -0.01,
                                    0.01,
                                    0.0001
                                ],
                                "initial_qty_pct": [
                                    0.01,
                                    0.03,
                                    0.0001
                                ],
                                "threshold_base_pct": [
                                    0,
                                    0.04,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            },
                            "close": {
                                "qty_pct": [
                                    0.05,
                                    1,
                                    0.01
                                ],
                                "threshold_base_pct": [
                                    -0.02,
                                    0.02,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    -0.05,
                                    0.05,
                                    0.0001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            }
                        }
                    },
                    "unstuck": {
                        "ema_span_0": [
                            770,
                            770
                        ],
                        "ema_span_1": [
                            210,
                            210
                        ],
                        "close_pct": [
                            0.05,
                            0.12,
                            0.001
                        ],
                        "ema_dist": [
                            -0.2,
                            -0.07,
                            0.0001
                        ],
                        "loss_allowance_pct": [
                            0.005,
                            0.025,
                            0.0001
                        ],
                        "threshold": [
                            0.4,
                            0.9,
                            0.001
                        ]
                    }
                },
                "short": {
                    "forager": {
                        "score_weights_ema_readiness": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volatility": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volume": [
                            0,
                            1,
                            0.01
                        ],
                        "volatility_ema_span_1m": [
                            10,
                            720,
                            1
                        ],
                        "volume_drop_pct": [
                            0.4,
                            1,
                            0.01
                        ],
                        "volume_ema_span_1m": [
                            360,
                            2880,
                            10
                        ]
                    },
                    "hsl": {
                        "cooldown_minutes_after_red": [
                            1,
                            2880,
                            10
                        ],
                        "ema_span_minutes": [
                            1,
                            2880,
                            10
                        ],
                        "red_threshold": [
                            0.01,
                            0.12,
                            0.001
                        ]
                    },
                    "risk": {
                        "entry_cooldown_minutes": [
                            0,
                            60,
                            0.1
                        ],
                        "n_positions": [
                            10,
                            10,
                            1
                        ],
                        "total_wallet_exposure_limit": [
                            0,
                            0
                        ],
                        "total_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ],
                        "we_excess_allowance_pct": [
                            0,
                            0.3,
                            0.01
                        ],
                        "position_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ]
                    },
                    "strategy": {
                        "trailing_martingale": {
                            "volatility_ema_span_1h": [
                                672,
                                2016,
                                1
                            ],
                            "volatility_ema_span_1m": [
                                5,
                                720,
                                1
                            ],
                            "entry": {
                                "ema_span_0": [
                                    200,
                                    1440,
                                    10
                                ],
                                "ema_span_1": [
                                    200,
                                    1440,
                                    10
                                ],
                                "double_down_factor": [
                                    0.5,
                                    1,
                                    0.01
                                ],
                                "initial_ema_dist": [
                                    -0.01,
                                    0.01,
                                    0.0001
                                ],
                                "initial_qty_pct": [
                                    0.01,
                                    0.03,
                                    0.0001
                                ],
                                "threshold_base_pct": [
                                    0,
                                    0.04,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            },
                            "close": {
                                "qty_pct": [
                                    0.05,
                                    1,
                                    0.01
                                ],
                                "threshold_base_pct": [
                                    -0.02,
                                    0.02,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    -0.05,
                                    0.05,
                                    0.0001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            }
                        }
                    },
                    "unstuck": {
                        "ema_span_0": [
                            100,
                            100
                        ],
                        "ema_span_1": [
                            100,
                            100
                        ],
                        "close_pct": [
                            0.05,
                            0.12,
                            0.001
                        ],
                        "ema_dist": [
                            -0.2,
                            -0.07,
                            0.0001
                        ],
                        "loss_allowance_pct": [
                            0.005,
                            0.025,
                            0.0001
                        ],
                        "threshold": [
                            0.4,
                            0.9,
                            0.001
                        ]
                    }
                }
            },
            "compress_results_file": true,
            "crossover_eta": 20,
            "crossover_probability": 0.64,
            "enable_overrides": [],
            "fixed_params": [],
            "fixed_runtime_overrides": {
                "bot.long.hsl.no_restart_drawdown_threshold": 1,
                "bot.short.hsl.no_restart_drawdown_threshold": 1
            },
            "iters": 500000,
            "limits": [
                {
                    "metric": "drawdown_worst_btc",
                    "penalize_if": "greater_than",
                    "value": 0.9
                },
                {
                    "metric": "drawdown_worst_usd",
                    "penalize_if": "greater_than",
                    "value": 0.9
                },
                {
                    "metric": "loss_profit_ratio",
                    "penalize_if": "greater_than",
                    "value": 0.6
                },
                {
                    "metric": "adg_pnl",
                    "penalize_if": "less_than",
                    "reducer": "mean",
                    "value": 0.0009
                },
                {
                    "metric": "peak_recovery_hours_pnl",
                    "penalize_if": "greater_than",
                    "value": 1344
                },
                {
                    "metric": "position_held_hours_max",
                    "penalize_if": "greater_than",
                    "value": 1344
                },
                {
                    "metric": "position_unchanged_hours_max",
                    "penalize_if": "greater_than",
                    "value": 840
                }
            ],
            "mutation_eta": 20,
            "mutation_indpb": 0.05,
            "mutation_probability": 0.34,
            "n_cpus": 16,
            "offspring_multiplier": 1,
            "pareto_max_size": 250,
            "population_size": 250,
            "pymoo": {
                "algorithm": "auto",
                "algorithms": {
                    "nsga2": {},
                    "nsga3": {
                        "ref_dirs": {
                            "method": "das_dennis",
                            "n_partitions": "auto"
                        }
                    }
                },
                "shared": {
                    "crossover_eta": 20,
                    "crossover_prob_var": 0.64,
                    "eliminate_duplicates": true,
                    "mutation_eta": 20,
                    "mutation_prob": 0.05,
                    "mutation_prob_per_variable": "auto"
                }
            },
            "round_to_n_significant_digits": 3,
            "scoring": [
                {
                    "goal": "max",
                    "metric": "adg_pnl"
                },
                {
                    "goal": "max",
                    "metric": "mdg_pnl"
                },
                {
                    "goal": "min",
                    "metric": "loss_profit_ratio"
                },
                {
                    "goal": "min",
                    "metric": "peak_recovery_hours_pnl"
                },
                {
                    "goal": "min",
                    "metric": "position_held_hours_max"
                },
                {
                    "goal": "min",
                    "metric": "position_unchanged_hours_max"
                },
                {
                    "goal": "max",
                    "metric": "volume_pct_per_day_avg_w"
                },
                {
                    "goal": "max",
                    "metric": "entry_initial_balance_pct_long"
                }
            ],
            "write_all_results": true
        }
    },
    "_coins_sources": {
        "approved_coins": {
            "long": [
                "ETH"
            ],
            "short": []
        },
        "ignored_coins": {
            "long": [],
            "short": []
        }
    },
    "_transform_log": [
        {
            "step": "normalize_config",
            "ts_ms": 1790895979531,
            "details": {
                "live_only": false,
                "base_config_path": "",
                "flavor": "current",
                "changes": [
                    {
                        "action": "add",
                        "path": "bot.long.hsl",
                        "value": {
                            "__dict__": {}
                        }
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.cooldown_minutes_after_red",
                        "value": 2160.0
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.ema_span_minutes",
                        "value": 720.0
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.enabled",
                        "value": false
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.no_restart_drawdown_threshold",
                        "value": 1
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.orange_tier_mode",
                        "value": "tp_only_with_active_entry_cancellation"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.panic_close_order_type",
                        "value": "limit"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.red_threshold",
                        "value": 0.15
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.restart_after_red_policy",
                        "value": "threshold"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.tier_ratios",
                        "value": {
                            "__dict__": {
                                "orange": 0.75,
                                "yellow": 0.5
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "bot.long.risk.total_exposure_enforcer_policy",
                        "value": "reduce_overweight"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.risk.total_exposure_entry_gate_enabled",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "bot.long.risk.we_excess_allowance_mode",
                        "value": "bounded"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.unstuck.ema_gating_enabled",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "bot.long.strategy.trailing_martingale.entry.ema_gate_mode",
                        "value": "all"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": 0.01,
                                "ema_span_0": 200.0,
                                "ema_span_1": 800.0,
                                "entry_double_down_factor": 0.0,
                                "offset": 0.002,
                                "offset_volatility_ema_span_1m": 60.0,
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "bot.long.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": 385.0,
                                "ema_span_1": 620.0,
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": 1.39,
                                        "grid_spacing_pct": 0.02312,
                                        "grid_spacing_we_weight": 0.6766,
                                        "grid_spacing_volatility_weight": 17.8,
                                        "initial_ema_dist": 0.0078,
                                        "initial_qty_pct": 0.0122,
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": 0.01041,
                                        "grid_markup_end": 0.00241,
                                        "grid_qty_pct": 0.88,
                                        "trailing_grid_ratio": -0.07,
                                        "trailing_qty_pct": 0.89,
                                        "trailing_retracement_pct": 0.00413,
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "bot.short.hsl.restart_after_red_policy",
                        "value": "threshold"
                    },
                    {
                        "action": "add",
                        "path": "bot.short.risk.total_exposure_enforcer_policy",
                        "value": "reduce_overweight"
                    },
                    {
                        "action": "add",
                        "path": "bot.short.risk.total_exposure_entry_gate_enabled",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "bot.short.risk.we_excess_allowance_mode",
                        "value": "bounded"
                    },
                    {
                        "action": "add",
                        "path": "bot.short.unstuck.ema_gating_enabled",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "bot.short.strategy.trailing_martingale.entry.ema_gate_mode",
                        "value": "all"
                    },
                    {
                        "action": "add",
                        "path": "bot.short.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": 0.01,
                                "ema_span_0": 200.0,
                                "ema_span_1": 800.0,
                                "entry_double_down_factor": 0.0,
                                "offset": 0.002,
                                "offset_volatility_ema_span_1m": 60.0,
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "bot.short.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": 300.0,
                                "ema_span_1": 700.0,
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": 1.0,
                                        "grid_spacing_pct": 0.02,
                                        "grid_spacing_we_weight": 1.0,
                                        "grid_spacing_volatility_weight": 10.0,
                                        "initial_ema_dist": 0.01,
                                        "initial_qty_pct": 0.01,
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": 0.00402,
                                        "grid_markup_end": 0.00223,
                                        "grid_qty_pct": 0.5,
                                        "trailing_grid_ratio": -0.03,
                                        "trailing_qty_pct": 0.5,
                                        "trailing_retracement_pct": 0.005,
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "optimize.bounds.long.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": [
                                    0.001,
                                    0.05,
                                    0.0001
                                ],
                                "ema_span_0": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry_double_down_factor": [
                                    0.0,
                                    2.0,
                                    0.01
                                ],
                                "offset": [
                                    0.0,
                                    0.05,
                                    0.0001
                                ],
                                "offset_volatility_ema_span_1m": [
                                    5.0,
                                    720.0,
                                    1.0
                                ],
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "optimize.bounds.long.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": [
                                            0.0,
                                            2.0,
                                            0.01
                                        ],
                                        "grid_spacing_pct": [
                                            0.001,
                                            0.03,
                                            0.0001
                                        ],
                                        "grid_spacing_we_weight": [
                                            0.0,
                                            10.0,
                                            0.001
                                        ],
                                        "grid_spacing_volatility_weight": [
                                            0.0,
                                            50.0,
                                            0.01
                                        ],
                                        "initial_ema_dist": [
                                            -0.1,
                                            0.02,
                                            0.0001
                                        ],
                                        "initial_qty_pct": [
                                            0.005,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": [
                                            0.0015,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_markup_end": [
                                            -0.1,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_grid_ratio": [
                                            -1.0,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_retracement_pct": [
                                            0.0,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "optimize.bounds.short.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": [
                                    0.001,
                                    0.05,
                                    0.0001
                                ],
                                "ema_span_0": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry_double_down_factor": [
                                    0.0,
                                    2.0,
                                    0.01
                                ],
                                "offset": [
                                    0.0,
                                    0.05,
                                    0.0001
                                ],
                                "offset_volatility_ema_span_1m": [
                                    5.0,
                                    720.0,
                                    1.0
                                ],
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "optimize.bounds.short.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": [
                                            0.0,
                                            2.0,
                                            0.01
                                        ],
                                        "grid_spacing_pct": [
                                            0.001,
                                            0.03,
                                            0.0001
                                        ],
                                        "grid_spacing_we_weight": [
                                            0.0,
                                            10.0,
                                            0.001
                                        ],
                                        "grid_spacing_volatility_weight": [
                                            0.0,
                                            50.0,
                                            0.01
                                        ],
                                        "initial_ema_dist": [
                                            -0.1,
                                            0.02,
                                            0.0001
                                        ],
                                        "initial_qty_pct": [
                                            0.005,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": [
                                            0.0015,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_markup_end": [
                                            -0.1,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_grid_ratio": [
                                            -1.0,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_retracement_pct": [
                                            0.0,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "backtest.hsl_detailed_report",
                        "value": false
                    },
                    {
                        "action": "add",
                        "path": "backtest.hlcvs_data_dir",
                        "value": null
                    },
                    {
                        "action": "add",
                        "path": "backtest.hlcvs_data_override_mode",
                        "value": "intersection"
                    },
                    {
                        "action": "add",
                        "path": "backtest.market_settings",
                        "value": {
                            "__dict__": {
                                "overrides": {
                                    "__dict__": {}
                                },
                                "overrides_by_exchange": {
                                    "__dict__": {}
                                }
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "backtest.offline",
                        "value": false
                    },
                    {
                        "action": "add",
                        "path": "live.custom_endpoints_path",
                        "value": null
                    },
                    {
                        "action": "add",
                        "path": "live.defer_broad_candle_warmup",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "live.enable_forager_ws_candles",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "live.exchange_symbol_unavailable_cooldown_hours",
                        "value": 6.0
                    },
                    {
                        "action": "add",
                        "path": "live.fee_conversion_max_age_ms",
                        "value": 86400000
                    },
                    {
                        "action": "add",
                        "path": "live.fee_pct_fallback",
                        "value": 0.0002
                    },
                    {
                        "action": "add",
                        "path": "live.fee_pct_sanity_abs_max",
                        "value": 0.001
                    },
                    {
                        "action": "add",
                        "path": "live.fills_confirmation_overlap_minutes",
                        "value": 60
                    },
                    {
                        "action": "add",
                        "path": "live.fills_recent_overlap_minutes",
                        "value": 10
                    },
                    {
                        "action": "add",
                        "path": "live.forager_ws_candle_rest_audit_minutes",
                        "value": 30
                    },
                    {
                        "action": "add",
                        "path": "live.force_cold_startup",
                        "value": false
                    },
                    {
                        "action": "add",
                        "path": "live.hsl_accept_incomplete_history",
                        "value": false
                    },
                    {
                        "action": "add",
                        "path": "live.hsl_unavailable_grace_seconds",
                        "value": 120.0
                    },
                    {
                        "action": "add",
                        "path": "live.limit_order_create_max_market_dist_pct",
                        "value": 0.8
                    },
                    {
                        "action": "add",
                        "path": "live.market_snapshot_ticker_strategy",
                        "value": "auto"
                    },
                    {
                        "action": "add",
                        "path": "live.max_active_candle_tail_gap_minutes",
                        "value": 10
                    },
                    {
                        "action": "add",
                        "path": "live.max_forager_candle_refresh_seconds",
                        "value": 45
                    },
                    {
                        "action": "add",
                        "path": "live.max_forager_candle_staleness_minutes",
                        "value": null
                    },
                    {
                        "action": "add",
                        "path": "live.order_replacement_churn_gate_activation_count",
                        "value": 10
                    },
                    {
                        "action": "add",
                        "path": "live.order_replacement_churn_gate_market_dist_pct",
                        "value": 0.005
                    },
                    {
                        "action": "add",
                        "path": "live.order_replacement_churn_gate_stability_minutes",
                        "value": 2.0
                    },
                    {
                        "action": "add",
                        "path": "live.order_replacement_churn_gate_window_minutes",
                        "value": 10.0
                    },
                    {
                        "action": "add",
                        "path": "live.risk_input_max_attempts",
                        "value": 10
                    },
                    {
                        "action": "add",
                        "path": "live.startup_phase_budgets",
                        "value": {
                            "__dict__": {}
                        }
                    },
                    {
                        "action": "add",
                        "path": "logging.live_event_debug_profiles",
                        "value": []
                    },
                    {
                        "action": "add",
                        "path": "optimize.objective_scenario",
                        "value": null
                    },
                    {
                        "action": "add",
                        "path": "optimize.seed",
                        "value": null
                    },
                    {
                        "action": "add",
                        "path": "optimize.gpu",
                        "value": {
                            "__dict__": {
                                "auto_lean_parallelism": true,
                                "batch_size": null,
                                "max_dispatch_candidate_bars": null,
                                "checkpoint_interval_seconds": 5.0,
                                "drift_halt": 0.6,
                                "drift_rank_halt": null,
                                "...": "10 more keys"
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "live.base_config_path",
                        "value": ""
                    },
                    {
                        "action": "remove",
                        "path": "backtest.max_warmup_minutes",
                        "value": 0
                    },
                    {
                        "action": "remove",
                        "path": "bot.long.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": 0.01,
                                "ema_span_0": 200.0,
                                "ema_span_1": 800.0,
                                "entry_double_down_factor": 0.0,
                                "offset": 0.002,
                                "offset_psize_weight": 0.1,
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "bot.long.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "close": {
                                    "__dict__": {
                                        "grid_markup_end": 0.00241,
                                        "grid_markup_start": 0.01041,
                                        "grid_qty_pct": 0.88,
                                        "trailing_grid_ratio": -0.07,
                                        "trailing_qty_pct": 0.89,
                                        "trailing_retracement_pct": 0.00413,
                                        "...": "1 more keys"
                                    }
                                },
                                "ema_span_0": 385.0,
                                "ema_span_1": 620.0,
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": 1.39,
                                        "grid_spacing_pct": 0.02312,
                                        "grid_spacing_volatility_weight": 17.8,
                                        "grid_spacing_we_weight": 0.6766,
                                        "initial_ema_dist": 0.0078,
                                        "initial_qty_pct": 0.0122,
                                        "...": "9 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "bot.short.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": 0.01,
                                "ema_span_0": 200.0,
                                "ema_span_1": 800.0,
                                "entry_double_down_factor": 0.0,
                                "offset": 0.002,
                                "offset_psize_weight": 0.1,
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "bot.short.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "close": {
                                    "__dict__": {
                                        "grid_markup_end": 0.00223,
                                        "grid_markup_start": 0.00402,
                                        "grid_qty_pct": 0.5,
                                        "trailing_grid_ratio": -0.03,
                                        "trailing_qty_pct": 0.5,
                                        "trailing_retracement_pct": 0.005,
                                        "...": "1 more keys"
                                    }
                                },
                                "ema_span_0": 300.0,
                                "ema_span_1": 700.0,
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": 1.0,
                                        "grid_spacing_pct": 0.02,
                                        "grid_spacing_volatility_weight": 10.0,
                                        "grid_spacing_we_weight": 1.0,
                                        "initial_ema_dist": 0.01,
                                        "initial_qty_pct": 0.01,
                                        "...": "9 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "optimize.bounds.long.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": [
                                    0.001,
                                    0.05,
                                    0.0001
                                ],
                                "ema_span_0": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry_double_down_factor": [
                                    0.0,
                                    2.0,
                                    0.01
                                ],
                                "offset": [
                                    0.0,
                                    0.05,
                                    0.0001
                                ],
                                "offset_volatility_ema_span_1m": [
                                    5.0,
                                    720.0,
                                    1.0
                                ],
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "optimize.bounds.long.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": [
                                            0.0,
                                            2.0,
                                            0.01
                                        ],
                                        "grid_spacing_pct": [
                                            0.001,
                                            0.03,
                                            0.0001
                                        ],
                                        "grid_spacing_we_weight": [
                                            0.0,
                                            10.0,
                                            0.001
                                        ],
                                        "grid_spacing_volatility_weight": [
                                            0.0,
                                            50.0,
                                            0.01
                                        ],
                                        "initial_ema_dist": [
                                            -0.1,
                                            0.02,
                                            0.0001
                                        ],
                                        "initial_qty_pct": [
                                            0.005,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": [
                                            0.0015,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_markup_end": [
                                            -0.1,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_grid_ratio": [
                                            -1.0,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_retracement_pct": [
                                            0.0,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "optimize.bounds.short.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": [
                                    0.001,
                                    0.05,
                                    0.0001
                                ],
                                "ema_span_0": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry_double_down_factor": [
                                    0.0,
                                    2.0,
                                    0.01
                                ],
                                "offset": [
                                    0.0,
                                    0.05,
                                    0.0001
                                ],
                                "offset_volatility_ema_span_1m": [
                                    5.0,
                                    720.0,
                                    1.0
                                ],
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "optimize.bounds.short.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": [
                                            0.0,
                                            2.0,
                                            0.01
                                        ],
                                        "grid_spacing_pct": [
                                            0.001,
                                            0.03,
                                            0.0001
                                        ],
                                        "grid_spacing_we_weight": [
                                            0.0,
                                            10.0,
                                            0.001
                                        ],
                                        "grid_spacing_volatility_weight": [
                                            0.0,
                                            50.0,
                                            0.01
                                        ],
                                        "initial_ema_dist": [
                                            -0.1,
                                            0.02,
                                            0.0001
                                        ],
                                        "initial_qty_pct": [
                                            0.005,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": [
                                            0.0015,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_markup_end": [
                                            -0.1,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_grid_ratio": [
                                            -1.0,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_retracement_pct": [
                                            0.0,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }
    ]
}
```

# 12. SOL 配置
```json
{
    "backtest": {
        "balance_sample_divider": 60,
        "base_dir": "backtests",
        "btc_collateral_cap": 0.0,
        "btc_collateral_ltv_cap": null,
        "candle_interval_minutes": 1,
        "coin_sources": {},
        "compress_cache": true,
        "dynamic_wel_by_tradability": true,
        "end_date": "2026-10-01",
        "exchanges": [
            "binance"
        ],
        "filter_by_min_effective_cost": false,
        "gap_tolerance_ohlcvs_minutes": 120,
        "liquidation_threshold": 0.05,
        "maker_fee_override": 0.0004,
        "market_order_slippage_pct": 0.0005,
        "limit_order_fill_buffer_pct": 0,
        "market_settings_sources": {},
        "ohlcv_source_dir": "/Users/liu/Documents/go/gopath/src/rust-pro/passivbot-struct/passivbot/caches/ft_source",
        "scenarios": [
            {
                "label": "SOL_recommended_long"
            }
        ],
        "start_date": "2020-09-15",
        "starting_balance": 100000,
        "suite_enabled": false,
        "taker_fee_override": null,
        "visible_metrics": null,
        "volume_normalization": true,
        "reducer": {
            "default": "mean",
            "drawdown_worst_hsl": "max",
            "drawdown_worst_mean_1pct_hsl": "max",
            "peak_recovery_hours_hsl": "max",
            "position_held_hours_max": "max"
        },
        "hsl_detailed_report": false,
        "hlcvs_data_dir": null,
        "hlcvs_data_override_mode": "intersection",
        "market_settings": {
            "overrides": {},
            "overrides_by_exchange": {}
        },
        "offline": false
    },
    "bot": {
        "long": {
            "forager": {
                "score_weights": {
                    "ema_readiness": 0.0,
                    "volatility": 1.0,
                    "volume": 0.0
                },
                "volatility_ema_span_1m": 80,
                "volume_drop_pct": 0.884,
                "volume_ema_span_1m": 1660
            },
            "hsl": {
                "cooldown_minutes_after_red": 2880,
                "ema_span_minutes": 720,
                "enabled": false,
                "no_restart_drawdown_threshold": 1,
                "orange_tier_mode": "tp_only_with_active_entry_cancellation",
                "panic_close_order_type": "limit",
                "red_threshold": 0.15,
                "restart_after_red_policy": "threshold",
                "tier_ratios": {
                    "orange": 0.75,
                    "yellow": 0.5
                }
            },
            "risk": {
                "entry_cooldown_minutes": 0,
                "n_positions": 1,
                "position_exposure_enforcer_enabled": true,
                "position_exposure_enforcer_threshold": 0.98,
                "total_exposure_enforcer_enabled": true,
                "total_exposure_enforcer_policy": "reduce_overweight",
                "total_exposure_enforcer_threshold": 0.98,
                "total_exposure_entry_gate_enabled": true,
                "total_wallet_exposure_limit": 1,
                "we_excess_allowance_mode": "bounded",
                "we_excess_allowance_pct": 0
            },
            "strategy": {
                "trailing_martingale": {
                    "close": {
                        "qty_pct": 0.1,
                        "retracement_base_pct": 0,
                        "retracement_volatility_1h_weight": 0,
                        "retracement_volatility_1m_weight": 0,
                        "threshold_base_pct": 0.0065,
                        "threshold_volatility_1h_weight": 1.0,
                        "threshold_volatility_1m_weight": 0,
                        "threshold_we_weight": -0.004
                    },
                    "entry": {
                        "double_down_factor": 0.66,
                        "ema_gate_mode": "all",
                        "ema_span_0": 770,
                        "ema_span_1": 210,
                        "initial_ema_dist": -0.016,
                        "initial_qty_pct": 0.012,
                        "retracement_base_pct": 0,
                        "retracement_volatility_1h_weight": 0,
                        "retracement_volatility_1m_weight": 0,
                        "retracement_we_weight": 0,
                        "threshold_base_pct": 0.032,
                        "threshold_volatility_1h_weight": 2.4,
                        "threshold_volatility_1m_weight": 0,
                        "threshold_we_weight": 0.0
                    },
                    "volatility_ema_span_1h": 1690,
                    "volatility_ema_span_1m": 60
                }
            },
            "unstuck": {
                "close_pct": 0.009,
                "ema_dist": -0.085,
                "ema_gating_enabled": true,
                "ema_span_0": 770,
                "ema_span_1": 210,
                "enabled": true,
                "loss_allowance_pct": 0.012,
                "threshold": 0.82
            }
        },
        "short": {
            "forager": {
                "score_weights": {
                    "ema_readiness": 0.0,
                    "volatility": 1.0,
                    "volume": 0.0
                },
                "volatility_ema_span_1m": 10,
                "volume_drop_pct": 0.5,
                "volume_ema_span_1m": 360
            },
            "hsl": {
                "cooldown_minutes_after_red": 1440.0,
                "ema_span_minutes": 60.0,
                "enabled": true,
                "no_restart_drawdown_threshold": 1,
                "orange_tier_mode": "tp_only_with_active_entry_cancellation",
                "panic_close_order_type": "market",
                "red_threshold": 0.15,
                "restart_after_red_policy": "threshold",
                "tier_ratios": {
                    "orange": 0.75,
                    "yellow": 0.5
                }
            },
            "risk": {
                "entry_cooldown_minutes": 0,
                "n_positions": 1,
                "position_exposure_enforcer_enabled": true,
                "position_exposure_enforcer_threshold": 0.95,
                "total_exposure_enforcer_enabled": true,
                "total_exposure_enforcer_policy": "reduce_overweight",
                "total_exposure_enforcer_threshold": 0.95,
                "total_exposure_entry_gate_enabled": true,
                "total_wallet_exposure_limit": 0,
                "we_excess_allowance_mode": "bounded",
                "we_excess_allowance_pct": 0
            },
            "strategy": {
                "trailing_martingale": {
                    "close": {
                        "qty_pct": 0.1,
                        "retracement_base_pct": 0,
                        "retracement_volatility_1h_weight": 0,
                        "retracement_volatility_1m_weight": 0,
                        "threshold_base_pct": 0.006,
                        "threshold_volatility_1h_weight": 1,
                        "threshold_volatility_1m_weight": 0,
                        "threshold_we_weight": -0.004
                    },
                    "entry": {
                        "double_down_factor": 0.5,
                        "ema_gate_mode": "all",
                        "ema_span_0": 100,
                        "ema_span_1": 100,
                        "initial_ema_dist": -0.01,
                        "initial_qty_pct": 0.01,
                        "retracement_base_pct": 0,
                        "retracement_volatility_1h_weight": 0,
                        "retracement_volatility_1m_weight": 0,
                        "retracement_we_weight": 0,
                        "threshold_base_pct": 0.025,
                        "threshold_volatility_1h_weight": 1,
                        "threshold_volatility_1m_weight": 0,
                        "threshold_we_weight": 0
                    },
                    "volatility_ema_span_1h": 672,
                    "volatility_ema_span_1m": 60
                }
            },
            "unstuck": {
                "close_pct": 0.001,
                "ema_dist": -0.1,
                "ema_gating_enabled": true,
                "ema_span_0": 100.0,
                "ema_span_1": 100.0,
                "enabled": true,
                "loss_allowance_pct": 0.001,
                "threshold": 0.4
            }
        }
    },
    "coin_overrides": {},
    "config_version": "v8.4.0",
    "live": {
        "approved_coins": {
            "long": [
                "SOL"
            ],
            "short": []
        },
        "auto_gs": true,
        "balance_hysteresis_snap_pct": 0.02,
        "balance_override": null,
        "candle_lock_timeout_seconds": 10,
        "enable_archive_candle_fetch": false,
        "execution_delay_seconds": 2,
        "filter_by_min_effective_cost": true,
        "forced_mode_long": "",
        "forced_mode_short": "",
        "hedge_mode": false,
        "hsl_position_during_cooldown_policy": "panic",
        "hsl_signal_mode": "unified",
        "ignored_coins": {
            "long": [],
            "short": []
        },
        "inactive_coin_candle_ttl_minutes": 10,
        "leverage": 1,
        "margin_mode_preference": "cross",
        "market_order_near_touch_threshold": 0.001,
        "market_orders_allowed": false,
        "max_concurrent_api_requests": null,
        "max_disk_candles_per_symbol_per_tf": 2000000,
        "max_memory_candles_per_symbol": 200000,
        "max_n_cancellations_per_batch": 5,
        "max_n_creations_per_batch": 3,
        "max_n_restarts_per_day": 10,
        "max_ohlcv_fetches_per_minute": 30,
        "max_realized_loss_pct": 1,
        "max_warmup_minutes": 0,
        "minimum_coin_age_days": 0,
        "forager_score_hysteresis_pct": 0.005,
        "order_match_tolerance_pct": 0.0002,
        "pnls_max_lookback_days": 30.0,
        "recv_window_ms": 5000,
        "strategy_kind": "trailing_martingale",
        "time_in_force": "good_till_cancelled",
        "user": "bybit_01",
        "warmup_concurrency": 0,
        "warmup_jitter_seconds": 30,
        "warmup_ratio": 0.3,
        "hsl_engine": "legacy",
        "custom_endpoints_path": null,
        "defer_broad_candle_warmup": true,
        "enable_forager_ws_candles": true,
        "exchange_symbol_unavailable_cooldown_hours": 6.0,
        "fee_conversion_max_age_ms": 86400000,
        "fee_pct_fallback": 0.0002,
        "fee_pct_sanity_abs_max": 0.001,
        "fills_confirmation_overlap_minutes": 60,
        "fills_recent_overlap_minutes": 10,
        "forager_ws_candle_rest_audit_minutes": 30,
        "force_cold_startup": false,
        "hsl_accept_incomplete_history": false,
        "hsl_unavailable_grace_seconds": 120.0,
        "limit_order_create_max_market_dist_pct": 0.8,
        "market_snapshot_ticker_strategy": "auto",
        "max_active_candle_tail_gap_minutes": 10,
        "max_forager_candle_refresh_seconds": 45,
        "max_forager_candle_staleness_minutes": null,
        "order_replacement_churn_gate_activation_count": 10,
        "order_replacement_churn_gate_market_dist_pct": 0.005,
        "order_replacement_churn_gate_stability_minutes": 2.0,
        "order_replacement_churn_gate_window_minutes": 10.0,
        "risk_input_max_attempts": 10,
        "startup_phase_budgets": {},
        "base_config_path": ""
    },
    "logging": {
        "backup_count": 5,
        "dir": "logs",
        "level": 1,
        "max_bytes_mb": 10.0,
        "memory_snapshot_interval_minutes": 30,
        "persist_to_file": true,
        "rotation": false,
        "volume_refresh_info_threshold_seconds": 30,
        "live_event_debug_profiles": []
    },
    "monitor": {
        "checkpoint_interval_minutes": 10.0,
        "compress_rotated_segments": true,
        "emit_completed_candles": true,
        "enabled": true,
        "event_rotation_mb": 128.0,
        "event_rotation_minutes": 60.0,
        "include_raw_fill_payloads": false,
        "max_total_bytes": 1073741824,
        "price_tick_min_interval_ms": 500,
        "retain_candles": true,
        "retain_days": 7.0,
        "retain_fills": true,
        "retain_price_ticks": true,
        "root_dir": "monitor",
        "snapshot_interval_seconds": 1.0
    },
    "optimize": {
        "backend": "pymoo",
        "bounds": {
            "long": {
                "forager": {
                    "score_weights_ema_readiness": [
                        0,
                        1,
                        0.01
                    ],
                    "score_weights_volatility": [
                        0,
                        1,
                        0.01
                    ],
                    "score_weights_volume": [
                        0,
                        1,
                        0.01
                    ],
                    "volatility_ema_span_1m": [
                        10,
                        720,
                        1
                    ],
                    "volume_drop_pct": [
                        0.4,
                        1,
                        0.01
                    ],
                    "volume_ema_span_1m": [
                        360,
                        2880,
                        10
                    ]
                },
                "hsl": {
                    "cooldown_minutes_after_red": [
                        1,
                        2880,
                        10
                    ],
                    "ema_span_minutes": [
                        1,
                        2880,
                        10
                    ],
                    "red_threshold": [
                        0.01,
                        0.12,
                        0.001
                    ]
                },
                "risk": {
                    "entry_cooldown_minutes": [
                        0,
                        60,
                        0.1
                    ],
                    "n_positions": [
                        10,
                        10,
                        1
                    ],
                    "position_exposure_enforcer_threshold": [
                        0.95,
                        1.01,
                        0.001
                    ],
                    "total_exposure_enforcer_threshold": [
                        0.95,
                        1.01,
                        0.001
                    ],
                    "total_wallet_exposure_limit": [
                        1.25,
                        1.25
                    ],
                    "we_excess_allowance_pct": [
                        0,
                        0.3,
                        0.01
                    ]
                },
                "unstuck": {
                    "close_pct": [
                        0.05,
                        0.12,
                        0.001
                    ],
                    "ema_dist": [
                        -0.2,
                        -0.07,
                        0.0001
                    ],
                    "ema_span_0": [
                        770,
                        770
                    ],
                    "ema_span_1": [
                        210,
                        210
                    ],
                    "loss_allowance_pct": [
                        0.005,
                        0.025,
                        0.0001
                    ],
                    "threshold": [
                        0.4,
                        0.9,
                        0.001
                    ]
                },
                "strategy": {
                    "trailing_martingale": {
                        "entry": {
                            "ema_span_0": [
                                200,
                                1440,
                                10
                            ],
                            "ema_span_1": [
                                200,
                                1440,
                                10
                            ],
                            "double_down_factor": [
                                0.5,
                                1,
                                0.01
                            ],
                            "initial_qty_pct": [
                                0.01,
                                0.03,
                                0.0001
                            ],
                            "initial_ema_dist": [
                                -0.01,
                                0.01,
                                0.0001
                            ],
                            "threshold_base_pct": [
                                0,
                                0.04,
                                1e-05
                            ],
                            "threshold_we_weight": [
                                0,
                                5,
                                0.001
                            ],
                            "threshold_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "threshold_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_base_pct": [
                                0,
                                0.015,
                                1e-05
                            ],
                            "retracement_we_weight": [
                                0,
                                5,
                                0.001
                            ],
                            "retracement_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ]
                        },
                        "volatility_ema_span_1h": [
                            672,
                            2016,
                            1
                        ],
                        "volatility_ema_span_1m": [
                            5,
                            720,
                            1
                        ],
                        "close": {
                            "qty_pct": [
                                0.05,
                                1,
                                0.01
                            ],
                            "threshold_base_pct": [
                                -0.02,
                                0.02,
                                1e-05
                            ],
                            "threshold_we_weight": [
                                -0.05,
                                0.05,
                                0.0001
                            ],
                            "threshold_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "threshold_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_base_pct": [
                                0,
                                0.015,
                                1e-05
                            ],
                            "retracement_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ]
                        }
                    }
                }
            },
            "short": {
                "forager": {
                    "score_weights_ema_readiness": [
                        0,
                        1,
                        0.01
                    ],
                    "score_weights_volatility": [
                        0,
                        1,
                        0.01
                    ],
                    "score_weights_volume": [
                        0,
                        1,
                        0.01
                    ],
                    "volatility_ema_span_1m": [
                        10,
                        720,
                        1
                    ],
                    "volume_drop_pct": [
                        0.4,
                        1,
                        0.01
                    ],
                    "volume_ema_span_1m": [
                        360,
                        2880,
                        10
                    ]
                },
                "hsl": {
                    "cooldown_minutes_after_red": [
                        1,
                        2880,
                        10
                    ],
                    "ema_span_minutes": [
                        1,
                        2880,
                        10
                    ],
                    "red_threshold": [
                        0.01,
                        0.12,
                        0.001
                    ]
                },
                "risk": {
                    "entry_cooldown_minutes": [
                        0,
                        60,
                        0.1
                    ],
                    "n_positions": [
                        10,
                        10,
                        1
                    ],
                    "position_exposure_enforcer_threshold": [
                        0.95,
                        1.01,
                        0.001
                    ],
                    "total_exposure_enforcer_threshold": [
                        0.95,
                        1.01,
                        0.001
                    ],
                    "total_wallet_exposure_limit": [
                        0,
                        0
                    ],
                    "we_excess_allowance_pct": [
                        0,
                        0.3,
                        0.01
                    ]
                },
                "unstuck": {
                    "close_pct": [
                        0.05,
                        0.12,
                        0.001
                    ],
                    "ema_dist": [
                        -0.2,
                        -0.07,
                        0.0001
                    ],
                    "ema_span_0": [
                        100,
                        100
                    ],
                    "ema_span_1": [
                        100,
                        100
                    ],
                    "loss_allowance_pct": [
                        0.005,
                        0.025,
                        0.0001
                    ],
                    "threshold": [
                        0.4,
                        0.9,
                        0.001
                    ]
                },
                "strategy": {
                    "trailing_martingale": {
                        "entry": {
                            "ema_span_0": [
                                200,
                                1440,
                                10
                            ],
                            "ema_span_1": [
                                200,
                                1440,
                                10
                            ],
                            "double_down_factor": [
                                0.5,
                                1,
                                0.01
                            ],
                            "initial_qty_pct": [
                                0.01,
                                0.03,
                                0.0001
                            ],
                            "initial_ema_dist": [
                                -0.01,
                                0.01,
                                0.0001
                            ],
                            "threshold_base_pct": [
                                0,
                                0.04,
                                1e-05
                            ],
                            "threshold_we_weight": [
                                0,
                                5,
                                0.001
                            ],
                            "threshold_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "threshold_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_base_pct": [
                                0,
                                0.015,
                                1e-05
                            ],
                            "retracement_we_weight": [
                                0,
                                5,
                                0.001
                            ],
                            "retracement_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ]
                        },
                        "volatility_ema_span_1h": [
                            672,
                            2016,
                            1
                        ],
                        "volatility_ema_span_1m": [
                            5,
                            720,
                            1
                        ],
                        "close": {
                            "qty_pct": [
                                0.05,
                                1,
                                0.01
                            ],
                            "threshold_base_pct": [
                                -0.02,
                                0.02,
                                1e-05
                            ],
                            "threshold_we_weight": [
                                -0.05,
                                0.05,
                                0.0001
                            ],
                            "threshold_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "threshold_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_base_pct": [
                                0,
                                0.015,
                                1e-05
                            ],
                            "retracement_volatility_1h_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ]
                        }
                    }
                }
            }
        },
        "compress_results_file": true,
        "crossover_eta": 20,
        "crossover_probability": 0.64,
        "enable_overrides": [],
        "fixed_params": [],
        "fixed_runtime_overrides": {
            "bot.long.hsl.no_restart_drawdown_threshold": 1,
            "bot.short.hsl.no_restart_drawdown_threshold": 1
        },
        "iters": 500000,
        "limits": [
            {
                "metric": "drawdown_worst_btc",
                "penalize_if": "greater_than",
                "value": 0.9
            },
            {
                "metric": "drawdown_worst_usd",
                "penalize_if": "greater_than",
                "value": 0.9
            },
            {
                "metric": "loss_profit_ratio",
                "penalize_if": "greater_than",
                "value": 0.6
            },
            {
                "metric": "adg_pnl",
                "penalize_if": "less_than",
                "reducer": "mean",
                "value": 0.0009
            },
            {
                "metric": "peak_recovery_hours_pnl",
                "penalize_if": "greater_than",
                "value": 1344
            },
            {
                "metric": "position_held_hours_max",
                "penalize_if": "greater_than",
                "value": 1344
            },
            {
                "metric": "position_unchanged_hours_max",
                "penalize_if": "greater_than",
                "value": 840
            }
        ],
        "mutation_eta": 20,
        "mutation_indpb": 0.05,
        "mutation_probability": 0.34,
        "n_cpus": 16,
        "offspring_multiplier": 1,
        "pareto_max_size": 250,
        "population_size": 250,
        "pymoo": {
            "algorithm": "auto",
            "shared": {
                "crossover_eta": 20.0,
                "crossover_prob_var": 0.64,
                "mutation_eta": 20.0,
                "mutation_prob": 0.05,
                "mutation_prob_per_variable": "auto",
                "eliminate_duplicates": true
            },
            "algorithms": {
                "nsga2": {},
                "nsga3": {
                    "ref_dirs": {
                        "method": "das_dennis",
                        "n_partitions": "auto"
                    }
                }
            }
        },
        "round_to_n_significant_digits": 3,
        "scoring": [
            {
                "metric": "adg_pnl",
                "goal": "max"
            },
            {
                "metric": "mdg_pnl",
                "goal": "max"
            },
            {
                "metric": "loss_profit_ratio",
                "goal": "min"
            },
            {
                "metric": "peak_recovery_hours_pnl",
                "goal": "min"
            },
            {
                "metric": "position_held_hours_max",
                "goal": "min"
            },
            {
                "metric": "position_unchanged_hours_max",
                "goal": "min"
            },
            {
                "metric": "volume_pct_per_day_avg_w",
                "goal": "max"
            },
            {
                "metric": "entry_initial_balance_pct_long",
                "goal": "max"
            }
        ],
        "write_all_results": true,
        "objective_scenario": null,
        "seed": null,
        "gpu": {
            "auto_lean_parallelism": true,
            "batch_size": null,
            "max_dispatch_candidate_bars": null,
            "checkpoint_interval_seconds": 5.0,
            "drift_halt": 0.6,
            "drift_rank_halt": null,
            "drift_objective_tolerance": 1e-06,
            "drift_min_samples": 32,
            "drift_probes": 4,
            "drift_window": 128,
            "exact_workers": 0,
            "max_pending_exact": 0,
            "population_size": null,
            "seed_bootstrap": {
                "max_exact": 128,
                "mode": "auto"
            },
            "screening": {
                "scenarios": [],
                "survival_fraction": 0.1,
                "min_survivors": 64
            },
            "validate_per_generation": 8
        }
    },
    "_raw": {
        "backtest": {
            "reducer": {
                "default": "mean",
                "drawdown_worst_hsl": "max",
                "drawdown_worst_mean_1pct_hsl": "max",
                "peak_recovery_hours_hsl": "max",
                "position_held_hours_max": "max"
            },
            "balance_sample_divider": 60,
            "base_dir": "backtests",
            "btc_collateral_cap": 0,
            "btc_collateral_ltv_cap": null,
            "candle_interval_minutes": 1,
            "coin_sources": {},
            "compress_cache": true,
            "dynamic_wel_by_tradability": true,
            "end_date": "now",
            "exchanges": [
                "binance"
            ],
            "filter_by_min_effective_cost": false,
            "gap_tolerance_ohlcvs_minutes": 120,
            "liquidation_threshold": 0.05,
            "maker_fee_override": 0.0004,
            "market_order_slippage_pct": 0.0005,
            "limit_order_fill_buffer_pct": 0,
            "market_settings_sources": {},
            "max_warmup_minutes": 0,
            "ohlcv_source_dir": null,
            "scenarios": [
                {
                    "label": "SOL_normal_osc_long"
                }
            ],
            "start_date": "2019-01-01",
            "starting_balance": 100000,
            "suite_enabled": false,
            "taker_fee_override": null,
            "visible_metrics": null,
            "volume_normalization": true
        },
        "bot": {
            "long": {
                "forager": {
                    "score_weights": {
                        "ema_readiness": 0,
                        "volatility": 1,
                        "volume": 0
                    },
                    "volatility_ema_span_1m": 101,
                    "volume_drop_pct": 0.884,
                    "volume_ema_span_1m": 1660
                },
                "risk": {
                    "entry_cooldown_minutes": 0,
                    "n_positions": 1,
                    "total_wallet_exposure_limit": 1,
                    "total_exposure_enforcer_enabled": true,
                    "total_exposure_enforcer_threshold": 0.99,
                    "we_excess_allowance_pct": 1.64,
                    "position_exposure_enforcer_enabled": true,
                    "position_exposure_enforcer_threshold": 0.99
                },
                "strategy": {
                    "trailing_martingale": {
                        "volatility_ema_span_1h": 1690,
                        "volatility_ema_span_1m": 60,
                        "entry": {
                            "ema_span_0": 770,
                            "ema_span_1": 210,
                            "double_down_factor": 0.74,
                            "initial_ema_dist": -0.0105,
                            "initial_qty_pct": 0.0261,
                            "threshold_base_pct": 0.037,
                            "threshold_we_weight": 0.135,
                            "threshold_volatility_1h_weight": 2.4,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_we_weight": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        },
                        "close": {
                            "qty_pct": 0.1,
                            "threshold_base_pct": 0.0067,
                            "threshold_we_weight": -0.004,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        }
                    }
                },
                "unstuck": {
                    "ema_span_0": 770,
                    "ema_span_1": 210,
                    "close_pct": 0.00936,
                    "ema_dist": -0.064,
                    "enabled": true,
                    "loss_allowance_pct": 0.00523,
                    "threshold": 0.833
                }
            },
            "short": {
                "forager": {
                    "score_weights": {
                        "ema_readiness": 0,
                        "volatility": 1,
                        "volume": 0
                    },
                    "volatility_ema_span_1m": 10,
                    "volume_drop_pct": 0.5,
                    "volume_ema_span_1m": 360
                },
                "hsl": {
                    "cooldown_minutes_after_red": 0,
                    "ema_span_minutes": 60,
                    "enabled": false,
                    "no_restart_drawdown_threshold": 1,
                    "orange_tier_mode": "tp_only_with_active_entry_cancellation",
                    "panic_close_order_type": "limit",
                    "red_threshold": 0.2,
                    "tier_ratios": {
                        "orange": 0.75,
                        "yellow": 0.5
                    }
                },
                "risk": {
                    "entry_cooldown_minutes": 0,
                    "n_positions": 1,
                    "total_wallet_exposure_limit": 0,
                    "total_exposure_enforcer_enabled": true,
                    "total_exposure_enforcer_threshold": 0.95,
                    "we_excess_allowance_pct": 0,
                    "position_exposure_enforcer_enabled": true,
                    "position_exposure_enforcer_threshold": 0.95
                },
                "strategy": {
                    "trailing_martingale": {
                        "volatility_ema_span_1h": 672,
                        "volatility_ema_span_1m": 60,
                        "entry": {
                            "ema_span_0": 100,
                            "ema_span_1": 100,
                            "double_down_factor": 0.5,
                            "initial_ema_dist": -0.01,
                            "initial_qty_pct": 0.01,
                            "threshold_base_pct": 0.025,
                            "threshold_we_weight": 0,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_we_weight": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        },
                        "close": {
                            "qty_pct": 0.1,
                            "threshold_base_pct": 0.006,
                            "threshold_we_weight": -0.004,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        }
                    }
                },
                "unstuck": {
                    "ema_span_0": 100,
                    "ema_span_1": 100,
                    "close_pct": 0.001,
                    "ema_dist": -0.1,
                    "enabled": true,
                    "loss_allowance_pct": 0.001,
                    "threshold": 0.4
                }
            }
        },
        "coin_overrides": {},
        "config_version": "v8.4.0",
        "live": {
            "approved_coins": {
                "long": [
                    "SOL"
                ],
                "short": []
            },
            "auto_gs": true,
            "balance_hysteresis_snap_pct": 0.02,
            "balance_override": null,
            "candle_lock_timeout_seconds": 10,
            "enable_archive_candle_fetch": false,
            "execution_delay_seconds": 2,
            "filter_by_min_effective_cost": true,
            "forced_mode_long": "",
            "forced_mode_short": "",
            "hedge_mode": false,
            "hsl_position_during_cooldown_policy": "panic",
            "hsl_signal_mode": "unified",
            "ignored_coins": {
                "long": [],
                "short": []
            },
            "inactive_coin_candle_ttl_minutes": 10,
            "leverage": 1,
            "margin_mode_preference": "cross",
            "market_order_near_touch_threshold": 0.001,
            "market_orders_allowed": false,
            "max_concurrent_api_requests": null,
            "max_disk_candles_per_symbol_per_tf": 2000000,
            "max_memory_candles_per_symbol": 200000,
            "max_n_cancellations_per_batch": 5,
            "max_n_creations_per_batch": 3,
            "max_n_restarts_per_day": 10,
            "max_ohlcv_fetches_per_minute": 30,
            "max_realized_loss_pct": 1,
            "max_warmup_minutes": 0,
            "minimum_coin_age_days": 0,
            "forager_score_hysteresis_pct": 0.005,
            "order_match_tolerance_pct": 0.0002,
            "pnls_max_lookback_days": 30,
            "recv_window_ms": 5000,
            "strategy_kind": "trailing_martingale",
            "time_in_force": "good_till_cancelled",
            "user": "bybit_01",
            "warmup_concurrency": 0,
            "warmup_jitter_seconds": 30,
            "warmup_ratio": 0.3
        },
        "logging": {
            "backup_count": 5,
            "dir": "logs",
            "level": 1,
            "max_bytes_mb": 10,
            "memory_snapshot_interval_minutes": 30,
            "persist_to_file": true,
            "rotation": false,
            "volume_refresh_info_threshold_seconds": 30
        },
        "monitor": {
            "checkpoint_interval_minutes": 10,
            "compress_rotated_segments": true,
            "emit_completed_candles": true,
            "enabled": true,
            "event_rotation_mb": 128,
            "event_rotation_minutes": 60,
            "include_raw_fill_payloads": false,
            "max_total_bytes": 1073741824,
            "price_tick_min_interval_ms": 500,
            "retain_candles": true,
            "retain_days": 7,
            "retain_fills": true,
            "retain_price_ticks": true,
            "root_dir": "monitor",
            "snapshot_interval_seconds": 1
        },
        "optimize": {
            "backend": "pymoo",
            "bounds": {
                "long": {
                    "forager": {
                        "score_weights_ema_readiness": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volatility": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volume": [
                            0,
                            1,
                            0.01
                        ],
                        "volatility_ema_span_1m": [
                            10,
                            720,
                            1
                        ],
                        "volume_drop_pct": [
                            0.4,
                            1,
                            0.01
                        ],
                        "volume_ema_span_1m": [
                            360,
                            2880,
                            10
                        ]
                    },
                    "hsl": {
                        "cooldown_minutes_after_red": [
                            1,
                            2880,
                            10
                        ],
                        "ema_span_minutes": [
                            1,
                            2880,
                            10
                        ],
                        "red_threshold": [
                            0.01,
                            0.12,
                            0.001
                        ]
                    },
                    "risk": {
                        "entry_cooldown_minutes": [
                            0,
                            60,
                            0.1
                        ],
                        "n_positions": [
                            10,
                            10,
                            1
                        ],
                        "total_wallet_exposure_limit": [
                            1.25,
                            1.25
                        ],
                        "total_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ],
                        "we_excess_allowance_pct": [
                            0,
                            0.3,
                            0.01
                        ],
                        "position_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ]
                    },
                    "strategy": {
                        "trailing_martingale": {
                            "volatility_ema_span_1h": [
                                672,
                                2016,
                                1
                            ],
                            "volatility_ema_span_1m": [
                                5,
                                720,
                                1
                            ],
                            "entry": {
                                "ema_span_0": [
                                    200,
                                    1440,
                                    10
                                ],
                                "ema_span_1": [
                                    200,
                                    1440,
                                    10
                                ],
                                "double_down_factor": [
                                    0.5,
                                    1,
                                    0.01
                                ],
                                "initial_ema_dist": [
                                    -0.01,
                                    0.01,
                                    0.0001
                                ],
                                "initial_qty_pct": [
                                    0.01,
                                    0.03,
                                    0.0001
                                ],
                                "threshold_base_pct": [
                                    0,
                                    0.04,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            },
                            "close": {
                                "qty_pct": [
                                    0.05,
                                    1,
                                    0.01
                                ],
                                "threshold_base_pct": [
                                    -0.02,
                                    0.02,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    -0.05,
                                    0.05,
                                    0.0001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            }
                        }
                    },
                    "unstuck": {
                        "ema_span_0": [
                            770,
                            770
                        ],
                        "ema_span_1": [
                            210,
                            210
                        ],
                        "close_pct": [
                            0.05,
                            0.12,
                            0.001
                        ],
                        "ema_dist": [
                            -0.2,
                            -0.07,
                            0.0001
                        ],
                        "loss_allowance_pct": [
                            0.005,
                            0.025,
                            0.0001
                        ],
                        "threshold": [
                            0.4,
                            0.9,
                            0.001
                        ]
                    }
                },
                "short": {
                    "forager": {
                        "score_weights_ema_readiness": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volatility": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volume": [
                            0,
                            1,
                            0.01
                        ],
                        "volatility_ema_span_1m": [
                            10,
                            720,
                            1
                        ],
                        "volume_drop_pct": [
                            0.4,
                            1,
                            0.01
                        ],
                        "volume_ema_span_1m": [
                            360,
                            2880,
                            10
                        ]
                    },
                    "hsl": {
                        "cooldown_minutes_after_red": [
                            1,
                            2880,
                            10
                        ],
                        "ema_span_minutes": [
                            1,
                            2880,
                            10
                        ],
                        "red_threshold": [
                            0.01,
                            0.12,
                            0.001
                        ]
                    },
                    "risk": {
                        "entry_cooldown_minutes": [
                            0,
                            60,
                            0.1
                        ],
                        "n_positions": [
                            10,
                            10,
                            1
                        ],
                        "total_wallet_exposure_limit": [
                            0,
                            0
                        ],
                        "total_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ],
                        "we_excess_allowance_pct": [
                            0,
                            0.3,
                            0.01
                        ],
                        "position_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ]
                    },
                    "strategy": {
                        "trailing_martingale": {
                            "volatility_ema_span_1h": [
                                672,
                                2016,
                                1
                            ],
                            "volatility_ema_span_1m": [
                                5,
                                720,
                                1
                            ],
                            "entry": {
                                "ema_span_0": [
                                    200,
                                    1440,
                                    10
                                ],
                                "ema_span_1": [
                                    200,
                                    1440,
                                    10
                                ],
                                "double_down_factor": [
                                    0.5,
                                    1,
                                    0.01
                                ],
                                "initial_ema_dist": [
                                    -0.01,
                                    0.01,
                                    0.0001
                                ],
                                "initial_qty_pct": [
                                    0.01,
                                    0.03,
                                    0.0001
                                ],
                                "threshold_base_pct": [
                                    0,
                                    0.04,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            },
                            "close": {
                                "qty_pct": [
                                    0.05,
                                    1,
                                    0.01
                                ],
                                "threshold_base_pct": [
                                    -0.02,
                                    0.02,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    -0.05,
                                    0.05,
                                    0.0001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            }
                        }
                    },
                    "unstuck": {
                        "ema_span_0": [
                            100,
                            100
                        ],
                        "ema_span_1": [
                            100,
                            100
                        ],
                        "close_pct": [
                            0.05,
                            0.12,
                            0.001
                        ],
                        "ema_dist": [
                            -0.2,
                            -0.07,
                            0.0001
                        ],
                        "loss_allowance_pct": [
                            0.005,
                            0.025,
                            0.0001
                        ],
                        "threshold": [
                            0.4,
                            0.9,
                            0.001
                        ]
                    }
                }
            },
            "compress_results_file": true,
            "crossover_eta": 20,
            "crossover_probability": 0.64,
            "enable_overrides": [],
            "fixed_params": [],
            "fixed_runtime_overrides": {
                "bot.long.hsl.no_restart_drawdown_threshold": 1,
                "bot.short.hsl.no_restart_drawdown_threshold": 1
            },
            "iters": 500000,
            "limits": [
                {
                    "metric": "drawdown_worst_btc",
                    "penalize_if": "greater_than",
                    "value": 0.9
                },
                {
                    "metric": "drawdown_worst_usd",
                    "penalize_if": "greater_than",
                    "value": 0.9
                },
                {
                    "metric": "loss_profit_ratio",
                    "penalize_if": "greater_than",
                    "value": 0.6
                },
                {
                    "metric": "adg_pnl",
                    "penalize_if": "less_than",
                    "reducer": "mean",
                    "value": 0.0009
                },
                {
                    "metric": "peak_recovery_hours_pnl",
                    "penalize_if": "greater_than",
                    "value": 1344
                },
                {
                    "metric": "position_held_hours_max",
                    "penalize_if": "greater_than",
                    "value": 1344
                },
                {
                    "metric": "position_unchanged_hours_max",
                    "penalize_if": "greater_than",
                    "value": 840
                }
            ],
            "mutation_eta": 20,
            "mutation_indpb": 0.05,
            "mutation_probability": 0.34,
            "n_cpus": 16,
            "offspring_multiplier": 1,
            "pareto_max_size": 250,
            "population_size": 250,
            "pymoo": {
                "algorithm": "auto",
                "algorithms": {
                    "nsga2": {},
                    "nsga3": {
                        "ref_dirs": {
                            "method": "das_dennis",
                            "n_partitions": "auto"
                        }
                    }
                },
                "shared": {
                    "crossover_eta": 20,
                    "crossover_prob_var": 0.64,
                    "eliminate_duplicates": true,
                    "mutation_eta": 20,
                    "mutation_prob": 0.05,
                    "mutation_prob_per_variable": "auto"
                }
            },
            "round_to_n_significant_digits": 3,
            "scoring": [
                {
                    "goal": "max",
                    "metric": "adg_pnl"
                },
                {
                    "goal": "max",
                    "metric": "mdg_pnl"
                },
                {
                    "goal": "min",
                    "metric": "loss_profit_ratio"
                },
                {
                    "goal": "min",
                    "metric": "peak_recovery_hours_pnl"
                },
                {
                    "goal": "min",
                    "metric": "position_held_hours_max"
                },
                {
                    "goal": "min",
                    "metric": "position_unchanged_hours_max"
                },
                {
                    "goal": "max",
                    "metric": "volume_pct_per_day_avg_w"
                },
                {
                    "goal": "max",
                    "metric": "entry_initial_balance_pct_long"
                }
            ],
            "write_all_results": true
        }
    },
    "_raw_effective": {
        "backtest": {
            "reducer": {
                "default": "mean",
                "drawdown_worst_hsl": "max",
                "drawdown_worst_mean_1pct_hsl": "max",
                "peak_recovery_hours_hsl": "max",
                "position_held_hours_max": "max"
            },
            "balance_sample_divider": 60,
            "base_dir": "backtests",
            "btc_collateral_cap": 0,
            "btc_collateral_ltv_cap": null,
            "candle_interval_minutes": 1,
            "coin_sources": {},
            "compress_cache": true,
            "dynamic_wel_by_tradability": true,
            "end_date": "now",
            "exchanges": [
                "binance"
            ],
            "filter_by_min_effective_cost": false,
            "gap_tolerance_ohlcvs_minutes": 120,
            "liquidation_threshold": 0.05,
            "maker_fee_override": 0.0004,
            "market_order_slippage_pct": 0.0005,
            "limit_order_fill_buffer_pct": 0,
            "market_settings_sources": {},
            "max_warmup_minutes": 0,
            "ohlcv_source_dir": null,
            "scenarios": [
                {
                    "label": "SOL_normal_osc_long"
                }
            ],
            "start_date": "2019-01-01",
            "starting_balance": 100000,
            "suite_enabled": false,
            "taker_fee_override": null,
            "visible_metrics": null,
            "volume_normalization": true
        },
        "bot": {
            "long": {
                "forager": {
                    "score_weights": {
                        "ema_readiness": 0,
                        "volatility": 1,
                        "volume": 0
                    },
                    "volatility_ema_span_1m": 101,
                    "volume_drop_pct": 0.884,
                    "volume_ema_span_1m": 1660
                },
                "risk": {
                    "entry_cooldown_minutes": 0,
                    "n_positions": 1,
                    "total_wallet_exposure_limit": 1,
                    "total_exposure_enforcer_enabled": true,
                    "total_exposure_enforcer_threshold": 0.99,
                    "we_excess_allowance_pct": 1.64,
                    "position_exposure_enforcer_enabled": true,
                    "position_exposure_enforcer_threshold": 0.99
                },
                "strategy": {
                    "trailing_martingale": {
                        "volatility_ema_span_1h": 1690,
                        "volatility_ema_span_1m": 60,
                        "entry": {
                            "ema_span_0": 770,
                            "ema_span_1": 210,
                            "double_down_factor": 0.74,
                            "initial_ema_dist": -0.0105,
                            "initial_qty_pct": 0.0261,
                            "threshold_base_pct": 0.037,
                            "threshold_we_weight": 0.135,
                            "threshold_volatility_1h_weight": 2.4,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_we_weight": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        },
                        "close": {
                            "qty_pct": 0.1,
                            "threshold_base_pct": 0.0067,
                            "threshold_we_weight": -0.004,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        }
                    }
                },
                "unstuck": {
                    "ema_span_0": 770,
                    "ema_span_1": 210,
                    "close_pct": 0.00936,
                    "ema_dist": -0.064,
                    "enabled": true,
                    "loss_allowance_pct": 0.00523,
                    "threshold": 0.833
                }
            },
            "short": {
                "forager": {
                    "score_weights": {
                        "ema_readiness": 0,
                        "volatility": 1,
                        "volume": 0
                    },
                    "volatility_ema_span_1m": 10,
                    "volume_drop_pct": 0.5,
                    "volume_ema_span_1m": 360
                },
                "hsl": {
                    "cooldown_minutes_after_red": 0,
                    "ema_span_minutes": 60,
                    "enabled": false,
                    "no_restart_drawdown_threshold": 1,
                    "orange_tier_mode": "tp_only_with_active_entry_cancellation",
                    "panic_close_order_type": "limit",
                    "red_threshold": 0.2,
                    "tier_ratios": {
                        "orange": 0.75,
                        "yellow": 0.5
                    }
                },
                "risk": {
                    "entry_cooldown_minutes": 0,
                    "n_positions": 1,
                    "total_wallet_exposure_limit": 0,
                    "total_exposure_enforcer_enabled": true,
                    "total_exposure_enforcer_threshold": 0.95,
                    "we_excess_allowance_pct": 0,
                    "position_exposure_enforcer_enabled": true,
                    "position_exposure_enforcer_threshold": 0.95
                },
                "strategy": {
                    "trailing_martingale": {
                        "volatility_ema_span_1h": 672,
                        "volatility_ema_span_1m": 60,
                        "entry": {
                            "ema_span_0": 100,
                            "ema_span_1": 100,
                            "double_down_factor": 0.5,
                            "initial_ema_dist": -0.01,
                            "initial_qty_pct": 0.01,
                            "threshold_base_pct": 0.025,
                            "threshold_we_weight": 0,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_we_weight": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        },
                        "close": {
                            "qty_pct": 0.1,
                            "threshold_base_pct": 0.006,
                            "threshold_we_weight": -0.004,
                            "threshold_volatility_1h_weight": 1,
                            "threshold_volatility_1m_weight": 0,
                            "retracement_base_pct": 0,
                            "retracement_volatility_1h_weight": 0,
                            "retracement_volatility_1m_weight": 0
                        }
                    }
                },
                "unstuck": {
                    "ema_span_0": 100,
                    "ema_span_1": 100,
                    "close_pct": 0.001,
                    "ema_dist": -0.1,
                    "enabled": true,
                    "loss_allowance_pct": 0.001,
                    "threshold": 0.4
                }
            }
        },
        "coin_overrides": {},
        "config_version": "v8.4.0",
        "live": {
            "approved_coins": {
                "long": [
                    "SOL"
                ],
                "short": []
            },
            "auto_gs": true,
            "balance_hysteresis_snap_pct": 0.02,
            "balance_override": null,
            "candle_lock_timeout_seconds": 10,
            "enable_archive_candle_fetch": false,
            "execution_delay_seconds": 2,
            "filter_by_min_effective_cost": true,
            "forced_mode_long": "",
            "forced_mode_short": "",
            "hedge_mode": false,
            "hsl_position_during_cooldown_policy": "panic",
            "hsl_signal_mode": "unified",
            "ignored_coins": {
                "long": [],
                "short": []
            },
            "inactive_coin_candle_ttl_minutes": 10,
            "leverage": 1,
            "margin_mode_preference": "cross",
            "market_order_near_touch_threshold": 0.001,
            "market_orders_allowed": false,
            "max_concurrent_api_requests": null,
            "max_disk_candles_per_symbol_per_tf": 2000000,
            "max_memory_candles_per_symbol": 200000,
            "max_n_cancellations_per_batch": 5,
            "max_n_creations_per_batch": 3,
            "max_n_restarts_per_day": 10,
            "max_ohlcv_fetches_per_minute": 30,
            "max_realized_loss_pct": 1,
            "max_warmup_minutes": 0,
            "minimum_coin_age_days": 0,
            "forager_score_hysteresis_pct": 0.005,
            "order_match_tolerance_pct": 0.0002,
            "pnls_max_lookback_days": 30,
            "recv_window_ms": 5000,
            "strategy_kind": "trailing_martingale",
            "time_in_force": "good_till_cancelled",
            "user": "bybit_01",
            "warmup_concurrency": 0,
            "warmup_jitter_seconds": 30,
            "warmup_ratio": 0.3
        },
        "logging": {
            "backup_count": 5,
            "dir": "logs",
            "level": 1,
            "max_bytes_mb": 10,
            "memory_snapshot_interval_minutes": 30,
            "persist_to_file": true,
            "rotation": false,
            "volume_refresh_info_threshold_seconds": 30
        },
        "monitor": {
            "checkpoint_interval_minutes": 10,
            "compress_rotated_segments": true,
            "emit_completed_candles": true,
            "enabled": true,
            "event_rotation_mb": 128,
            "event_rotation_minutes": 60,
            "include_raw_fill_payloads": false,
            "max_total_bytes": 1073741824,
            "price_tick_min_interval_ms": 500,
            "retain_candles": true,
            "retain_days": 7,
            "retain_fills": true,
            "retain_price_ticks": true,
            "root_dir": "monitor",
            "snapshot_interval_seconds": 1
        },
        "optimize": {
            "backend": "pymoo",
            "bounds": {
                "long": {
                    "forager": {
                        "score_weights_ema_readiness": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volatility": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volume": [
                            0,
                            1,
                            0.01
                        ],
                        "volatility_ema_span_1m": [
                            10,
                            720,
                            1
                        ],
                        "volume_drop_pct": [
                            0.4,
                            1,
                            0.01
                        ],
                        "volume_ema_span_1m": [
                            360,
                            2880,
                            10
                        ]
                    },
                    "hsl": {
                        "cooldown_minutes_after_red": [
                            1,
                            2880,
                            10
                        ],
                        "ema_span_minutes": [
                            1,
                            2880,
                            10
                        ],
                        "red_threshold": [
                            0.01,
                            0.12,
                            0.001
                        ]
                    },
                    "risk": {
                        "entry_cooldown_minutes": [
                            0,
                            60,
                            0.1
                        ],
                        "n_positions": [
                            10,
                            10,
                            1
                        ],
                        "total_wallet_exposure_limit": [
                            1.25,
                            1.25
                        ],
                        "total_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ],
                        "we_excess_allowance_pct": [
                            0,
                            0.3,
                            0.01
                        ],
                        "position_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ]
                    },
                    "strategy": {
                        "trailing_martingale": {
                            "volatility_ema_span_1h": [
                                672,
                                2016,
                                1
                            ],
                            "volatility_ema_span_1m": [
                                5,
                                720,
                                1
                            ],
                            "entry": {
                                "ema_span_0": [
                                    200,
                                    1440,
                                    10
                                ],
                                "ema_span_1": [
                                    200,
                                    1440,
                                    10
                                ],
                                "double_down_factor": [
                                    0.5,
                                    1,
                                    0.01
                                ],
                                "initial_ema_dist": [
                                    -0.01,
                                    0.01,
                                    0.0001
                                ],
                                "initial_qty_pct": [
                                    0.01,
                                    0.03,
                                    0.0001
                                ],
                                "threshold_base_pct": [
                                    0,
                                    0.04,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            },
                            "close": {
                                "qty_pct": [
                                    0.05,
                                    1,
                                    0.01
                                ],
                                "threshold_base_pct": [
                                    -0.02,
                                    0.02,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    -0.05,
                                    0.05,
                                    0.0001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            }
                        }
                    },
                    "unstuck": {
                        "ema_span_0": [
                            770,
                            770
                        ],
                        "ema_span_1": [
                            210,
                            210
                        ],
                        "close_pct": [
                            0.05,
                            0.12,
                            0.001
                        ],
                        "ema_dist": [
                            -0.2,
                            -0.07,
                            0.0001
                        ],
                        "loss_allowance_pct": [
                            0.005,
                            0.025,
                            0.0001
                        ],
                        "threshold": [
                            0.4,
                            0.9,
                            0.001
                        ]
                    }
                },
                "short": {
                    "forager": {
                        "score_weights_ema_readiness": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volatility": [
                            0,
                            1,
                            0.01
                        ],
                        "score_weights_volume": [
                            0,
                            1,
                            0.01
                        ],
                        "volatility_ema_span_1m": [
                            10,
                            720,
                            1
                        ],
                        "volume_drop_pct": [
                            0.4,
                            1,
                            0.01
                        ],
                        "volume_ema_span_1m": [
                            360,
                            2880,
                            10
                        ]
                    },
                    "hsl": {
                        "cooldown_minutes_after_red": [
                            1,
                            2880,
                            10
                        ],
                        "ema_span_minutes": [
                            1,
                            2880,
                            10
                        ],
                        "red_threshold": [
                            0.01,
                            0.12,
                            0.001
                        ]
                    },
                    "risk": {
                        "entry_cooldown_minutes": [
                            0,
                            60,
                            0.1
                        ],
                        "n_positions": [
                            10,
                            10,
                            1
                        ],
                        "total_wallet_exposure_limit": [
                            0,
                            0
                        ],
                        "total_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ],
                        "we_excess_allowance_pct": [
                            0,
                            0.3,
                            0.01
                        ],
                        "position_exposure_enforcer_threshold": [
                            0.95,
                            1.01,
                            0.001
                        ]
                    },
                    "strategy": {
                        "trailing_martingale": {
                            "volatility_ema_span_1h": [
                                672,
                                2016,
                                1
                            ],
                            "volatility_ema_span_1m": [
                                5,
                                720,
                                1
                            ],
                            "entry": {
                                "ema_span_0": [
                                    200,
                                    1440,
                                    10
                                ],
                                "ema_span_1": [
                                    200,
                                    1440,
                                    10
                                ],
                                "double_down_factor": [
                                    0.5,
                                    1,
                                    0.01
                                ],
                                "initial_ema_dist": [
                                    -0.01,
                                    0.01,
                                    0.0001
                                ],
                                "initial_qty_pct": [
                                    0.01,
                                    0.03,
                                    0.0001
                                ],
                                "threshold_base_pct": [
                                    0,
                                    0.04,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_we_weight": [
                                    0,
                                    5,
                                    0.001
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            },
                            "close": {
                                "qty_pct": [
                                    0.05,
                                    1,
                                    0.01
                                ],
                                "threshold_base_pct": [
                                    -0.02,
                                    0.02,
                                    1e-05
                                ],
                                "threshold_we_weight": [
                                    -0.05,
                                    0.05,
                                    0.0001
                                ],
                                "threshold_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "threshold_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_base_pct": [
                                    0,
                                    0.015,
                                    1e-05
                                ],
                                "retracement_volatility_1h_weight": [
                                    0,
                                    40,
                                    0.1
                                ],
                                "retracement_volatility_1m_weight": [
                                    0,
                                    40,
                                    0.1
                                ]
                            }
                        }
                    },
                    "unstuck": {
                        "ema_span_0": [
                            100,
                            100
                        ],
                        "ema_span_1": [
                            100,
                            100
                        ],
                        "close_pct": [
                            0.05,
                            0.12,
                            0.001
                        ],
                        "ema_dist": [
                            -0.2,
                            -0.07,
                            0.0001
                        ],
                        "loss_allowance_pct": [
                            0.005,
                            0.025,
                            0.0001
                        ],
                        "threshold": [
                            0.4,
                            0.9,
                            0.001
                        ]
                    }
                }
            },
            "compress_results_file": true,
            "crossover_eta": 20,
            "crossover_probability": 0.64,
            "enable_overrides": [],
            "fixed_params": [],
            "fixed_runtime_overrides": {
                "bot.long.hsl.no_restart_drawdown_threshold": 1,
                "bot.short.hsl.no_restart_drawdown_threshold": 1
            },
            "iters": 500000,
            "limits": [
                {
                    "metric": "drawdown_worst_btc",
                    "penalize_if": "greater_than",
                    "value": 0.9
                },
                {
                    "metric": "drawdown_worst_usd",
                    "penalize_if": "greater_than",
                    "value": 0.9
                },
                {
                    "metric": "loss_profit_ratio",
                    "penalize_if": "greater_than",
                    "value": 0.6
                },
                {
                    "metric": "adg_pnl",
                    "penalize_if": "less_than",
                    "reducer": "mean",
                    "value": 0.0009
                },
                {
                    "metric": "peak_recovery_hours_pnl",
                    "penalize_if": "greater_than",
                    "value": 1344
                },
                {
                    "metric": "position_held_hours_max",
                    "penalize_if": "greater_than",
                    "value": 1344
                },
                {
                    "metric": "position_unchanged_hours_max",
                    "penalize_if": "greater_than",
                    "value": 840
                }
            ],
            "mutation_eta": 20,
            "mutation_indpb": 0.05,
            "mutation_probability": 0.34,
            "n_cpus": 16,
            "offspring_multiplier": 1,
            "pareto_max_size": 250,
            "population_size": 250,
            "pymoo": {
                "algorithm": "auto",
                "algorithms": {
                    "nsga2": {},
                    "nsga3": {
                        "ref_dirs": {
                            "method": "das_dennis",
                            "n_partitions": "auto"
                        }
                    }
                },
                "shared": {
                    "crossover_eta": 20,
                    "crossover_prob_var": 0.64,
                    "eliminate_duplicates": true,
                    "mutation_eta": 20,
                    "mutation_prob": 0.05,
                    "mutation_prob_per_variable": "auto"
                }
            },
            "round_to_n_significant_digits": 3,
            "scoring": [
                {
                    "goal": "max",
                    "metric": "adg_pnl"
                },
                {
                    "goal": "max",
                    "metric": "mdg_pnl"
                },
                {
                    "goal": "min",
                    "metric": "loss_profit_ratio"
                },
                {
                    "goal": "min",
                    "metric": "peak_recovery_hours_pnl"
                },
                {
                    "goal": "min",
                    "metric": "position_held_hours_max"
                },
                {
                    "goal": "min",
                    "metric": "position_unchanged_hours_max"
                },
                {
                    "goal": "max",
                    "metric": "volume_pct_per_day_avg_w"
                },
                {
                    "goal": "max",
                    "metric": "entry_initial_balance_pct_long"
                }
            ],
            "write_all_results": true
        }
    },
    "_coins_sources": {
        "approved_coins": {
            "long": [
                "SOL"
            ],
            "short": []
        },
        "ignored_coins": {
            "long": [],
            "short": []
        }
    },
    "_transform_log": [
        {
            "step": "normalize_config",
            "ts_ms": 1790895979897,
            "details": {
                "live_only": false,
                "base_config_path": "",
                "flavor": "current",
                "changes": [
                    {
                        "action": "add",
                        "path": "bot.long.hsl",
                        "value": {
                            "__dict__": {}
                        }
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.cooldown_minutes_after_red",
                        "value": 2160.0
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.ema_span_minutes",
                        "value": 720.0
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.enabled",
                        "value": false
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.no_restart_drawdown_threshold",
                        "value": 1
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.orange_tier_mode",
                        "value": "tp_only_with_active_entry_cancellation"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.panic_close_order_type",
                        "value": "limit"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.red_threshold",
                        "value": 0.15
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.restart_after_red_policy",
                        "value": "threshold"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.hsl.tier_ratios",
                        "value": {
                            "__dict__": {
                                "orange": 0.75,
                                "yellow": 0.5
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "bot.long.risk.total_exposure_enforcer_policy",
                        "value": "reduce_overweight"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.risk.total_exposure_entry_gate_enabled",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "bot.long.risk.we_excess_allowance_mode",
                        "value": "bounded"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.unstuck.ema_gating_enabled",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "bot.long.strategy.trailing_martingale.entry.ema_gate_mode",
                        "value": "all"
                    },
                    {
                        "action": "add",
                        "path": "bot.long.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": 0.01,
                                "ema_span_0": 200.0,
                                "ema_span_1": 800.0,
                                "entry_double_down_factor": 0.0,
                                "offset": 0.002,
                                "offset_volatility_ema_span_1m": 60.0,
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "bot.long.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": 385.0,
                                "ema_span_1": 620.0,
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": 1.39,
                                        "grid_spacing_pct": 0.02312,
                                        "grid_spacing_we_weight": 0.6766,
                                        "grid_spacing_volatility_weight": 17.8,
                                        "initial_ema_dist": 0.0078,
                                        "initial_qty_pct": 0.0122,
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": 0.01041,
                                        "grid_markup_end": 0.00241,
                                        "grid_qty_pct": 0.88,
                                        "trailing_grid_ratio": -0.07,
                                        "trailing_qty_pct": 0.89,
                                        "trailing_retracement_pct": 0.00413,
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "bot.short.hsl.restart_after_red_policy",
                        "value": "threshold"
                    },
                    {
                        "action": "add",
                        "path": "bot.short.risk.total_exposure_enforcer_policy",
                        "value": "reduce_overweight"
                    },
                    {
                        "action": "add",
                        "path": "bot.short.risk.total_exposure_entry_gate_enabled",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "bot.short.risk.we_excess_allowance_mode",
                        "value": "bounded"
                    },
                    {
                        "action": "add",
                        "path": "bot.short.unstuck.ema_gating_enabled",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "bot.short.strategy.trailing_martingale.entry.ema_gate_mode",
                        "value": "all"
                    },
                    {
                        "action": "add",
                        "path": "bot.short.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": 0.01,
                                "ema_span_0": 200.0,
                                "ema_span_1": 800.0,
                                "entry_double_down_factor": 0.0,
                                "offset": 0.002,
                                "offset_volatility_ema_span_1m": 60.0,
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "bot.short.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": 300.0,
                                "ema_span_1": 700.0,
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": 1.0,
                                        "grid_spacing_pct": 0.02,
                                        "grid_spacing_we_weight": 1.0,
                                        "grid_spacing_volatility_weight": 10.0,
                                        "initial_ema_dist": 0.01,
                                        "initial_qty_pct": 0.01,
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": 0.00402,
                                        "grid_markup_end": 0.00223,
                                        "grid_qty_pct": 0.5,
                                        "trailing_grid_ratio": -0.03,
                                        "trailing_qty_pct": 0.5,
                                        "trailing_retracement_pct": 0.005,
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "optimize.bounds.long.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": [
                                    0.001,
                                    0.05,
                                    0.0001
                                ],
                                "ema_span_0": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry_double_down_factor": [
                                    0.0,
                                    2.0,
                                    0.01
                                ],
                                "offset": [
                                    0.0,
                                    0.05,
                                    0.0001
                                ],
                                "offset_volatility_ema_span_1m": [
                                    5.0,
                                    720.0,
                                    1.0
                                ],
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "optimize.bounds.long.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": [
                                            0.0,
                                            2.0,
                                            0.01
                                        ],
                                        "grid_spacing_pct": [
                                            0.001,
                                            0.03,
                                            0.0001
                                        ],
                                        "grid_spacing_we_weight": [
                                            0.0,
                                            10.0,
                                            0.001
                                        ],
                                        "grid_spacing_volatility_weight": [
                                            0.0,
                                            50.0,
                                            0.01
                                        ],
                                        "initial_ema_dist": [
                                            -0.1,
                                            0.02,
                                            0.0001
                                        ],
                                        "initial_qty_pct": [
                                            0.005,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": [
                                            0.0015,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_markup_end": [
                                            -0.1,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_grid_ratio": [
                                            -1.0,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_retracement_pct": [
                                            0.0,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "optimize.bounds.short.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": [
                                    0.001,
                                    0.05,
                                    0.0001
                                ],
                                "ema_span_0": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry_double_down_factor": [
                                    0.0,
                                    2.0,
                                    0.01
                                ],
                                "offset": [
                                    0.0,
                                    0.05,
                                    0.0001
                                ],
                                "offset_volatility_ema_span_1m": [
                                    5.0,
                                    720.0,
                                    1.0
                                ],
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "optimize.bounds.short.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": [
                                            0.0,
                                            2.0,
                                            0.01
                                        ],
                                        "grid_spacing_pct": [
                                            0.001,
                                            0.03,
                                            0.0001
                                        ],
                                        "grid_spacing_we_weight": [
                                            0.0,
                                            10.0,
                                            0.001
                                        ],
                                        "grid_spacing_volatility_weight": [
                                            0.0,
                                            50.0,
                                            0.01
                                        ],
                                        "initial_ema_dist": [
                                            -0.1,
                                            0.02,
                                            0.0001
                                        ],
                                        "initial_qty_pct": [
                                            0.005,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": [
                                            0.0015,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_markup_end": [
                                            -0.1,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_grid_ratio": [
                                            -1.0,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_retracement_pct": [
                                            0.0,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "backtest.hsl_detailed_report",
                        "value": false
                    },
                    {
                        "action": "add",
                        "path": "backtest.hlcvs_data_dir",
                        "value": null
                    },
                    {
                        "action": "add",
                        "path": "backtest.hlcvs_data_override_mode",
                        "value": "intersection"
                    },
                    {
                        "action": "add",
                        "path": "backtest.market_settings",
                        "value": {
                            "__dict__": {
                                "overrides": {
                                    "__dict__": {}
                                },
                                "overrides_by_exchange": {
                                    "__dict__": {}
                                }
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "backtest.offline",
                        "value": false
                    },
                    {
                        "action": "add",
                        "path": "live.custom_endpoints_path",
                        "value": null
                    },
                    {
                        "action": "add",
                        "path": "live.defer_broad_candle_warmup",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "live.enable_forager_ws_candles",
                        "value": true
                    },
                    {
                        "action": "add",
                        "path": "live.exchange_symbol_unavailable_cooldown_hours",
                        "value": 6.0
                    },
                    {
                        "action": "add",
                        "path": "live.fee_conversion_max_age_ms",
                        "value": 86400000
                    },
                    {
                        "action": "add",
                        "path": "live.fee_pct_fallback",
                        "value": 0.0002
                    },
                    {
                        "action": "add",
                        "path": "live.fee_pct_sanity_abs_max",
                        "value": 0.001
                    },
                    {
                        "action": "add",
                        "path": "live.fills_confirmation_overlap_minutes",
                        "value": 60
                    },
                    {
                        "action": "add",
                        "path": "live.fills_recent_overlap_minutes",
                        "value": 10
                    },
                    {
                        "action": "add",
                        "path": "live.forager_ws_candle_rest_audit_minutes",
                        "value": 30
                    },
                    {
                        "action": "add",
                        "path": "live.force_cold_startup",
                        "value": false
                    },
                    {
                        "action": "add",
                        "path": "live.hsl_accept_incomplete_history",
                        "value": false
                    },
                    {
                        "action": "add",
                        "path": "live.hsl_unavailable_grace_seconds",
                        "value": 120.0
                    },
                    {
                        "action": "add",
                        "path": "live.limit_order_create_max_market_dist_pct",
                        "value": 0.8
                    },
                    {
                        "action": "add",
                        "path": "live.market_snapshot_ticker_strategy",
                        "value": "auto"
                    },
                    {
                        "action": "add",
                        "path": "live.max_active_candle_tail_gap_minutes",
                        "value": 10
                    },
                    {
                        "action": "add",
                        "path": "live.max_forager_candle_refresh_seconds",
                        "value": 45
                    },
                    {
                        "action": "add",
                        "path": "live.max_forager_candle_staleness_minutes",
                        "value": null
                    },
                    {
                        "action": "add",
                        "path": "live.order_replacement_churn_gate_activation_count",
                        "value": 10
                    },
                    {
                        "action": "add",
                        "path": "live.order_replacement_churn_gate_market_dist_pct",
                        "value": 0.005
                    },
                    {
                        "action": "add",
                        "path": "live.order_replacement_churn_gate_stability_minutes",
                        "value": 2.0
                    },
                    {
                        "action": "add",
                        "path": "live.order_replacement_churn_gate_window_minutes",
                        "value": 10.0
                    },
                    {
                        "action": "add",
                        "path": "live.risk_input_max_attempts",
                        "value": 10
                    },
                    {
                        "action": "add",
                        "path": "live.startup_phase_budgets",
                        "value": {
                            "__dict__": {}
                        }
                    },
                    {
                        "action": "add",
                        "path": "logging.live_event_debug_profiles",
                        "value": []
                    },
                    {
                        "action": "add",
                        "path": "optimize.objective_scenario",
                        "value": null
                    },
                    {
                        "action": "add",
                        "path": "optimize.seed",
                        "value": null
                    },
                    {
                        "action": "add",
                        "path": "optimize.gpu",
                        "value": {
                            "__dict__": {
                                "auto_lean_parallelism": true,
                                "batch_size": null,
                                "max_dispatch_candidate_bars": null,
                                "checkpoint_interval_seconds": 5.0,
                                "drift_halt": 0.6,
                                "drift_rank_halt": null,
                                "...": "10 more keys"
                            }
                        }
                    },
                    {
                        "action": "add",
                        "path": "live.base_config_path",
                        "value": ""
                    },
                    {
                        "action": "remove",
                        "path": "backtest.max_warmup_minutes",
                        "value": 0
                    },
                    {
                        "action": "remove",
                        "path": "bot.long.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": 0.01,
                                "ema_span_0": 200.0,
                                "ema_span_1": 800.0,
                                "entry_double_down_factor": 0.0,
                                "offset": 0.002,
                                "offset_psize_weight": 0.1,
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "bot.long.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "close": {
                                    "__dict__": {
                                        "grid_markup_end": 0.00241,
                                        "grid_markup_start": 0.01041,
                                        "grid_qty_pct": 0.88,
                                        "trailing_grid_ratio": -0.07,
                                        "trailing_qty_pct": 0.89,
                                        "trailing_retracement_pct": 0.00413,
                                        "...": "1 more keys"
                                    }
                                },
                                "ema_span_0": 385.0,
                                "ema_span_1": 620.0,
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": 1.39,
                                        "grid_spacing_pct": 0.02312,
                                        "grid_spacing_volatility_weight": 17.8,
                                        "grid_spacing_we_weight": 0.6766,
                                        "initial_ema_dist": 0.0078,
                                        "initial_qty_pct": 0.0122,
                                        "...": "9 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "bot.short.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": 0.01,
                                "ema_span_0": 200.0,
                                "ema_span_1": 800.0,
                                "entry_double_down_factor": 0.0,
                                "offset": 0.002,
                                "offset_psize_weight": 0.1,
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "bot.short.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "close": {
                                    "__dict__": {
                                        "grid_markup_end": 0.00223,
                                        "grid_markup_start": 0.00402,
                                        "grid_qty_pct": 0.5,
                                        "trailing_grid_ratio": -0.03,
                                        "trailing_qty_pct": 0.5,
                                        "trailing_retracement_pct": 0.005,
                                        "...": "1 more keys"
                                    }
                                },
                                "ema_span_0": 300.0,
                                "ema_span_1": 700.0,
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": 1.0,
                                        "grid_spacing_pct": 0.02,
                                        "grid_spacing_volatility_weight": 10.0,
                                        "grid_spacing_we_weight": 1.0,
                                        "initial_ema_dist": 0.01,
                                        "initial_qty_pct": 0.01,
                                        "...": "9 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "optimize.bounds.long.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": [
                                    0.001,
                                    0.05,
                                    0.0001
                                ],
                                "ema_span_0": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry_double_down_factor": [
                                    0.0,
                                    2.0,
                                    0.01
                                ],
                                "offset": [
                                    0.0,
                                    0.05,
                                    0.0001
                                ],
                                "offset_volatility_ema_span_1m": [
                                    5.0,
                                    720.0,
                                    1.0
                                ],
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "optimize.bounds.long.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": [
                                            0.0,
                                            2.0,
                                            0.01
                                        ],
                                        "grid_spacing_pct": [
                                            0.001,
                                            0.03,
                                            0.0001
                                        ],
                                        "grid_spacing_we_weight": [
                                            0.0,
                                            10.0,
                                            0.001
                                        ],
                                        "grid_spacing_volatility_weight": [
                                            0.0,
                                            50.0,
                                            0.01
                                        ],
                                        "initial_ema_dist": [
                                            -0.1,
                                            0.02,
                                            0.0001
                                        ],
                                        "initial_qty_pct": [
                                            0.005,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": [
                                            0.0015,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_markup_end": [
                                            -0.1,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_grid_ratio": [
                                            -1.0,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_retracement_pct": [
                                            0.0,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "optimize.bounds.short.strategy.ema_anchor",
                        "value": {
                            "__dict__": {
                                "base_qty_pct": [
                                    0.001,
                                    0.05,
                                    0.0001
                                ],
                                "ema_span_0": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    20.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry_double_down_factor": [
                                    0.0,
                                    2.0,
                                    0.01
                                ],
                                "offset": [
                                    0.0,
                                    0.05,
                                    0.0001
                                ],
                                "offset_volatility_ema_span_1m": [
                                    5.0,
                                    720.0,
                                    1.0
                                ],
                                "...": "4 more keys"
                            }
                        }
                    },
                    {
                        "action": "remove",
                        "path": "optimize.bounds.short.strategy.trailing_grid_v7",
                        "value": {
                            "__dict__": {
                                "ema_span_0": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "ema_span_1": [
                                    200.0,
                                    1440.0,
                                    1.0
                                ],
                                "entry": {
                                    "__dict__": {
                                        "grid_double_down_factor": [
                                            0.0,
                                            2.0,
                                            0.01
                                        ],
                                        "grid_spacing_pct": [
                                            0.001,
                                            0.03,
                                            0.0001
                                        ],
                                        "grid_spacing_we_weight": [
                                            0.0,
                                            10.0,
                                            0.001
                                        ],
                                        "grid_spacing_volatility_weight": [
                                            0.0,
                                            50.0,
                                            0.01
                                        ],
                                        "initial_ema_dist": [
                                            -0.1,
                                            0.02,
                                            0.0001
                                        ],
                                        "initial_qty_pct": [
                                            0.005,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "9 more keys"
                                    }
                                },
                                "close": {
                                    "__dict__": {
                                        "grid_markup_start": [
                                            0.0015,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_markup_end": [
                                            -0.1,
                                            0.012,
                                            1e-05
                                        ],
                                        "grid_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_grid_ratio": [
                                            -1.0,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_qty_pct": [
                                            0.05,
                                            1.0,
                                            0.01
                                        ],
                                        "trailing_retracement_pct": [
                                            0.0,
                                            0.1,
                                            0.0001
                                        ],
                                        "...": "1 more keys"
                                    }
                                }
                            }
                        }
                    }
                ]
            }
        }
    ]
}
```

# 13. 建议的第一轮回测矩阵

不要一次把所有参数全部优化，否则很容易产生过拟合。

### 第一轮：只测试 4 个核心参数

- `initial_qty_pct`
- `double_down_factor`
- `initial_ema_dist`
- `threshold_base_pct`

### BTC

```text
initial_qty_pct      0.015 / 0.018 / 0.021
double_down_factor   0.62 / 0.68 / 0.74
initial_ema_dist    -0.006 / -0.008 / -0.010
threshold_base_pct   0.018 / 0.020 / 0.022
```

### ETH

```text
initial_qty_pct      0.014 / 0.017 / 0.020
double_down_factor   0.64 / 0.70 / 0.76
initial_ema_dist    -0.009 / -0.0115 / -0.014
threshold_base_pct   0.022 / 0.024 / 0.027
```

### SOL

```text
initial_qty_pct      0.009 / 0.012 / 0.015
double_down_factor   0.60 / 0.66 / 0.72
initial_ema_dist    -0.013 / -0.016 / -0.019
threshold_base_pct   0.028 / 0.032 / 0.036
```

第二轮再优化：

```text
threshold_volatility_1h_weight
unstuck.close_pct
unstuck.loss_allowance_pct
unstuck.threshold
```

不要第一轮就同时优化 10~20 个参数。

# 14. 最终建议

如果你的目标仍然是：

> **低频手动启动 + Passivbot 自动挂单 + 0 Maker 手续费 + 尽量少人工盯盘 + 稳定优先**

那么建议把 Passivbot 定义成：

**“震荡环境自动执行器”，而不是“全天候交易机器人”。**

人工真正需要做的不是判断每一笔买卖，而是判断：

> **现在是不是值得把机器人打开。**

其中最重要的三个开关指标可以简化为：

```text
4H ADX       → 判断有没有趋势
ATR%分位     → 判断波动是否失控
1H EMA结构   → 判断是不是正常震荡
```

然后用 `15M RSI + 成交量 + OI` 做最后确认。

**BTC：最宽松**  
**ETH：中等**  
**SOL：最严格**

这比给三个币使用同一套 Passivbot 参数更符合 `trailing_martingale` 的风险结构。
