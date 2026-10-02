# BTC / ETH / XRP / SOL / ADA 多空配置(注释版)

`configs/examples/BTC_ETH_XRP_SOL_ADA_long.json` 的注释参考版,参数值与该文件完全一致。

- 注释采用 HJSON 风格 `//`,仓库配置加载器(`src/config/parse.py`)使用 hjson 解析,可自动忽略注释。
- 但 Markdown 代码围栏不会被加载器剥离,直接把本文件传给 bot/回测/优化会解析失败;实际运行请使用同名 `.json` 文件。
- 比例类参数均为小数(0.01 = 1%);暴露(wallet exposure)= |仓位| × 价格 × 倍率 / 余额。

```json
{
    // ==================== 回测 ====================
    "backtest": {
        // 多场景(suite)结果的聚合方式:指标名 -> 统计量(min/max/mean/std/median)
        // 未单独列出的指标使用 default;回撤/时长类取 max(各场景最差值)
        "reducer": {
            "default": "mean", // 其余指标默认取均值
            "drawdown_worst_hsl": "max", // HSL 最差回撤取最坏
            "drawdown_worst_mean_1pct_hsl": "max", // HSL 1% 均值最差回撤取最坏
            "peak_recovery_hours_hsl": "max",
            "position_held_hours_max": "max"
        },
        // balance/equity 时间序列降采样:每 60 分钟一个采样点(1 = 每分钟)
        "balance_sample_divider": 60,
        // 回测结果输出根目录
        "base_dir": "backtests",
        // BTC 抵押占比:0 = 全 USD 抵押,1 = 全 BTC;0.7 表示 70% 权益转为 BTC 抵押
        "btc_collateral_cap": 0.7,
        // BTC 抵押的 LTV(负债/权益)上限;null = 不限制
        "btc_collateral_ltv_cap": null,
        // K 线聚合周期(分钟):1 = 原生 1m;调大可加速回测,但丢失周期内的成交顺序
        "candle_interval_minutes": 1,
        // 个别币种指定 K 线来源交易所(如 {"BTC": "binance"});空 = 自动选最佳数据源
        "coin_sources": {},
        // 压缩 OHLCV/回测缓存(true 省磁盘,false 加载更快)
        "compress_cache": true,
        // true: 单币 WEL 分母按“出现过 K 线的最多币数”动态调整;false: 固定 TWEL/n_positions
        "dynamic_wel_by_tradability": true,
        // 回测结束时间;"now" 解析为当前 UTC 日
        "end_date": "now",
        // 参与 K 线合并的交易所;多于一个时按币种自动选最佳数据源
        "exchanges": [
            "binance",
            "bybit"
        ],
        // 剔除初始入场预算低于交易所最小有效下单成本的币(回测默认关,实盘默认开)
        "filter_by_min_effective_cost": false,
        // 数据准备时允许填补的 K 线缺口上限(分钟);更大缺口将被剔除出可交易窗口
        "gap_tolerance_ohlcvs_minutes": 120,
        // 提前终止线:总权益 <= 起始资金 x 5% 时结束回测(是权益下限,不是回撤百分比)
        "liquidation_threshold": 0.05,
        // 覆盖 maker 费率(0.0004 = 0.04%);null = 用交易所费率
        "maker_fee_override": 0.0004,
        // 模拟市价单滑点(0.0005 = 0.05%),作用于 HSL 恐慌平仓及被提升为市价的订单
        "market_order_slippage_pct": 0.0005,
        // 限价单成交缓冲:买单需 low < 限价x(1-缓冲)、卖单需 high > 限价x(1+缓冲)才成交;0 = 触及即成交
        "limit_order_fill_buffer_pct": 0.0,
        // 个别币种指定市场元数据(步长/费率/最小下单量)来源交易所
        "market_settings_sources": {},
        // 预热窗口硬上限(分钟);0 = 不限制(按 EMA 跨度自动计算)
        "max_warmup_minutes": 0,
        // 直接读取外部 OHLCV 目录;null = 使用内置缓存/交易所下载
        "ohlcv_source_dir": null,
        // 多场景定义(suite_enabled=true 时生效):base 为全量 5 币;
        // subset1~5 各剔除一个币(稳健性检验);
        // pure_trailing / pure_grid 自 2024-07 起,通过覆盖 retracement_base_pct
        // 对比“追踪入场+追踪止盈”(0.005)与“纯网格”(0)两种模式
        "scenarios": [
            {
                "label": "base" // 基准:全部 5 币
            },
            {
                "coins": [
                    "ADA",
                    "BTC",
                    "ETH",
                    "SOL"
                ],
                "label": "subset1" // 剔除 XRP
            },
            {
                "coins": [
                    "ADA",
                    "BTC",
                    "ETH",
                    "XRP"
                ],
                "label": "subset2" // 剔除 SOL
            },
            {
                "coins": [
                    "ADA",
                    "BTC",
                    "SOL",
                    "XRP"
                ],
                "label": "subset3" // 剔除 ETH
            },
            {
                "coins": [
                    "ADA",
                    "ETH",
                    "SOL",
                    "XRP"
                ],
                "label": "subset4" // 剔除 BTC
            },
            {
                "coins": [
                    "BTC",
                    "ETH",
                    "SOL",
                    "XRP"
                ],
                "label": "subset5" // 剔除 ADA
            },
            {
                "label": "pure_trailing", // 追踪模式对照(入场+止盈均加 0.5% 回踩确认)
                "overrides": {
                    "bot.long.strategy.trailing_martingale.close.retracement_base_pct": 0.005,
                    "bot.long.strategy.trailing_martingale.entry.retracement_base_pct": 0.005
                },
                "start_date": "2024-07"
            },
            {
                "label": "pure_grid", // 纯网格对照(显式置 0,与基准同型但窗口相同)
                "overrides": {
                    "bot.long.strategy.trailing_martingale.close.retracement_base_pct": 0,
                    "bot.long.strategy.trailing_martingale.entry.retracement_base_pct": 0
                },
                "start_date": "2024-07"
            }
        ],
        // 回测开始时间
        "start_date": "2021-03-01",
        // 起始资金(USD),也是 liquidation_threshold 的锚点
        "starting_balance": 100000,
        // 多场景模式总开关;true 时依次跑 scenarios 并按 reducer 聚合
        "suite_enabled": false,
        // 覆盖 taker 费率;null = 用交易所费率
        "taker_fee_override": null,
        // 独立回测打印哪些指标:null = 按 optimize.scoring/limits 推断,[] = 全部
        "visible_metrics": null,
        // 多交易所数据合并时对成交量做跨所归一化(按各所/币日对数量比中位数换算)
        "volume_normalization": true
    },
    // ==================== 机器人交易参数 ====================
    "bot": {
        "long": {
            // ---- 选币器:从 approved_coins 中为空槽位挑币 ----
            "forager": {
                // 选币评分权重(归一化后使用):ema_readiness = 价格距入场 EMA 带的接近度,
                // volatility = 1m 对数振幅 EMA(越高越好),volume = 成交量 EMA(越高越好)
                // 此处全押波动率:优先选波动最大的币
                "score_weights": {
                    "ema_readiness": 0.0,
                    "volatility": 1.0,
                    "volume": 0.0
                },
                // 波动率特征的 EMA 跨度(分钟,基于 1m K 线对数振幅 ln(high/low))
                "volatility_ema_span_1m": 101,
                // 低量裁剪:剔除成交量 EMA 最低 88.4% 分位的候选(至少保留够填满空槽位的数量)
                "volume_drop_pct": 0.884,
                // 成交量特征的 EMA 跨度(分钟,基于 1m K 线报价成交量)
                "volume_ema_span_1m": 1660
            },
            // ---- 权益硬止损 HSL(本配置未启用;以下为 legacy 引擎字段)----
            "hsl": {
                // 红色熔断平仓后的冷却分钟数;legacy 引擎中 0 = 该侧不自动重启
                "cooldown_minutes_after_red": 0,
                // 回撤信号 EMA 平滑跨度(分钟);触发分值 = min(原始回撤, EMA 回撤)
                "ema_span_minutes": 60,
                // 是否启用该侧 HSL 熔断
                "enabled": false,
                // 红色事件结束后跨重启回撤达到该阈值则永久停机;1 = 实际上不触发
                "no_restart_drawdown_threshold": 1,
                // 橙色档行为:仅平仓、撤销未成交入场单
                "orange_tier_mode": "tp_only_with_active_entry_cancellation",
                // 红色恐慌平仓单类型(limit = 限价;market = 市价,回测按滑点成交)
                "panic_close_order_type": "limit",
                // 回撤达到 20% 触发红色:恐慌平掉该侧全部持仓并停机
                "red_threshold": 0.2,
                // 黄/橙档阈值 = red_threshold x 比例:黄 10%、橙 15%(预警降风险档)
                "tier_ratios": {
                    "orange": 0.75,
                    "yellow": 0.5
                }
            },
            // ---- 风险与仓位约束 ----
            "risk": {
                // 同币加仓成交后的冷却分钟数(0 = 不限;>0 时入场阶梯逐单推进)
                "entry_cooldown_minutes": 0.0,
                // 该侧最多同时持有的仓位数;也是单币基础 WEL = TWEL/n_positions 的分母
                "n_positions": 4,
                // 该侧总钱包暴露上限(TWEL);此处 1 = 最多用掉 1 倍余额
                "total_wallet_exposure_limit": 1,
                // 总暴露执行器:同侧总暴露 > TWEL x 阈值时对受管仓位发 reduce-only 减仓
                "total_exposure_enforcer_enabled": true,
                "total_exposure_enforcer_threshold": 0.99,
                // 单仓位可借用未用槽位额度的超额比例(bounded 模式下有效 WEL 不超过 TWEL)
                // 本配置:基础 WEL=1/4=0.25,有效 WEL 最高 0.25x(1+1.64)=0.66 倍余额
                "we_excess_allowance_pct": 1.64,
                // 单仓位暴露执行器:仓位暴露 > 有效WEL x 阈值时修剪回目标(不受 EMA/亏损额度限制)
                "position_exposure_enforcer_enabled": true,
                "position_exposure_enforcer_threshold": 0.99
            },
            // ---- 追踪马丁格尔策略 ----
            "strategy": {
                "trailing_martingale": {
                    // 波动率 EMA 跨度:1h 项按小时桶(1690 小时),1m 项按 1m K 线(60 分钟)
                    // 用于放大/缩小入场与止盈的阈值、回踩距离
                    "volatility_ema_span_1h": 1690,
                    "volatility_ema_span_1m": 60.0,
                    "entry": {
                        // 入场 EMA 带跨度(分钟):带 = min/max(span_0, span_1, sqrt(span_0*span_1))
                        "ema_span_0": 770,
                        "ema_span_1": 210,
                        // 补仓量系数:下一次补仓量 = 当前仓位 x 0.73(与初始量下限取大,受暴露上限裁剪)
                        "double_down_factor": 0.73,
                        // 首次入场价距 EMA 带的距离:多头 = min(买一, 下轨x(1-0.97%)),正值 = 低于下轨挂单
                        "initial_ema_dist": 0.0097,
                        // 首次入场量 = 余额 x 有效WEL x 2.76% / 价格(同时是每次补仓量的下限)
                        "initial_qty_pct": 0.0276,
                        // 补仓基准距离:距持仓均价 3.3%,乘以 max(1, 1 + 暴露项 + 波动项)
                        "threshold_base_pct": 0.033,
                        // 暴露项:(wel/基础WEL) x 0.135 —— 暴露越深,下次补仓越远
                        "threshold_we_weight": 0.135,
                        "threshold_volatility_1h_weight": 2.4, // 1h 波动率 x 2.4 放大补仓距离
                        "threshold_volatility_1m_weight": 0.0, // 未启用
                        // 0 = 网格模式:补仓为被动递归限价单;>0 = 追踪模式(先突破阈值,再回踩确认)
                        "retracement_base_pct": 0.0,
                        "retracement_we_weight": 0.0, // 回踩距离的暴露/波动放大项(网格模式下无效)
                        "retracement_volatility_1h_weight": 0.0,
                        "retracement_volatility_1m_weight": 0.0
                    },
                    "close": {
                        // 递归止盈时每片平掉当前仓位的 10%(threshold_we_weight != 0 启用递归阶梯)
                        "qty_pct": 0.1,
                        // 止盈基准距离 0.6%(加性公式:base + (wel/基础WEL)xwe_weight + 波动项)
                        "threshold_base_pct": 0.006,
                        "threshold_we_weight": -0.004, // 暴露越深,止盈越近(负权重)
                        "threshold_volatility_1h_weight": 1.0, // 1h 波动率抬升止盈距离
                        "threshold_volatility_1m_weight": 0.0,
                        // 0 = 普通限价止盈;>0 = 追踪止盈(先触及阈值,再回踩才平)
                        "retracement_base_pct": 0.0,
                        "retracement_volatility_1h_weight": 0.0,
                        "retracement_volatility_1m_weight": 0.0
                    }
                }
            },
            // ---- 自动解套:亏损减仓、回收卡住的仓位 ----
            "unstuck": {
                // 解套专用 EMA 带跨度(分钟),独立于策略跨度
                "ema_span_0": 770.0,
                "ema_span_1": 210.0,
                // 每次解套平仓量 = 余额 x 有效WEL x 0.936% / 平仓价(占暴露预算,非仓位比例)
                "close_pct": 0.00936,
                // 触发偏移:多头价格 >= 上轨x(1-0.064) 即可解套;负值 = 提前(更积极)
                "ema_dist": -0.064,
                // 是否启用自动解套
                "enabled": true,
                // 已实现亏损预算:允许亏损 = 0.523% x TWEL x 余额峰值(按 pnls_max_lookback_days 滚动重建)
                "loss_allowance_pct": 0.00523,
                // 资格门槛:仓位暴露/有效WEL 严格大于 0.833 才候选(不是目标仓位)
                "threshold": 0.833
            }
        },
        "short": { // 空头侧:TWEL=0 表示完全禁用,以下参数仅在启用后生效
            // ---- 选币器 ----
            "forager": {
                "score_weights": { // 权重同多头:全押波动率
                    "ema_readiness": 0.0,
                    "volatility": 1.0,
                    "volume": 0.0
                },
                "volatility_ema_span_1m": 10, // 波动率 EMA 跨度(分钟)
                "volume_drop_pct": 0.5, // 剔除成交量 EMA 最低 50% 分位的候选
                "volume_ema_span_1m": 360 // 成交量 EMA 跨度(分钟)
            },
            // ---- HSL(未启用)----
            "hsl": {
                "cooldown_minutes_after_red": 0, // 0 = 该侧不自动重启
                "ema_span_minutes": 60, // 回撤信号 EMA 平滑跨度(分钟)
                "enabled": false,
                "no_restart_drawdown_threshold": 1, // 1 = 实际上不触发永久停机
                "orange_tier_mode": "tp_only_with_active_entry_cancellation",
                "panic_close_order_type": "limit",
                "red_threshold": 0.2, // 回撤 20% 触发红色熔断
                "tier_ratios": { // 黄 10%、橙 15%
                    "orange": 0.75,
                    "yellow": 0.5
                }
            },
            // ---- 风险与仓位约束 ----
            "risk": {
                "entry_cooldown_minutes": 0.0, // 加仓无冷却
                "n_positions": 7, // 最多 7 个空仓
                "total_wallet_exposure_limit": 0, // 0 = 禁用空头(不选币、不下单)
                "total_exposure_enforcer_enabled": true,
                "total_exposure_enforcer_threshold": 0.95,
                "we_excess_allowance_pct": 0, // 无超额额度
                "position_exposure_enforcer_enabled": true,
                "position_exposure_enforcer_threshold": 0.95
            },
            // ---- 追踪马丁格尔策略 ----
            "strategy": {
                "trailing_martingale": {
                    "volatility_ema_span_1h": 672, // 1h 波动率 EMA 跨度(小时)
                    "volatility_ema_span_1m": 60.0, // 1m 波动率 EMA 跨度(分钟)
                    "entry": {
                        "ema_span_0": 100, // 入场 EMA 带跨度(分钟)
                        "ema_span_1": 100,
                        "double_down_factor": 0.5, // 补仓量 = 当前仓位 x 0.5
                        // 空头 = max(卖一, 上轨x(1+dist));负值 = 上轨下方即入场(更积极)
                        "initial_ema_dist": -0.01,
                        "initial_qty_pct": 0.01, // 首次入场占有效 WEL 的 1%
                        "threshold_base_pct": 0.025, // 补仓基准距离 2.5%
                        "threshold_we_weight": 0.0, // 不随暴露放大
                        "threshold_volatility_1h_weight": 1.0,
                        "threshold_volatility_1m_weight": 0.0,
                        "retracement_base_pct": 0.0, // 网格模式补仓
                        "retracement_we_weight": 0.0,
                        "retracement_volatility_1h_weight": 0.0,
                        "retracement_volatility_1m_weight": 0.0
                    },
                    "close": {
                        "qty_pct": 0.1, // 递归止盈每片平 10%
                        "threshold_base_pct": 0.006, // 止盈基准 0.6%
                        "threshold_we_weight": -0.004,
                        "threshold_volatility_1h_weight": 1.0,
                        "threshold_volatility_1m_weight": 0.0,
                        "retracement_base_pct": 0.0, // 普通限价止盈
                        "retracement_volatility_1h_weight": 0.0,
                        "retracement_volatility_1m_weight": 0.0
                    }
                }
            },
            // ---- 自动解套 ----
            "unstuck": {
                "ema_span_0": 100.0, // 解套 EMA 带跨度(分钟)
                "ema_span_1": 100.0,
                "close_pct": 0.001, // 每次平有效暴露预算的 0.1%
                "ema_dist": -0.1, // 空头价格 <= 下轨x(1+0.1) 即可解套;负值 = 提前
                "enabled": true,
                "loss_allowance_pct": 0.001, // 允许亏损 = 0.1% x TWEL x 余额峰值
                "threshold": 0.4 // 暴露/有效WEL > 0.4 触发
            }
        }
    },
    // 按币覆盖任意 bot 参数,如 {"BTC": {"bot": {"long": {"risk": {"n_positions": 2}}}}}
    "coin_overrides": {},
    // 配置结构版本(决定迁移/校验规则)
    "config_version": "v8.4.0",
    // ==================== 实盘运行 ====================
    "live": {
        // 各侧允许交易的币种;[] 禁用该侧,也支持 "all" 或外部文件路径
        "approved_coins": {
            "long": [
                "ADA",
                "BTC",
                "ETH",
                "SOL",
                "XRP"
            ],
            "short": [
                "ADA",
                "BTC",
                "ETH",
                "SOL",
                "XRP"
            ]
        },
        // 币被移出 approved/加入 ignored 后自动转 graceful_stop(false 则转手动)
        "auto_gs": true,
        // 余额更新滞回快照比例(2%),抑制余额噪声;0 = 关闭(精确暴露修复仍用原始余额)
        "balance_hysteresis_snap_pct": 0.02,
        // 手动覆盖钱包余额(调试/干跑);null = 从交易所读取
        "balance_override": null,
        // 等待 K 线管理器文件锁的超时秒数(多 bot 共享缓存目录时可调大)
        "candle_lock_timeout_seconds": 10,
        // 是否允许实盘从交易所归档接口补充历史 K 线
        "enable_archive_candle_fetch": false,
        // 每次执行订单后的等待秒数
        "execution_delay_seconds": 2,
        // 剔除初始入场成本低于交易所最小有效成本的币(实盘默认开)
        "filter_by_min_effective_cost": true,
        // 强制该侧运行模式:""=正常, gs=graceful_stop, t=tp_only, p=panic, m=manual
        "forced_mode_long": "",
        "forced_mode_short": "",
        // 同币双向持仓(实际生效 = 配置 且 交易所支持)
        "hedge_mode": false,
        // HSL 红色冷却期间出现的仓位处理:panic = 再次恐慌平仓并重新计时
        "hsl_position_during_cooldown_policy": "panic",
        // HSL 回撤信号粒度:coin=按仓位槽, pside=按侧, unified=账户级统一
        "hsl_signal_mode": "unified",
        // 各侧明确禁止开仓的币(已有仓位按 auto_gs 处理)
        "ignored_coins": {
            "long": [],
            "short": []
        },
        // 非活跃币种 K 线内存保鲜时长(分钟):越低越新鲜,请求越多
        "inactive_coin_candle_ttl_minutes": 10,
        // 交易所杠杆倍数
        "leverage": 10,
        // 保证金模式:auto_cross/auto_isolated 自动协商;strict cross/isolated 强制
        "margin_mode_preference": "cross",
        // 订单价距市价在该比例内将被改为市价单(仅 market_orders_allowed=true 时生效)
        "market_order_near_touch_threshold": 0.001,
        // 是否允许市价单(false = 只用限价单)
        "market_orders_allowed": false,
        // 实盘 REST 并发上限;null = 默认行为
        "max_concurrent_api_requests": null,
        // 每币每周期落盘 K 线上限(超出裁剪最旧分片)
        "max_disk_candles_per_symbol_per_tf": 2000000,
        // 每币内存保留的 1m K 线上限
        "max_memory_candles_per_symbol": 200000,
        // 单批最大撤单/挂单数(撤 > 挂:先腾位置再下单)
        "max_n_cancellations_per_batch": 5,
        "max_n_creations_per_batch": 3,
        // 崩溃自动重启次数上限(每天),超过后停止
        "max_n_restarts_per_day": 10,
        // K 线类指标(选币排名/预热)每分钟 REST 拉取预算
        "max_ohlcv_fetches_per_minute": 30,
        // 已实现亏损总闸:平仓后余额 < 余额峰值x(1-1.0) 即拦截;>=1 = 关闭;恐慌平仓豁免
        "max_realized_loss_pct": 1,
        // 预热窗口硬上限(分钟);0 = 不限制
        "max_warmup_minutes": 0,
        // 币龄不足 180 天不开仓
        "minimum_coin_age_days": 180,
        // 选币在位保护:已在位的空仓币只有被高出 0.5% 归一化分的挑战者击败才更换
        "forager_score_hysteresis_pct": 0.005,
        // 订单匹配容差:与现有订单相对差异在此内的拟议订单不触发撤/换,防抖动
        "order_match_tolerance_pct": 0.0002,
        // PnL 回看天数(也是解套/亏损预算的滚动窗口);0 = 最小窗口,"all" = 全部
        "pnls_max_lookback_days": 30,
        // 签名请求 recv_window(毫秒);交易所报时钟漂移时可调大
        "recv_window_ms": 5000,
        // 策略类型(trailing_martingale / ema_anchor)
        "strategy_kind": "trailing_martingale",
        // 订单有效期:good_till_cancelled 或 post_only
        "time_in_force": "good_till_cancelled",
        // api-keys.json 中的账户配置名(决定交易所与密钥)
        "user": "bybit_01",
        // 预热并发数(0 = 自动选择)
        "warmup_concurrency": 0,
        // 启动预热随机延迟秒数,避免多 bot 同时拉数据
        "warmup_jitter_seconds": 30,
        // 预热比例:按最长 EMA 跨度 x 0.3 决定预取多少 1m 历史
        "warmup_ratio": 0.3
    },
    // ==================== 日志 ====================
    "logging": {
        "backup_count": 5, // 轮转保留的旧日志份数(rotation=true 时生效)
        "dir": "logs", // 日志目录(含 logs/{user}.log 当前运行别名)
        "level": 1, // 0=警告, 1=info, 2=debug, 3=trace
        "max_bytes_mb": 10.0, // 单文件超过 10MB 轮转(rotation=true 时生效)
        "memory_snapshot_interval_minutes": 30, // 内存快照(RSS/缓存/任务数)间隔
        "persist_to_file": true, // 写入带时间戳的日志文件
        "rotation": false, // 是否启用日志轮转(false = 单文件追加)
        "volume_refresh_info_threshold_seconds": 30 // 批量成交量刷新耗时超过 30s 才记 info
    },
    // ==================== 监控数据发布(monitor-relay 仪表盘数据源)====================
    "monitor": {
        "checkpoint_interval_minutes": 10.0, // 压缩检查点间隔(0 = 关闭)
        "compress_rotated_segments": true, // 轮转后的事件段/检查点 gzip 压缩
        "emit_completed_candles": true, // 发布已完成 1m/1h K 线历史
        "enabled": true, // 监控发布总开关
        "event_rotation_mb": 128.0, // events/current.ndjson 超过 128MB 轮转
        "event_rotation_minutes": 60.0, // 或每 60 分钟轮转(先到先轮)
        "include_raw_fill_payloads": false, // 成交记录附带交易所原始报文
        "max_total_bytes": 1073741824, // 监控目录总大小上限(1 GiB,超出删最旧)
        "price_tick_min_interval_ms": 500, // 价格 tick 历史最小发射间隔
        "retain_candles": true, // 保留 K 线历史流
        "retain_days": 7.0, // 轮转文件保留天数
        "retain_fills": true, // 保留成交历史流
        "retain_price_ticks": true, // 保留价格 tick 历史流
        "root_dir": "monitor", // 输出根目录(实际数据在 monitor/{exchange}/{user})
        "snapshot_interval_seconds": 1.0 // state.latest.json 最小写入间隔
    },
    // ==================== 优化器 ====================
    "optimize": {
        // 优化后端:pymoo(默认)/ deap(旧)/ gpu(实验性)
        "backend": "pymoo",
        // 每参数搜索区间:[min,max] 连续;[min,max,step] 离散网格;[x,x] 固定该值
        "bounds": {
            "long": {
                "forager": {
                    "score_weights_ema_readiness": [ // 选币权重(归一化,相对比例才重要)
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
                    "volatility_ema_span_1m": [ // 波动率 EMA 跨度(分钟)
                        10,
                        720,
                        1
                    ],
                    "volume_drop_pct": [ // 低量裁剪分位
                        0.4,
                        1,
                        0.01
                    ],
                    "volume_ema_span_1m": [ // 成交量 EMA 跨度(分钟)
                        360,
                        2880,
                        10
                    ]
                },
                "hsl": {
                    "cooldown_minutes_after_red": [ // 红色后冷却(分钟)
                        1,
                        2880,
                        10
                    ],
                    "ema_span_minutes": [ // 回撤 EMA 平滑跨度(分钟)
                        1,
                        2880,
                        10
                    ],
                    "red_threshold": [ // 红色熔断回撤阈值
                        0.01,
                        0.12,
                        0.001
                    ]
                },
                "risk": {
                    "entry_cooldown_minutes": [ // 加仓冷却(分钟)
                        0.0,
                        60.0,
                        0.1
                    ],
                    "n_positions": [ // 固定 10 个仓位(与 bot 当前值 4 不同,优化按 10 评估)
                        10,
                        10,
                        1
                    ],
                    "total_wallet_exposure_limit": [ // 固定 TWEL=1.25
                        1.25,
                        1.25
                    ],
                    "total_exposure_enforcer_threshold": [ // 总暴露执行器阈值
                        0.95,
                        1.01,
                        0.001
                    ],
                    "we_excess_allowance_pct": [ // 单仓位超额额度
                        0,
                        0.3,
                        0.01
                    ],
                    "position_exposure_enforcer_threshold": [ // 单仓位执行器阈值
                        0.95,
                        1.01,
                        0.001
                    ]
                },
                "strategy": {
                    "trailing_martingale": {
                        "volatility_ema_span_1h": [ // 1h 波动率 EMA 跨度(小时)
                            672,
                            2016,
                            1
                        ],
                        "volatility_ema_span_1m": [ // 1m 波动率 EMA 跨度(分钟)
                            5,
                            720,
                            1
                        ],
                        "entry": {
                            "ema_span_0": [ // 入场 EMA 带跨度(分钟)
                                200,
                                1440,
                                10
                            ],
                            "ema_span_1": [
                                200,
                                1440,
                                10
                            ],
                            "double_down_factor": [ // 补仓量系数
                                0.5,
                                1,
                                0.01
                            ],
                            "initial_ema_dist": [ // 首次入场距 EMA 带距离(正值 = 更远)
                                -0.01,
                                0.01,
                                0.0001
                            ],
                            "initial_qty_pct": [ // 首次入场占有效 WEL 比例
                                0.01,
                                0.03,
                                0.0001
                            ],
                            "threshold_base_pct": [ // 补仓基准距离
                                0,
                                0.04,
                                1e-05
                            ],
                            "threshold_we_weight": [ // 补仓距离的暴露权重
                                0,
                                5,
                                0.001
                            ],
                            "threshold_volatility_1h_weight": [ // 补仓距离的 1h 波动权重
                                0,
                                40,
                                0.1
                            ],
                            "threshold_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_base_pct": [ // 补仓回踩确认距离(0 = 网格)
                                0,
                                0.015,
                                1e-05
                            ],
                            "retracement_we_weight": [ // 回踩距离的暴露权重
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
                            "qty_pct": [ // 递归止盈每片比例
                                0.05,
                                1,
                                0.01
                            ],
                            "threshold_base_pct": [ // 止盈基准距离(可为负 = 允许亏损平仓)
                                -0.02,
                                0.02,
                                1e-05
                            ],
                            "threshold_we_weight": [ // 止盈距离的暴露权重(可为负)
                                -0.05,
                                0.05,
                                0.0001
                            ],
                            "threshold_volatility_1h_weight": [ // 止盈距离的 1h 波动权重
                                0,
                                40,
                                0.1
                            ],
                            "threshold_volatility_1m_weight": [
                                0,
                                40,
                                0.1
                            ],
                            "retracement_base_pct": [ // 止盈回踩确认距离(0 = 限价)
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
                    "ema_span_0": [770, 770], // 固定解套 EMA 跨度,不搜索
                    "ema_span_1": [210, 210],
                    "close_pct": [ // 每次解套平仓占有效 WEL 比例
                        0.05,
                        0.12,
                        0.001
                    ],
                    "ema_dist": [ // 解套触发偏移(负值 = 提前)
                        -0.2,
                        -0.07,
                        0.0001
                    ],
                    "loss_allowance_pct": [ // 已实现亏损预算比例
                        0.005,
                        0.025,
                        0.0001
                    ],
                    "threshold": [ // 解套资格阈值
                        0.4,
                        0.9,
                        0.001
                    ]
                }
            },
            "short": { // 结构同 long,以下仅注释与 long 不同之处
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
                        0.0,
                        60.0,
                        0.1
                    ],
                    "n_positions": [ // 固定 10
                        10,
                        10,
                        1
                    ],
                    "total_wallet_exposure_limit": [ // 固定 0:优化全程空头保持关闭
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
                            "initial_ema_dist": [ // 空头:正值 = 高于上轨,负值 = 提前入场
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
                    "ema_span_0": [100, 100], // 固定解套 EMA 跨度,不搜索
                    "ema_span_1": [100, 100],
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
        // 压缩优化结果文件 all_results.bin
        "compress_results_file": true,
        // ---- 以下 crossover_*/mutation_* 为 legacy 顶层参数:deap 后端直接使用,
        // pymoo 后端仅在 optimize.pymoo.shared 未设置时回退使用 ----
        "crossover_eta": 20, // SBX 交叉分布指数:越大后代越接近父代
        "crossover_probability": 0.64, // 个体交叉概率
        // 候选生成约束覆盖,如 couple_unstuck_ema_spans、mirror_short_from_long
        "enable_overrides": [],
        // 整个运行期间固定在当前值的参数(点路径选择器,支持 * 通配)
        "fixed_params": [],
        // 优化评估时的运行时覆盖(不写入落盘配置);此处把 HSL 永久停机阈值固定为 1(禁用)
        "fixed_runtime_overrides": {
            "bot.long.hsl.no_restart_drawdown_threshold": 1,
            "bot.short.hsl.no_restart_drawdown_threshold": 1
        },
        // 总评估次数(每次 = 一次完整回测)
        "iters": 500000,
        // ---- 惩罚条件:违反不淘汰候选,而是注入罚分;与 limits.value 比较 ----
        "limits": [
            {
                "metric": "drawdown_worst_btc", // BTC 计价最差回撤 > 90% 罚
                "penalize_if": "greater_than",
                "value": 0.9
            },
            {
                "metric": "drawdown_worst_usd", // USD 计价最差回撤 > 90% 罚
                "penalize_if": "greater_than",
                "value": 0.9
            },
            {
                "metric": "loss_profit_ratio", // 亏损/盈利比 > 0.6 罚
                "penalize_if": "greater_than",
                "value": 0.6
            },
            {
                "metric": "adg_pnl", // 日均收益率 < 0.09% 罚
                "penalize_if": "less_than",
                "reducer": "mean",
                "value": 0.0009
            },
            {
                "metric": "peak_recovery_hours_pnl", // 权益新高恢复 > 56 天罚
                "penalize_if": "greater_than",
                "value": 1344
            },
            {
                "metric": "position_held_hours_max", // 最长持仓 > 56 天罚
                "penalize_if": "greater_than",
                "value": 1344
            },
            {
                "metric": "position_unchanged_hours_max", // 最长无成交 > 35 天罚(防僵尸仓位)
                "penalize_if": "greater_than",
                "value": 840
            }
        ],
        "mutation_eta": 20, // 多项式变异分布指数:越大变异越局部
        "mutation_indpb": 0.05, // 被选中个体中每个基因的变异概率
        "mutation_probability": 0.34, // 个体变异概率
        // 并行评估使用的 CPU 核数
        "n_cpus": 16,
        // 每代子代数 = population_size x 该倍数(mu+lambda 进化策略)
        "offspring_multiplier": 1,
        // 磁盘上 Pareto 前沿最大容量(超出按拥挤度裁剪,保留各目标极端点)
        "pareto_max_size": 250,
        // 种群大小
        "population_size": 250,
        // pymoo 后端专属设置
        "pymoo": {
            "algorithm": "auto", // 自动:目标数 <=3 用 NSGA-II,>=4 用 NSGA-III(本配置 8 目标 -> NSGA-III)
            "algorithms": {
                "nsga2": {},
                "nsga3": {
                    "ref_dirs": {
                        "method": "das_dennis", // 参考方向生成方法
                        "n_partitions": "auto" // 自动选能装入种群预算的最细网格
                    }
                }
            },
            // 两种算法及 GPU 后端 CPU 侧提案阶段共用的算子参数
            "shared": {
                "crossover_eta": 20.0,
                "crossover_prob_var": 0.64, // 单变量交叉概率
                "eliminate_duplicates": true, // 消除重复个体
                "mutation_eta": 20.0,
                "mutation_prob": 0.05, // 个体变异概率
                "mutation_prob_per_variable": "auto" // auto = 1/参数数
            }
        },
        // 候选去重/落盘的有效数字位数(越小合并越激进)
        "round_to_n_significant_digits": 3,
        // 多目标函数:每项一个适应度分量,Pareto 前沿在全部目标上维护
        "scoring": [
            {
                "goal": "max",
                "metric": "adg_pnl" // 日均收益率(算术平均)
            },
            {
                "goal": "max",
                "metric": "mdg_pnl" // 日均收益率(中位数)
            },
            {
                "goal": "min",
                "metric": "loss_profit_ratio" // 亏损/盈利比(越低越好)
            },
            {
                "goal": "min",
                "metric": "peak_recovery_hours_pnl" // 权益新高恢复时间(小时)
            },
            {
                "goal": "min",
                "metric": "position_held_hours_max" // 最长持仓时长(小时)
            },
            {
                "goal": "min",
                "metric": "position_unchanged_hours_max" // 最长无成交时长(小时)
            },
            {
                "goal": "max",
                "metric": "volume_pct_per_day_avg_w" // 日均成交额占余额比(近期加权)
            },
            {
                "goal": "max",
                "metric": "entry_initial_balance_pct_long" // 多头单次初始入场占余额比
            }
        ],
        // 把每个已评估候选都写入 all_results.bin
        "write_all_results": true
    }
}
```
