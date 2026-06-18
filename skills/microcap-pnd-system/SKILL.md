---
name: microcap-pnd-system
description: "极端山寨P&D交易系统 v3.0 — 全自动深度分析。一次扫描完成发现+基本面+合约+垃圾币过滤+量价诊断+综合评分+交易建议。检测器/追踪器/退出信号器/鲸鱼监控四件套。"
version: 3.1.0
metadata:
  hermes:
    tags: [microcap, altcoin, pump-and-dump, PnD, meme, forensic, backtest, exit-strategy, deep-analysis]
    related_skills: [crypto-market-analysis]
---

# 极端山寨P&D交易系统 v3.1

> ⛔ 铁律：你不是在写行情播报，你是在做法医解剖。每句话必须回答"为什么"。禁止"可能""或许""值得关注"。每个数据必须有对比基准。每个判断必须有因果链。

> **核心认知：86%的极端山寨最终崩盘>50%。赚钱靠的不是选对币，是在崩之前跑掉。**
> **铁则：每次分析必须全维度，禁止只给价格就建议入场。泵幅>50%自动降级。**

## 一、系统架构

```
pnd_detect.py v3（全自动深度分析）
  ├── ① Binance现货 24hr ticker
  ├── ② 4H/1H/日线 K线 + 量轨迹
  ├── ③ 永续合约 OI + 资金费率(5次历史)
  ├── ④ CoinGecko: MCAP/FDV/流通/ATH/ATL/排名
  ├── ⑤ 社区: Twitter粉丝数 + 项目分类
  ├── ⑥ 退市风险检查 (已知退市列表 + 描述关键词)
  ├── ⑦ 垃圾币自动过滤 (ATH-99% + 死社区 + 僵尸量 + 排名>1500)
  ├── ⑧ 红牌检查 (换手/流通/FDV/MCAP/ATH回撤)
  ├── ⑨ 量价健康度诊断 (量缩率 + 上影 + 换手率)
  └── ⑩ 综合评分(0-10) + 交易建议

pnd_track.py v3（全维度实时追踪）
  └── 价格/量/OI/费率/阶段变迁/健康度/预警 (Binance→Bybit→Gate.io回退)

pnd_exit.py v3（全维度退出决策引擎）
  └── 5级信号权重 + 6级操作指令 + OI背离检测 + 移动止损

pnd_whale.py v1（BSC链上鲸鱼监控）
  └── 持仓集中度 + 大额转账 + 鲸鱼动向检测
```

## 二、脚本详解

### 2.1 怎么抓 — `pnd_detect.py` v3.0（全自动深度分析）

**一条命令 = 扫描 + 基本面 + 合约 + 垃圾币过滤 + 评分 + 建议。**

```bash
# 全自动扫描+深度分析Top8
python3 ~/.hermes/scripts/microcap/pnd_detect.py

# 指定币种深度分析
python3 ~/.hermes/scripts/microcap/pnd_detect.py --symbol BANANAS31,EDEN,SPELL

# 只看能进的(评分≥5)
python3 ~/.hermes/scripts/microcap/pnd_detect.py --deep 10 --min-score 5

# JSON输出
python3 ~/.hermes/scripts/microcap/pnd_detect.py --json --deep 5

# 后台定时扫+预警文件输出
python3 ~/.hermes/scripts/microcap/pnd_detect.py --deep 5 --alert
```

**评分体系**：
- ≥7.0 → 🟢 可进（信号强，风险可控）
- 5.0-6.9 → 🟡 谨慎（有信号但存在风险点）
- 3.0-4.9 → 🟠 高风险（多项红牌，小仓位可赌）
- 1.0-2.9 → 🔴 不建议（风险大于机会）
- <1.0 → 💀 不做（垃圾币/退市候选）

**垃圾币自动过滤器**（任一满足即扣分至负）：
- ATH回撤 > 99.5%（死猫）
- CoinGecko排名 > 1500（无人关注）
- Twitter < 1K粉（死社区）
- 24h换手率 < 0.01（僵尸）
- 已知退市记录（Bitget/Bitfinex等）

**9级P&D阶段判定**：
| 阶段 | 条件 | 操作 |
|------|------|------|
| 🟢 EARLY | 24h涨10-15%，高回撤<3%，量↗ | ✅可进 |
| 📈 PUMP | 24h涨15-40%，高回撤<8%，量↗ | ✅可追 |
| 🚀 SURGE | 1h涨>15%，量↗↗ | 🟢可追 |
| 🚀 MOON | 24h涨>40%，高回撤<8% | 🟢可追 |
| 🛑 ACCUM | 横盘，换手0.02-0.2x | 🟡观察 |
| ⚠️ FADE | 高回撤25-40% | 🔴回避 |
| 💀 DIST | 高回撤>40% | 🔴回避 |
| 🔻 DUMP | 24h跌>20% | 🔴回避 |
| 😴 ZOMBIE | 换手<0.01 | 💀不做 |

### 2.2 怎么跟 — `pnd_track.py` v3.0（全维度追踪）

**新增**：OI+价格四象限、健康度评分(0-100)、阶段变迁标注、入场信号检测

```bash
python3 ~/.hermes/scripts/microcap/pnd_track.py BANANAS31 --duration 60 --interval 2
python3 ~/.hermes/scripts/microcap/pnd_track.py BANANAS31 --once   # 单次全维度快照
python3 ~/.hermes/scripts/microcap/pnd_track.py BANANAS31 --watch --alert  # 无限追踪
```

### 2.3 怎么跑 — `pnd_exit.py` v3.0（全维度退出决策）

**新增**：OI+价格背离检测、信号权重系统(1-5)、六级操作指令、正向信号检测

```bash
python3 ~/.hermes/scripts/microcap/pnd_exit.py BANANAS31
python3 ~/.hermes/scripts/microcap/pnd_exit.py BANANAS31 --entry 0.01 --trailing 25
python3 ~/.hermes/scripts/microcap/pnd_exit.py BANANAS31 --watch --entry 0.01 --alert &  # 后台
```

**信号权重系统**：

| 权重 | 级别 | 触发条件示例 |
|------|------|-------------|
| 🔴5 | 强制清仓 | 24h高回撤>40%、移动止损、量<10%峰值、1h跌>25%、OI价-齐跌 |
| 🟠4 | 强减仓 | 回撤>25%、量<20%、1h跌>15% |
| 🟡3 | 减仓 | 高点8h未破、量<35%、24h转跌>10% |
| ⚪2 | 预警 | 费率极端、流动性枯竭 |
| 🟢-2 | 正向 | OI+价+(多头建仓) |

**决策矩阵**：weight=5×1→清仓 | weight=4×2→清仓 | weight=4×1→减仓50% | weight=3×2→减仓25% | 正向≥2→可加仓

### 2.4 链上鲸鱼 — `pnd_whale.py` v1.0

```bash
python3 ~/.hermes/scripts/microcap/pnd_whale.py 0x合约地址
python3 ~/.hermes/scripts/microcap/pnd_whale.py BANANAS31  # 自动查找合约
python3 ~/.hermes/scripts/microcap/pnd_whale.py 0x... --watch --interval 5
```

需要 `BSCSCAN_API_KEY` 环境变量（bscscan.com免费注册）。

## 三、完整交易流程

```
1. pnd_detect.py → 扫描+深度分析，评分≥7的进入候选
2. 人工验证：看项目官网/TG/推特，排除明显骗局
3. pnd_track.py --once → 确认1h趋势+量价健康
4. 入场（1%仓位，−30%硬止损）
5. pnd_exit.py --watch --entry <入场价> --alert & → 后台监控
6. 触发退出信号 → 立即清仓
```

## 四、铁律

1. **先排雷再看泵**：退市候选/垃圾币/ATH-99% → 直接跳过，不看价格
2. **仓位**：单币不超过总资金2%
3. **止损**：入场价−30%硬止损，或追踪峰值−30%移动止损
4. **不做反弹**：派发确认后不接飞刀
5. **深度分析不可跳过**：只给价格+涨幅就建议入场 = 失职
6. **信号优先于信仰**：退出信号触发就撤
7. **CoinGecko限流时用交易所API回退**：不依赖单一数据源

## 五、微盘红牌清单（全面版）

| 条件 | 阈值 | 严重度 |
|------|------|--------|
| 换手率>2x | vol/mcap > 2.0 | 🔴极度投机 |
| 换手率>1x | vol/mcap > 1.0 | 🟡投机活跃 |
| 流通率<15% | circ < 15% | 🔴高度控盘 |
| 流通率<25% | circ < 25% | 🟡庄家影响力大 |
| FDV/MCAP>8x | fdv/mcap > 8.0 | 🔴巨大解锁抛压 |
| FDV/MCAP>5x | fdv/mcap > 5.0 | 🟡解锁抛压 |
| MCAP<$5M | mcap < 5M | 🔴极易操纵 |
| MCAP<$10M | mcap < 10M | 🟡流动性差 |
| ATH回撤>99% | ath_dd < -99% | 🔴死猫反弹 |
| 退市记录 | 任一家 | 💀一票否决 |

## 六、脚本位置

```
~/.hermes/scripts/microcap/
├── microcap_utils.py   # 共享基础设施（限流/多交易所/ID查找/预警输出）
├── pnd_detect.py       # v3.0 全自动深度分析检测器
├── pnd_track.py        # v3.0 全维度实时追踪器
├── pnd_exit.py         # v3.0 全维度退出决策引擎
└── pnd_whale.py        # v1.0 BSC链上鲸鱼监控

~/.hermes/alerts/microcap/   # 预警文件输出目录
```

## 七、与BTC分析的差异

| | BTC | 微型山寨 |
|---|-----|---------|
| 分析技能 | crypto-market-analysis | microcap-pnd-system |
| 结构分析 | 核心依据 | ❌不适用 |
| 支撑/阻力 | 关键 | ❌无意义 |
| 止损方式 | 结构位±0.3% | 百分比硬止损(−30%) |
| 仓位 | 2%风险 | 1%风险 |
| 持仓周期 | 日内/波段 | 小时级别 |
| 链上数据 | 完整 | BSCScan鲸鱼 |
| 期权 | Deribit | ❌无 |
| 必查项 | 宏观/FOMC/VIX | 退市风险/垃圾币过滤 |
| 分析深度 | 六维框架 | 十步自动分析 |

## 八、数据源优先级

| 源 | 速度 | 限流 | 用途 |
|---|------|------|------|
| Binance | ⚡即时 | 1200次/分 | 主力（现货+合约） |
| Bybit | ⚡即时 | 宽松 | 备用交叉验证 |
| Gate.io | ⚡即时 | 宽松 | 小币覆盖 |
| CoinGecko | 🐢2.5s间隔 | ~30次/分 | MCAP/FDV/社区 |
| BSCScan | 🐢需Key | 5次/秒 | 链上鲸鱼 |

## 九、法医验证（基于50个极端山寨回溯）

### 五大铁证

| # | 发现 | 数据 | 系统改动 |
|---|------|------|---------|
| ① | **86%的极端山寨已死或正在死** | 60%💀+26%⚠️ | 退出信号>入场信号 |
| ② | **泵幅>50%=死刑判决** | 平均回撤-66% | 自动降级+收紧止损至20% |
| ③ | **量崩是伴随现象，不是原因** | 量<20%=回撤-64%, 量>50%=回撤-48%（差距仅16%） | 量崩仍保留为信号但优先级降低 |
| ④ | **泵的窗口中位数16小时** | 46%在≤8h完成 | "等回踩"策略不可行 |
| ⑤ | **泵幅20-50%是最优区间** | 回撤仅-34%（最优） | 优先推荐此区间标的 |

### 交易启示

- **不做泵幅>50%的币**——回撤66%，风险回报比太差
- **不在泵幅>30%时追高**——窗口已过大半
- **横盘吸筹的币优先**——虽然样本少(1个)，但回撤仅-13%
- **退出信号触发必须执行**——60%的币最终崩盘>50%
